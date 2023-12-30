import grpc
import json
import os
import pytest
import random
import tempfile
from concurrent import futures
from unittest.mock import patch

import amaas.grpc.aio
from .mock_server import MockScanServicer
from amaas.grpc.exception import AMaasErrorCode
from amaas.grpc.exception import AMaasException


NUM_DATA_LOOP = 128
_, TEST_DATA_FILE_NAME = tempfile.mkstemp()
SERVER_PORT = random.randint(49152, 65535)


#
# Test init_by_region method
#
@patch("amaas.grpc.aio._init_by_region_util")
def test_init_by_region(utilmock):
    amaas.grpc.aio.init_by_region("us-east-1", "dummy_key")

    # ensure True is passed to is_aio_channel parameter
    utilmock.assert_called_with("us-east-1", "dummy_key", True, None, True)


#
# Test init method
#
@patch("amaas.grpc.aio._init_util")
def test_init(utilmock):
    amaas.grpc.aio.init("us-east-1", "dummy_key")

    # ensure False is passed to is_aio_channel parameter
    utilmock.assert_called_with("us-east-1", "dummy_key", False, None, True)


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
# Testing the SDK scan_file method failed with MSG_ID_ERR_FILE_NOT_FOUND exception.
#
@pytest.mark.asyncio
async def test_scan_file_not_found():
    handle = grpc.aio.insecure_channel(f"localhost:{SERVER_PORT}")
    NOT_EXIST_FILE = "012345.txt"
    with pytest.raises(AMaasException) as exc_info:
        await amaas.grpc.scan_file(handle, NOT_EXIST_FILE)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_FILE_NOT_FOUND
    assert exc_info.value.args[1] == NOT_EXIST_FILE


#
# Testing the SDK scan_file method failed with MSG_ID_ERR_FILE_NO_PERMISSION exception
#
@pytest.mark.asyncio
async def test_scan_file_no_permission():
    handle = grpc.insecure_channel(f"localhost:{SERVER_PORT}")
    NOT_PERMISSION_FILE = tempfile.NamedTemporaryFile().name
    open(NOT_PERMISSION_FILE, "x")
    os.chmod(NOT_PERMISSION_FILE, 0x000)
    with pytest.raises(AMaasException) as exc_info:
        await amaas.grpc.scan_file(handle, NOT_PERMISSION_FILE)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_FILE_NO_PERMISSION
    assert exc_info.value.args[1] == NOT_PERMISSION_FILE
    os.remove(NOT_PERMISSION_FILE)


#
# Testing the SDK scan_buffer method succeeded without viruses.
#
@pytest.mark.asyncio
async def test_scan_buffer_success():
    handle = grpc.aio.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        response = await amaas.grpc.aio.scan_buffer(handle, buffer, TEST_DATA_FILE_NAME)
        assert json.loads(response)["scanResult"] == 0


#
# Testing the SDK scan_buffer method succeeded with viruses.
#
@pytest.mark.asyncio
async def test_scan_buffer_virus():
    handle = grpc.aio.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        response = await amaas.grpc.aio.scan_buffer(handle, buffer, "virus")
        jobj = json.loads(response)
        assert jobj["scanResult"] == 1
        assert jobj["foundMalwares"] == ["virus1", "virus2"]


#
# Test different exceptions throwed by scan_buffer API.
#
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error_type, expected_exception",
    [
        (
            MockScanServicer.IDENTIFIER_EXCEED_RATE,
            [AMaasErrorCode.MSG_ID_ERR_RATE_LIMIT_EXCEEDED],
        ),
        (
            MockScanServicer.IDENTIFIER_MISMATCHED,
            [
                AMaasErrorCode.MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE,
                amaas.grpc.scan_pb2.CMD_QUIT,
                amaas.grpc.scan_pb2.STAGE_RUN,
            ],
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
async def test_scan_buffer_exceptions(error_type, expected_exception):
    handle = grpc.aio.insecure_channel(f"localhost:{SERVER_PORT}")
    with open(TEST_DATA_FILE_NAME, mode="rb") as bfile:
        buffer = bfile.read()
        with pytest.raises(AMaasException) as exc_info:
            await amaas.grpc.aio.scan_buffer(handle, buffer, error_type)
        for cnt in range(len(expected_exception)):
            assert exc_info.value.args[cnt] == expected_exception[cnt]
