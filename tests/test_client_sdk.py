import grpc
import json
import os
import pytest
import random
import tempfile
import uuid
from concurrent import futures
from unittest.mock import patch

import amaas.grpc
from .mock_server import MockScanServicer
from amaas.grpc.exception import AMaasErrorCode
from amaas.grpc.exception import AMaasException


NUM_DATA_LOOP = 128
_, TEST_DATA_FILE_NAME = tempfile.mkstemp()
SERVER_PORT = random.randint(49152, 65535)


@patch("amaas.grpc._init_by_region_util")
def test_init_by_region(utilmock):
    amaas.grpc.init_by_region("ap-southeast-2", "dummy_key")

    # ensure False is passed to is_aio_channel parameter
    utilmock.assert_called_with("ap-southeast-2", "dummy_key", True, None, False)


@patch("amaas.grpc._init_util")
def test_init(utilmock):
    amaas.grpc.init("ap-southeast-2", "dummy_key")

    # ensure False is passed to is_aio_channel parameter
    utilmock.assert_called_with("ap-southeast-2", "dummy_key", False, None, False)


#
# Create a mock gRPC server with MockScanServicer
#
@pytest.fixture(scope="module", autouse=True)
def run_setup():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    amaas.grpc.protos.scan_pb2_grpc.add_ScanServicer_to_server(
        MockScanServicer(), server
    )
    server.add_insecure_port(f"[::]:{SERVER_PORT}")
    server.start()
    yield server
    server.stop(None)


#
# This routine is to create a data file for testing.
# The binary file contains of NUM_DATA_LOOP of consecutive bytes from 0x00 to 0xff.
# This is to make checking the correctness of the content of the retrieval easier.
# The grpc client receives a sequence of instructions from grpc server to retrieve chunks of data
# from a data file during scanning.
# One of the important checking is to ensure the data retrived is what is actually rqeuested by the server.
#
@pytest.fixture(scope="session", autouse=True)
def create_data_file():
    with open(TEST_DATA_FILE_NAME, "wb") as binary_file:
        for j in range(NUM_DATA_LOOP):
            for i in range(256):
                # Convert the number to a single byte and write to the file
                byte_value = i.to_bytes(1, byteorder="big")
                binary_file.write(byte_value)
    yield
    os.remove(TEST_DATA_FILE_NAME)


#
# The method is to verify the chunk matching the data chunk at the given location in the file.
# @param buf buf of the data chunk
# @param offset location in the data file
# @return True if matched False otherwise.
#
def verify_buf_with_data(buf, offset):
    blen = len(buf)
    cnt = 0
    for posn in range(offset, blen):
        val = posn % 256
        # byte_value = val.to_bytes(1, byteorder='big')
        assert buf[cnt] == val
        cnt += 1


#
# Testing authentication failure.
#
def test_scan_file_failed_authentication():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    handle = amaas.grpc.init_by_region("us-east-1", "api-key", True, None)
    with pytest.raises(AMaasException) as exc_info:
        amaas.grpc.scan_file(handle, dir_path + "/fake_server_cert.pem")
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_KEY_AUTH_FAILED


#
# Testing the generate_message method correctly processing the initial message from grpc client
#
def test_generate_message_init():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    with open(TEST_DATA_FILE_NAME, "rb") as f:
        size = os.stat(TEST_DATA_FILE_NAME).st_size
        server_resp = amaas.grpc.scan_pb2.C2S(
            stage=amaas.grpc.scan_pb2.STAGE_INIT,
            file_name=TEST_DATA_FILE_NAME,
            rs_size=size,
            offset=0,
            chunk=None,
            tags=None,
        )

        pipeline.set_message(server_resp)
        c2s_msg = next(amaas.grpc._generate_messages(pipeline, f, True, stats))
        assert c2s_msg.stage == amaas.grpc.scan_pb2.STAGE_INIT
        assert c2s_msg.offset == 0
        assert c2s_msg.rs_size == size
        assert c2s_msg.file_name == TEST_DATA_FILE_NAME


