"""Reader support for scanning data sources that are not local files.

The AMaasReader protocol mirrors the Go SDK's AmaasClientReader interface:
the scan engine pulls the chunks it needs via read_bytes(), so a reader can
serve data from a remote source (e.g. an S3 object) without downloading it
in full. _ReaderAdapter adapts a reader to the seekable file-like object
that the scan protocol in amaas.grpc._scan_data consumes.
"""

import io
from typing import Protocol

from .exception import AMaasErrorCode, AMaasException


class AMaasReader(Protocol):
    """Reader protocol consumed by amaas.grpc.scan_reader.

    Mirrors the Go SDK's AmaasClientReader (Identifier/DataSize/ReadBytes).
    """

    def identifier(self) -> str:
        """Return the identifier of the data source, e.g. "s3://bucket/key"."""
        ...

    def data_size(self) -> int:
        """Return the total size of the data source in bytes."""
        ...

    def read_bytes(self, offset: int, length: int) -> bytes:
        """Return length bytes of the data source starting at offset."""
        ...


class _ReaderAdapter:
    """Adapt an AMaasReader to the seekable file-like object the scan
    protocol expects (seek/tell/read)."""

    def __init__(self, reader: AMaasReader):
        self._reader = reader
        self._pos = 0

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self._pos = offset
        elif whence == io.SEEK_CUR:
            self._pos += offset
        elif whence == io.SEEK_END:
            self._pos = max(0, self._reader.data_size() + offset)
        else:
            raise ValueError(f"invalid whence: {whence}")
        if self._pos < 0:
            raise ValueError("negative seek position")
        return self._pos

    def tell(self) -> int:
        return self._pos

    def read(self, length: int = -1) -> bytes:
        size = self._reader.data_size()
        if self._pos >= size:
            return b""
        if length is None or length < 0 or length > size - self._pos:
            length = size - self._pos
        data = self._reader.read_bytes(self._pos, length)
        if len(data) != length:
            # A reader reporting more data_size than it serves would otherwise
            # silently upload a truncated chunk or hash truncated data.
            raise AMaasException(
                AMaasErrorCode.MSG_ID_ERR_RETRIEVE_DATA, length, len(data)
            )
        self._pos += len(data)
        return data
