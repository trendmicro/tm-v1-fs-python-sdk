import io
import logging
import os
import threading
from typing import BinaryIO

import grpc

from .exception import AMaasErrorCode, AMaasException
from .protos import scan_pb2, scan_pb2_grpc
from .reader import AMaasReader, _ReaderAdapter
from .util import (
    APP_NAME_FILE_SCAN,
    APP_NAME_HEADER,
    _digest_hex_pair,
    _init_by_region_util,
    _init_util,
    _validate_tags,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

timeout_in_seconds = int(os.environ.get("TM_AM_SCAN_TIMEOUT_SECS", 300))
heartbeat_interval_in_seconds = int(os.environ.get("TM_AM_HEARTBEAT_INTERVAL_SECS", 30))


class _Pipeline:
    """
    Class to allow a single element pipeline between producer and consumer.
    """

    def __init__(self):
        self._message = 0
        self._producer_lock = threading.Lock()
        self._consumer_lock = threading.Lock()
        self._consumer_lock.acquire()

    def get_message(self, timeout=None):
        acquired = self._consumer_lock.acquire(timeout=timeout)
        if not acquired:
            return None
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


def _generate_messages(
    pipeline: _Pipeline, data_reader: BinaryIO, bulk: bool, stats: dict
) -> None:
    responses = []

    while True:
        for r in responses:
            if r[0] == "INIT":
                response = r[1]
            elif r[0] == "RUN":
                offset = r[1]
                length = r[2]
                data_reader.seek(offset)
                try:
                    chunk = data_reader.read(length)
                except AMaasException as err:
                    # The request iterator runs on a gRPC consumer thread, so
                    # this exception is swallowed there; stash it for the
                    # response loop to re-raise in the caller's thread.
                    stats["reader_error"] = err
                    raise
                response = scan_pb2.C2S(
                    stage=scan_pb2.STAGE_RUN,
                    file_name=None,
                    rs_size=0,
                    offset=offset,
                    chunk=chunk,
                )
                stats["total_upload"] = stats.get("total_upload", 0) + len(chunk)
            else:
                raise AMaasException(
                    AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE, "None", r[0]
                )
            yield response

        responses.clear()
        while True:
            message = pipeline.get_message(timeout=heartbeat_interval_in_seconds)
            if message is None:
                logger.debug("sending heartbeat to keep connection alive")
                yield scan_pb2.C2S(stage=scan_pb2.STAGE_HEARTBEAT)
                continue
            break

        if message.stage == scan_pb2.STAGE_INIT:
            logger.debug("stage INIT")
            responses.append(("INIT", message))
        elif message.stage == scan_pb2.STAGE_RUN:
            if message.cmd != scan_pb2.CMD_RETR:
                raise AMaasException(
                    AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE,
                    message.cmd,
                    message.stage,
                )

            length = []
            offset = []

            if bulk:
                offset = message.bulk_offset[:]
                length = message.bulk_length[:]

                if len(length) > 1:
                    logger.debug("bulk transfer triggered")
            else:
                offset.append(message.offset)
                length.append(message.length)

            for i in range(len(length)):
                logger.debug(
                    f"stage RUN, try to read {length[i]} at offset {offset[i]}"
                )
                responses.append(("RUN", offset[i], length[i]))
        elif message.stage == scan_pb2.STAGE_FINI:
            if message.cmd != scan_pb2.CMD_QUIT:
                raise AMaasException(
                    AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE,
                    message.cmd,
                    message.stage,
                )

            logger.debug("final stage, quit generating C2S messages...")
            break
        else:
            logger.debug("unknown stage.....!!!")
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNKNOWN_STAGE, message.stage)


def quit(handle):
    handle.close()