#
# Testing the generate_message method correctly processing a number of back and forth
# data retrieval message from grpc server.
#
def test_generate_message_data():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    f = open(TEST_DATA_FILE_NAME, "rb")
    size = os.stat(TEST_DATA_FILE_NAME).st_size
    #
    # lets loop 5 times to check
    #
    for _ in range(5):
        start = random.randint(0, size - 1)
        end = random.randint(start, size)
        server_resp = amaas.grpc.scan_pb2.S2C(
            stage=amaas.grpc.scan_pb2.STAGE_RUN,
            cmd=amaas.grpc.scan_pb2.CMD_RETR,
            bulk_offset=[start],
            bulk_length=[end - start],
        )

        pipeline.set_message(server_resp)
        c2s_msg = next(amaas.grpc._generate_messages(pipeline, f, True, stats))
        assert c2s_msg.stage == amaas.grpc.scan_pb2.STAGE_RUN
        assert c2s_msg.offset == start
        verify_buf_with_data(c2s_msg.chunk, start)


#
# Testing the generate_message method correctly raise exception when recieved
# wrong command in STAGE RUN from server.
#
def test_generate_message_data_wrong_cmd_exception():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    with open(TEST_DATA_FILE_NAME, "rb") as f:
        size = os.stat(TEST_DATA_FILE_NAME).st_size
        start = random.randint(0, size - 1)
        end = random.randint(start, size)
        server_resp = amaas.grpc.scan_pb2.S2C(
            stage=amaas.grpc.scan_pb2.STAGE_RUN,
            cmd=amaas.grpc.scan_pb2.CMD_QUIT,
            bulk_offset=[start],
            bulk_length=[end - start],
        )
        pipeline.set_message(server_resp)
        with pytest.raises(AMaasException) as exc_info:
            next(amaas.grpc._generate_messages(pipeline, f, True, stats))
        assert (
            exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE
        )
        assert exc_info.value.args[1] == amaas.grpc.scan_pb2.CMD_QUIT
        assert exc_info.value.args[2] == amaas.grpc.scan_pb2.STAGE_RUN


#
# Testing the generate_message method correctly processing the final message from grpc server.
#
def test_generate_message_final():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    f = open(TEST_DATA_FILE_NAME, "rb")
    server_resp = amaas.grpc.scan_pb2.S2C(
        stage=amaas.grpc.scan_pb2.STAGE_FINI, cmd=amaas.grpc.scan_pb2.CMD_QUIT
    )

    pipeline.set_message(server_resp)
    client_msg = next(amaas.grpc._generate_messages(pipeline, f, True, stats), None)
    assert client_msg is None


#
# Testing the generate_message method correctly raise exception when recieved wrong command in STAGE_FINI from server.
#
def test_generate_message_final_wrong_cmd_exception():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    with open(TEST_DATA_FILE_NAME, "rb") as f:
        size = os.stat(TEST_DATA_FILE_NAME).st_size
        start = random.randint(0, size - 1)
        end = random.randint(start, size)
        server_resp = amaas.grpc.scan_pb2.S2C(
            stage=amaas.grpc.scan_pb2.STAGE_FINI,
            cmd=amaas.grpc.scan_pb2.CMD_RETR,
            offset=start,
            length=end - start,
        )
        pipeline.set_message(server_resp)
        with pytest.raises(AMaasException) as exc_info:
            next(amaas.grpc._generate_messages(pipeline, f, True, stats))
        assert (
            exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE
        )
        assert exc_info.value.args[1] == amaas.grpc.scan_pb2.CMD_RETR
        assert exc_info.value.args[2] == amaas.grpc.scan_pb2.STAGE_FINI


