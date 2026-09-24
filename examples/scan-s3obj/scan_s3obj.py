"""Example: scan an AWS S3 object without downloading it locally.

Implements the same reader contract as the Go SDK's scan-s3obj example:
GetObjectAttributes for the object size and ranged GetObject calls for
partial reads, so only the chunks the scan engine asks for cross the wire.

The reader satisfies amaas.grpc.scan_reader's reader protocol:
    identifier()   -> scan result fileName, e.g. "s3://bucket/key"
    data_size()    -> total object size in bytes
    read_bytes(offset, length) -> bytes for the requested range
"""

import argparse
import sys
import time

import boto3
from botocore.exceptions import ClientError

import amaas.grpc


class S3ObjectReader:
    """AmaasClientReader equivalent backed by an S3 object."""

    def __init__(self, bucket: str, key: str, region: str):
        self._s3 = boto3.client("s3", region_name=region)
        self._bucket = bucket
        self._key = key
        self._size = self._get_object_size()

    def _get_object_size(self) -> int:
        attr = self._s3.get_object_attributes(
            Bucket=self._bucket, Key=self._key, ObjectAttributes=["ObjectSize"]
        )
        size = attr.get("ObjectSize")
        if size is None:
            raise RuntimeError("unable to get object size from S3")
        return size

    def identifier(self) -> str:
        return f"s3://{self._bucket}/{self._key}"

    def data_size(self) -> int:
        return self._size

    def read_bytes(self, offset: int, length: int) -> bytes:
        rng = f"bytes={offset}-{offset + length - 1}"
        resp = self._s3.get_object(Bucket=self._bucket, Key=self._key, Range=rng)
        return resp["Body"].read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan an S3 object in place")
    parser.add_argument("-b", "--bucket", required=True, help="S3 bucket name")
    parser.add_argument("-k", "--key", required=True, help="S3 object key")
    parser.add_argument("--bucketregion", default="us-west-2", help="region of the S3 bucket")
    parser.add_argument("-r", "--region", help="File Security region; e.g. us-east-1")
    parser.add_argument("-a", "--addr", help="gRPC server address (self hosted)")
    parser.add_argument("--api_key", help="api key for authentication")
    parser.add_argument("--tls", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--ca_cert", help="CA certificate for self hosted AMaaS server")
    parser.add_argument("--pml", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--feedback", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("-t", "--tags", nargs="+", help="list of tags")
    parser.add_argument(
        "--digest",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="calculate digests; downloads the whole object, so keep it off for large objects",
    )
    args = parser.parse_args()

    if args.region:
        handle = amaas.grpc.init_by_region(args.region, args.api_key, args.tls, args.ca_cert)
    elif args.addr:
        handle = amaas.grpc.init(args.addr, args.api_key, args.tls, args.ca_cert)
    else:
        parser.error("either -r/--region or -a/--addr is required")
        return 2

    try:
        reader = S3ObjectReader(args.bucket, args.key, args.bucketregion)
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
    except ClientError as err:
        print(f"S3 error: {err}")
        return 1
    except Exception as err:  # noqa: BLE001
        print(err)
        return 1
    finally:
        amaas.grpc.quit(handle)


if __name__ == "__main__":
    sys.exit(main())
