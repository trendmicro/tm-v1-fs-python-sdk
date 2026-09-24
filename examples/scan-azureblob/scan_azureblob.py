"""Example: scan an Azure Blob Storage blob without downloading it locally.

Implements the same reader contract as the scan-s3obj example:
get_blob_properties for the blob size and ranged download_blob calls for
partial reads, so only the chunks the scan engine asks for cross the wire.

Authentication: pass --sas_token for SAS token auth (dev/test), otherwise
DefaultAzureCredential is used (az login, managed identity, environment).

The reader satisfies amaas.grpc.scan_reader's reader protocol:
    identifier()   -> scan result fileName, e.g. "azure://account/container/blob"
    data_size()    -> total blob size in bytes
    read_bytes(offset, length) -> bytes for the requested range
"""

import argparse
import sys
import time

import amaas.grpc
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient


class AzureBlobReader:
    """AmaasClientReader equivalent backed by an Azure block blob."""

    def __init__(
        self, account_url: str, container: str, blob: str, sas_token: str = None
    ):
        credential = sas_token.lstrip("?") if sas_token else DefaultAzureCredential()
        self._client = BlobClient(
            account_url=account_url,
            container_name=container,
            blob_name=blob,
            credential=credential,
        )
        self._host = account_url.split("//", 1)[-1].rstrip("/")
        self._container = container
        self._blob = blob
        self._size = self._get_blob_size()

    def _get_blob_size(self) -> int:
        size = self._client.get_blob_properties().size
        if size is None:
            raise RuntimeError("unable to get blob size from Azure Storage")
        return size

    def identifier(self) -> str:
        return f"azure://{self._host}/{self._container}/{self._blob}"

    def data_size(self) -> int:
        return self._size

    def read_bytes(self, offset: int, length: int) -> bytes:
        return self._client.download_blob(offset=offset, length=length).readall()


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan an Azure blob in place")
    parser.add_argument(
        "-u",
        "--account_url",
        required=True,
        help="storage account URL, e.g. https://ACCOUNT.blob.core.windows.net",
    )
    parser.add_argument("-c", "--container", required=True, help="blob container name")
    parser.add_argument("-b", "--blob", required=True, help="blob name")
    parser.add_argument(
        "--sas_token", help="blob service SAS token; omit to use DefaultAzureCredential"
    )
    parser.add_argument("-r", "--region", help="File Security region; e.g. us-east-1")
    parser.add_argument("-a", "--addr", help="gRPC server address (self hosted)")
    parser.add_argument("--api_key", help="api key for authentication")
    parser.add_argument("--tls", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--ca_cert", help="CA certificate for self hosted AMaaS server")
    parser.add_argument("--pml", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--feedback", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument(
        "-v", "--verbose", action=argparse.BooleanOptionalAction, default=False
    )
    parser.add_argument("-t", "--tags", nargs="+", help="list of tags")
    parser.add_argument(
        "--digest",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="calculate digests; downloads the whole blob, so keep it off for large blobs",
    )
    args = parser.parse_args()

    if args.region:
        handle = amaas.grpc.init_by_region(
            args.region, args.api_key, args.tls, args.ca_cert
        )
    elif args.addr:
        handle = amaas.grpc.init(args.addr, args.api_key, args.tls, args.ca_cert)
    else:
        parser.error("either -r/--region or -a/--addr is required")
        return 2

    try:
        reader = AzureBlobReader(
            args.account_url, args.container, args.blob, args.sas_token
        )
        s = time.perf_counter()
        result = amaas.grpc.scan_reader(
            handle,
            reader,
            tags=args.tags,
            pml=args.pml,
            feedback=args.feedback,
            verbose=args.verbose,
            digest=args.digest,
        )
        elapsed = time.perf_counter() - s
        print(f"scan executed in {elapsed:0.2f} seconds.")
        print(result)
        return 0
    except HttpResponseError as err:
        print(f"Azure Storage error: {err}")
        return 1
    except Exception as err:  # noqa: BLE001
        print(err)
        return 1
    finally:
        amaas.grpc.quit(handle)


if __name__ == "__main__":
    sys.exit(main())
