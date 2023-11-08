import threading
import logging
from typing import BinaryIO, List

import grpc
import os
import io

from .protos import scan_pb2
from .protos import scan_pb2_grpc
from .exception import AMaasException
from .exception import AMaasErrorCode
from .util import _init_by_region_util
from .util import _init_util
from .util import _validate_tags
from .util import _digest_hex
from .util import APP_NAME_HEADER, APP_NAME_FILE_SCAN

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(LOG_LEVEL)
logger.propagate = False

timeout_in_seconds = 180


class _Pipeline:
    """
    Class to allow a single element pipeline between producer and consumer.
    """

    def __init__(self):
        self._message = 0
        self._producer_lock = threading.Lock()
        self._consumer_lock = threading.Lock()
        self._consumer_lock.acquire()

    def get_message(self):
        self._consumer_lock.acquire()
        message = self._message
        self._producer_lock.release()
        return message

    def set_message(self, message):
        self._producer_lock.acquire()
        self._message = message
        self._consumer_lock.release()


def init_by_region(region, api_key, enable_tls=True, ca_cert=None):
    return _init_by_region_util(region, api_key, enable_tls, ca_cert, False)


def init(host, api_key=None, enable_tls=False, ca_cert=None):
    return _init_util(host, api_key, enable_tls, ca_cert, False)


def _generate_messages(pipeline: _Pipeline, data_reader: BinaryIO, stats: dict) -> None:
    while True:
        message = pipeline.get_message()

        if message.stage == scan_pb2.STAGE_INIT:
            logger.debug("stage INIT")
            yield message
        elif message.stage == scan_pb2.STAGE_RUN:
            if message.cmd != scan_pb2.CMD_RETR:
                raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE, message.cmd, message.stage)

            logger.debug(
                f"stage RUN, try to read {message.length} at offset {message.offset}")

            data_reader.seek(message.offset)
            chunk = data_reader.read(message.length)

            message = scan_pb2.C2S(
                stage=scan_pb2.STAGE_RUN,
                file_name=None,
                rs_size=0,
                offset=data_reader.tell(),
                chunk=chunk)

            stats["total_upload"] = stats.get(
                "total_upload", 0) + len(chunk)
            yield message
        elif message.stage == scan_pb2.STAGE_FINI:
            if message.cmd != scan_pb2.CMD_QUIT:
                raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE, message.cmd, message.stage)

            logger.debug("final stage, quit generating C2S messages...")
            break
        else:
            logger.debug("unknown stage.....!!!")
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNKNOWN_STAGE, message.stage)


def quit(handle):
    handle.close()


def _scan_data(channel: grpc.Channel, data_reader: BinaryIO, size: int, identifier: str, tags: List[str],
               app_name: str) -> str:
    _validate_tags(tags)
    stub = scan_pb2_grpc.ScanStub(channel)
    pipeline = _Pipeline()
    stats = {}
    result = None

    try:
        metadata = (
            (APP_NAME_HEADER, app_name),
        )
        responses = stub.Run(_generate_messages(pipeline, data_reader, stats), timeout=timeout_in_seconds,
                             metadata=metadata)
        message = scan_pb2.C2S(stage=scan_pb2.STAGE_INIT,
                               file_name=identifier,
                               rs_size=size,
                               offset=0,
                               chunk=None,
                               tags=tags,
                               file_sha1="sha1:" + _digest_hex(data_reader, "sha1"),
                               file_sha256="sha256:" + _digest_hex(data_reader, "sha256"))

        pipeline.set_message(message)

        for response in responses:
            if response.cmd == scan_pb2.CMD_RETR:
                pipeline.set_message(response)
            elif response.cmd == scan_pb2.CMD_QUIT:
                result = response.result
                pipeline.set_message(response)
                logger.debug("receive QUIT, exit loop...\n")
                break
            else:
                logger.debug("unknown command...")
                raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNKNOWN_CMD, response.cmd)

        total_upload = stats.get("total_upload", 0)
        logger.debug(f"total upload {total_upload} bytes")

    except AMaasException:
        raise
    except grpc.RpcError as rpc_error:
        if "429" in str(rpc_error):
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_RATE_LIMIT_EXCEEDED)
        elif rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_KEY_AUTH_FAILED)
        else:
            raise AMaasException(AMaasErrorCode.MSG_ID_GRPC_ERROR, rpc_error.code().value[0], rpc_error.details())
    except Exception as err:
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_ERROR, str(err))

    return result


def scan_file(channel: grpc.Channel, file_name: str, tags: List[str] = None, app_name: str = APP_NAME_FILE_SCAN) -> str:
    try:
        f = open(file_name, "rb")
        fid = os.path.basename(file_name)
        n = os.stat(file_name).st_size
    except FileNotFoundError as err:
        logger.debug("File not exist: " + str(err))
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_FILE_NOT_FOUND, file_name)
    except (PermissionError, IOError) as err:
        logger.debug("Permission error: " + str(err))
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_FILE_NO_PERMISSION, file_name)

    return _scan_data(channel, f, n, fid, tags, app_name)


def scan_buffer(channel: grpc.Channel, bytes_buffer: bytes, uid: str, tags: List[str] = None,
                app_name: str = APP_NAME_FILE_SCAN) -> str:
    f = io.BytesIO(bytes_buffer)
    return _scan_data(channel, f, len(bytes_buffer), uid, tags, app_name)
