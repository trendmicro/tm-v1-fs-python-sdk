# CHANGELOG

## 1.5.0 - 2026-09-15

- Add `scan_reader` (sync and aio) for scanning a data source through a reader implementing
  the new `amaas.grpc.reader.AMaasReader` protocol, mirroring the Go SDK's `ScanReader` and
  `AmaasClientReader`. The SDK pulls only the chunks the scan engine requests, so remote
  sources (e.g. S3 objects) need not be downloaded in full. `digest` defaults to `False`
  because digest calculation reads the whole data source.
- Add an S3 object scan example under `examples/scan-s3obj` demonstrating a reader backed
  by ranged S3 GETs.
- Add an Azure Blob scan example under `examples/scan-azureblob` demonstrating a reader backed
  by ranged blob downloads, with SAS token or `DefaultAzureCredential` auth.
- Enforce the reader contract like the Go SDK: `read_bytes` is never called beyond `data_size`, and
  a short read raises the new `MSG_ID_ERR_RETRIEVE_DATA` error instead of uploading truncated data
  or hashing a truncated source for `digest=True`.
- Compute sha1 and sha256 digests in a single pass, halving the reads a remote reader makes when
  `digest=True`.
- `scan_file` now reports `MSG_ID_ERR_UNEXPECTED_ERROR` for `OSError` other than permission-denied;
  only `PermissionError` maps to `MSG_ID_ERR_FILE_NO_PERMISSION`.

## 1.4.8 - 2026-08-19

- Support new region ap-southeast-3 (Indonesia)
- Support scan gateway for FSCS and FSVA
- Add an Error Handling section to the README documenting SDK and service error codes and messages

## 1.4.6 - 2026-06-24

- `scan_file` now reports the file path you pass as the scan identifier, instead of only
  its basename. Scan results (e.g. `foundMalwares[].fileName`) reflect the full path.

## 1.4.5 - 2026-03-18

- Support new region af-south-1

## 1.4.4 - 2026-01-19

- Support new regions eu-west-2 and ca-central-1

## 1.4.2 - 2025-05-13

- Update the minimum supported version to Python 3.9
- Update the maximum supported version to Python 3.13

## 1.4.1 - 2025-03-03

- Support new region me-central-1

## 1.4.0 - 2024-08-21

- Update README.md
- Support digest calculation bypass

## 1.3.0 - 2024-08-20

- Update README.md
- Support CA cert import

## 1.2.0 - 2024-07-05

- Support verbose scan result

## 1.1.1 - 2024-04-10

- Update README.md
- Extend the scan default timeout to 300 seconds

## 1.1.0 - 2024-04-03

- Update protos
- Enable PML (Predictive Machine Learning) detection and smart feedback
- Enable bulk mode
- Enable India region
- Support for scanning large files (over 2GB)

## 1.0.5 - 2023-12-28

- fix linting issues

## 1.0.4 - 2023-05-18

- set default timeout_in_seconds to 180 seconds

## 1.0.3 - 2023-05-10

- Change LICENSE

## 1.0.2 - 2023-05-10

- Change README.md

## 1.0.1 - 2023-05-04

- Add scan_buffer() function

## 1.0.0 - 2023-05-01

- Initial release