#
# Testing the generate_message method correctly processing the unknown stage message from grpc server.
#
def test_generate_message_unknwon_stage():
    pipeline = amaas.grpc._Pipeline()
    stats = {}
    f = open(TEST_DATA_FILE_NAME, "rb")
    UNKNOWN_STAGE = 9999
    server_resp = amaas.grpc.scan_pb2.S2C(
        stage=UNKNOWN_STAGE, cmd=amaas.grpc.scan_pb2.CMD_QUIT
    )

    pipeline.set_message(server_resp)
    with pytest.raises(AMaasException) as exc_info:
        next(amaas.grpc._generate_messages(pipeline, f, True, stats), None)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_UNKNOWN_STAGE
    assert exc_info.value.args[1] == UNKNOWN_STAGE


#
# Testing the SDK scan_file method sucessfully scans a file with no virus.
#
def test_scan_file_success():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    response = amaas.grpc.scan_file(handle, dir_path + "/fake_server_cert.pem")
    assert json.loads(response)["scanResult"] == 0


#
# Testing the SDK scan_file method sucessfully failed with MSG_ID_ERR_FILE_NOT_FOUND exception.
#
def test_scan_file_not_found():
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    NOT_EXIST_FILE = f"{str(uuid.uuid4())}.txt"
    with pytest.raises(AMaasException) as exc_info:
        amaas.grpc.scan_file(handle, NOT_EXIST_FILE)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_FILE_NOT_FOUND
    assert exc_info.value.args[1] == NOT_EXIST_FILE


#
# Testing the SDK scan_file method failed with MSG_ID_ERR_FILE_NO_PERMISSION exception
#
def test_scan_file_no_permission():
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    NOT_PERMISSION_FILE = tempfile.NamedTemporaryFile().name
    open(NOT_PERMISSION_FILE, "x")
    os.chmod(NOT_PERMISSION_FILE, 0x000)
    with pytest.raises(AMaasException) as exc_info:
        amaas.grpc.scan_file(handle, NOT_PERMISSION_FILE)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_FILE_NO_PERMISSION
    assert exc_info.value.args[1] == NOT_PERMISSION_FILE
    os.remove(NOT_PERMISSION_FILE)


#
# Testing the SDK scan_buffer method sucessfully scans a file with no virus.
#
def test_scan_buffer_success():
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        response = amaas.grpc.scan_buffer(handle, buffer, TEST_DATA_FILE_NAME)
        assert json.loads(response)["scanResult"] == 0


#
# Testing the SDK scan_buffer method sucessfully scans a file with virus.
#
def test_scan_buffer_virus():
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        response = amaas.grpc.scan_buffer(
            handle, buffer, MockScanServicer.IDENTIFIER_VIRUS
        )
        jobj = json.loads(response)
        assert jobj["scanResult"] == 1
        assert jobj["foundMalwares"] == ["virus1", "virus2"]


#
# Test different exceptions throwed by scan_buffer API.
#
@pytest.mark.parametrize(
    "error_type, expected_exception",
    [
        (
            MockScanServicer.IDENTIFIER_EXCEED_RATE,
            [AMaasErrorCode.MSG_ID_ERR_RATE_LIMIT_EXCEEDED],
        ),
        (
            MockScanServicer.IDENTIFIER_UNKNOWN_CMD,
            [AMaasErrorCode.MSG_ID_ERR_UNKNOWN_CMD, MockScanServicer.UNKNOWN_CMD],
        ),
        (
            MockScanServicer.IDENTIFIER_GRPC_ERROR,
            [AMaasErrorCode.MSG_ID_GRPC_ERROR, grpc.StatusCode.INTERNAL.value[0]],
        ),
    ],
)
def test_scan_buffer_exceptions(error_type, expected_exception):
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        with pytest.raises(AMaasException) as exc_info:
            amaas.grpc.scan_buffer(handle, buffer, error_type)
        for cnt in range(len(expected_exception)):
            assert exc_info.value.args[cnt] == expected_exception[cnt]
