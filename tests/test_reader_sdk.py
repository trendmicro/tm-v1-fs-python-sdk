"""Unit tests for the AMaasReader adapter and the scan_reader APIs.

Scans run against MockScanServicer (see mock_server.py) exactly like the
scan_buffer tests: the mock reads random ranges from the data source, which
exercises _ReaderAdapter.seek/read for every chunk the "engine" requests.
"""

import hashlib
import json
from concurrent import futures

import amaas.grpc
import amaas.grpc.aio
import grpc
import pytest
from amaas.grpc.reader import _ReaderAdapter

from .mock_server import MockScanServicer

NUM_DATA_LOOP = 128


class BytesBufferReader:
    """AMaasReader implementation over an in-memory buffer, mirroring the
    Go SDK's AmaasClientBufferReader."""

    def __init__(self, buffer: bytes, identifier: str):
        self._buffer = buffer
        self._identifier = identifier

    def identifier(self) -> str:
        return self._identifier

    def data_size(self) -> int:
        return len(self._buffer)

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self._buffer[offset : offset + length]


@pytest.fixture(scope="module")
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    amaas.grpc.protos.scan_pb2_grpc.add_ScanServicer_to_server(
        MockScanServicer(), server
    )
    # Port 0 lets the OS pick a free port; a fixed random port can collide
    # with an in-use one and fail the whole module.
    server_port = server.add_insecure_port("[::]:0")
    server.start()
    yield server_port
    server.stop(None)


@pytest.fixture(scope="session")
def test_data():
    # Same deterministic pattern as the scan_file/scan_buffer tests:
    # NUM_DATA_LOOP repetitions of bytes 0x00..0xff.
    data = bytearray()
    for _ in range(NUM_DATA_LOOP):
        for i in range(256):
            data += i.to_bytes(1, byteorder="big")
    return bytes(data)


#
# _ReaderAdapter behaviour over an AMaasReader.
#
def test_reader_adapter_seek_tell_read(test_data):
    reader = BytesBufferReader(test_data, "adapter-test")
    adapter = _ReaderAdapter(reader)

    assert adapter.tell() == 0

    # Seek + read a chunk; content must match the source bytes.
    adapter.seek(300)
    chunk = adapter.read(100)
    assert chunk == test_data[300:400]
    assert adapter.tell() == 400

    # Reading past EOF returns b"" instead of raising.
    adapter.seek(reader.data_size())
    assert adapter.read(10) == b""


def test_reader_adapter_read_clamps_to_size(test_data):
    reader = BytesBufferReader(test_data, "adapter-test")
    adapter = _ReaderAdapter(reader)

    # A read that extends past the end returns only the remaining bytes.
    adapter.seek(reader.data_size() - 10)
    assert adapter.read(100) == test_data[-10:]


def test_reader_adapter_seek_whence(test_data):
    reader = BytesBufferReader(test_data, "adapter-test")
    adapter = _ReaderAdapter(reader)

    import io

    adapter.seek(100)
    adapter.seek(50, io.SEEK_CUR)
    assert adapter.tell() == 150
    adapter.seek(-40, io.SEEK_END)
    assert adapter.tell() == reader.data_size() - 40


def test_reader_adapter_digest_matches_direct_hash(test_data):
    # The digest path reads the source through the adapter once and returns
    # both hashes; they must equal hashing the buffer directly.
    from amaas.grpc import util

    reader = BytesBufferReader(test_data, "digest-test")
    adapter = _ReaderAdapter(reader)

    sha1 = hashlib.sha1(test_data).hexdigest()
    sha256 = hashlib.sha256(test_data).hexdigest()
    assert util._digest_hex_pair(adapter) == (sha1, sha256)


