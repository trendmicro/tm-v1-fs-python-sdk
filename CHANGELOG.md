# CHANGELOG

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