def _scan_data(
    channel: grpc.Channel,
    data_reader: BinaryIO,
    size: int,
    identifier: str,
    tags: list[str],
    pml: bool,
    feedback: bool,
    verbose: bool,
    digest: bool,
) -> str:
    _validate_tags(tags)
    stub = scan_pb2_grpc.ScanStub(channel)
    pipeline = _Pipeline()
    stats = {}
    result = None
    bulk = True
    file_sha1 = ""
    file_sha256 = ""

    if digest:
        sha1_hex, sha256_hex = _digest_hex_pair(data_reader)
        file_sha1 = "sha1:" + sha1_hex
        file_sha256 = "sha256:" + sha256_hex

    try:
        metadata = ((APP_NAME_HEADER, APP_NAME_FILE_SCAN),)
        responses = stub.Run(
            _generate_messages(pipeline, data_reader, bulk, stats),
            timeout=timeout_in_seconds,
            metadata=metadata,
        )
        message = scan_pb2.C2S(
            stage=scan_pb2.STAGE_INIT,
            file_name=identifier,
            rs_size=size,
            offset=0,
            chunk=None,
            trendx=pml,
            tags=tags,
            file_sha1=file_sha1,
            file_sha256=file_sha256,
            bulk=bulk,
            spn_feedback=feedback,
            verbose=verbose,
        )

        pipeline.set_message(message)

        for response in responses:
            if response.cmd == scan_pb2.CMD_RETR:
                pipeline.set_message(response)
            elif response.cmd == scan_pb2.CMD_QUIT:
                result = response.result
                pipeline.set_message(response)
                logger.debug("receive QUIT, exit loop...")
                break
            else:
                logger.debug("unknown command...")
                raise AMaasException(
                    AMaasErrorCode.MSG_ID_ERR_UNKNOWN_CMD, response.cmd
                )

        total_upload = stats.get("total_upload", 0)
        logger.debug(f"total upload {total_upload} bytes")

    except AMaasException:
        raise
    except grpc.RpcError as rpc_error:
        reader_error = stats.get("reader_error")
        if reader_error is not None:
            raise reader_error
        if "429" in str(rpc_error):
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_RATE_LIMIT_EXCEEDED)
        elif rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise AMaasException(AMaasErrorCode.MSG_ID_ERR_KEY_AUTH_FAILED)
        else:
            raise AMaasException(
                AMaasErrorCode.MSG_ID_GRPC_ERROR,
                rpc_error.code().value[0],
                rpc_error.details(),
            )
    except Exception as err:
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_ERROR, str(err))

    reader_error = stats.get("reader_error")
    if reader_error is not None:
        raise reader_error

    return result


def scan_file(
    channel: grpc.Channel,
    file_name: str,
    tags: list[str] = None,
    pml: bool = False,
    feedback: bool = False,
    verbose: bool = False,
    digest: bool = True,
) -> str:
    try:
        f = open(file_name, "rb")
        fid = file_name
        n = os.stat(file_name).st_size
    except FileNotFoundError as err:
        logger.debug("File not exist: " + str(err))
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_FILE_NOT_FOUND, file_name)
    except PermissionError as err:  # only Errno 13 reports no permission
        logger.debug("Permission error: " + str(err))
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_FILE_NO_PERMISSION, file_name)
    except OSError as err:
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_ERROR, str(err))

    return _scan_data(channel, f, n, fid, tags, pml, feedback, verbose, digest)


def scan_buffer(
    channel: grpc.Channel,
    bytes_buffer: bytes,
    uid: str,
    tags: list[str] = None,
    pml: bool = False,
    feedback: bool = False,
    verbose: bool = False,
    digest: bool = True,
) -> str:
    f = io.BytesIO(bytes_buffer)
    return _scan_data(
        channel, f, len(bytes_buffer), uid, tags, pml, feedback, verbose, digest
    )


def scan_reader(
    channel: grpc.Channel,
    reader: AMaasReader,
    tags: list[str] = None,
    pml: bool = False,
    feedback: bool = False,
    verbose: bool = False,
    digest: bool = False,
) -> str:
    """Scan a data source through an AMaasReader (see amaas.grpc.reader).

    digest defaults to False because digest calculation reads the whole data
    source; with a remote reader (e.g. an S3 object) that defeats the purpose
    of partial reads. Pass digest=True to opt in.
    """
    adapter = _ReaderAdapter(reader)
    try:
        size = reader.data_size()
        fid = reader.identifier()
        return _scan_data(
            channel,
            adapter,
            size,
            fid,
            tags,
            pml,
            feedback,
            verbose,
            digest,
        )
    except AMaasException:
        raise
    except Exception as err:
        raise AMaasException(AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_ERROR, str(err))