class ShortReadReader:
    """AMaasReader that reports the full data_size but serves fewer bytes
    than requested, e.g. a remote source truncating ranged reads."""

    def __init__(self, buffer: bytes, served: int):
        self._buffer = buffer
        self._served = served

    def identifier(self) -> str:
        return "short-read"

    def data_size(self) -> int:
        return len(self._buffer)

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self._buffer[offset : offset + self._served]


def test_reader_adapter_short_read_raises(test_data):
    from amaas.grpc.exception import AMaasErrorCode, AMaasException

    reader = ShortReadReader(test_data, served=2)
    adapter = _ReaderAdapter(reader)

    adapter.seek(0)
    with pytest.raises(AMaasException) as exc_info:
        adapter.read(100)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_RETRIEVE_DATA
    assert exc_info.value.args[1] == 100
    assert exc_info.value.args[2] == 2


#
# scan_reader against the mock scan server.
#
def test_scan_reader_success(test_data, grpc_server):
    handle = grpc.insecure_channel(f"localhost:{grpc_server}")
    reader = BytesBufferReader(test_data, "good_sample.zip")
    response = amaas.grpc.scan_reader(handle, reader)
    assert json.loads(response)["scanResult"] == 0


def test_scan_reader_virus(test_data, grpc_server):
    handle = grpc.insecure_channel(f"localhost:{grpc_server}")
    reader = BytesBufferReader(test_data, MockScanServicer.IDENTIFIER_VIRUS)
    response = amaas.grpc.scan_reader(handle, reader)
    jobj = json.loads(response)
    assert jobj["scanResult"] == 1
    assert jobj["foundMalwares"] == ["virus1", "virus2"]


def test_scan_reader_digest(test_data, grpc_server):
    # digest=True forces the SDK to read the whole source for hashing; the
    # scan still completes and the mock's chunks keep matching.
    handle = grpc.insecure_channel(f"localhost:{grpc_server}")
    reader = BytesBufferReader(test_data, "digest-test")
    response = amaas.grpc.scan_reader(handle, reader, digest=True)
    assert json.loads(response)["scanResult"] == 0


def test_scan_reader_short_read_raises(test_data, grpc_server):
    from amaas.grpc.exception import AMaasErrorCode, AMaasException

    # The scan engine keeps requesting chunks; a reader serving fewer bytes
    # than requested must fail the scan instead of uploading truncated data.
    handle = grpc.insecure_channel(f"localhost:{grpc_server}")
    reader = ShortReadReader(test_data, served=2)
    with pytest.raises(AMaasException) as exc_info:
        amaas.grpc.scan_reader(handle, reader)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_RETRIEVE_DATA


@pytest.mark.asyncio
async def test_scan_reader_short_read_raises_aio(test_data, grpc_server):
    from amaas.grpc.exception import AMaasErrorCode, AMaasException

    handle = grpc.aio.insecure_channel(f"localhost:{grpc_server}")
    reader = ShortReadReader(test_data, served=2)
    with pytest.raises(AMaasException) as exc_info:
        await amaas.grpc.aio.scan_reader(handle, reader)
    assert exc_info.value.args[0] == AMaasErrorCode.MSG_ID_ERR_RETRIEVE_DATA


@pytest.mark.asyncio
async def test_scan_reader_success_aio(test_data, grpc_server):
    handle = grpc.aio.insecure_channel(f"localhost:{grpc_server}")
    reader = BytesBufferReader(test_data, "good_sample.zip")
    response = await amaas.grpc.aio.scan_reader(handle, reader)
    assert json.loads(response)["scanResult"] == 0


@pytest.mark.asyncio
async def test_scan_reader_virus_aio(test_data, grpc_server):
    handle = grpc.aio.insecure_channel(f"localhost:{grpc_server}")
    reader = BytesBufferReader(test_data, MockScanServicer.IDENTIFIER_VIRUS)
    response = await amaas.grpc.aio.scan_reader(handle, reader)
    jobj = json.loads(response)
    assert jobj["scanResult"] == 1
    assert jobj["foundMalwares"] == ["virus1", "virus2"]
