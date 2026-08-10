# Trend Vision One™ File Security Python SDK User Guide

Trend Vision One™ - File Security is a scanner app for files and cloud storage. This scanner can detect all types of malicious software (malware) including trojans, ransomware, spyware, and more. Based on fragments of previously seen malware, File Security detects obfuscated or polymorphic variants of malware.
File Security can assess any file type or size for malware and display real-time results. With the latest file reputation and variant protection technologies backed by leading threat research, File Security automates malware scanning.
File Security can also scan objects across your environment in any application, whether on-premises or in the cloud.

The Python software development kit (SDK) for Trend Vision One™ File Security empowers you to craft applications which seamlessly integrate with File Security. With this SDK you can perform a thorough scan of data and artifacts within your applications to identify potential malicious elements.
Follow the steps below to set up your development environment and configure your project, laying the foundation to effectively use File Security.

## Checking prerequisites

- Python 3.9 to 3.13
- Trend Vision One account with a chosen region - for more information, see the [Trend Vision One documentation](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-trend-micro-xdr-abou_001).
- A Trend Vision One API key with proper role - for more information, see the [Trend Vision One API key documentation](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-api-keys).

When you have all the prerequisites, continue with creating an API key.

## Creating an API Key

The File Security SDK requires a valid application programming interface (API) key provided as a parameter to the SDK client object. Trend Vision One API keys are associated with different regions. Refer to the region flag below to obtain a better understanding of the valid regions associated with the API key. For more information, see the [Trend Vision One API key documentation](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-api-keys).

### Procedure

- Go to Administrations > API Keys.
- Click Add API Key.
- Configure the API key to use the role with the 'Run file scan via SDK' permission.
- Verify that the API key is associated with the region you plan to use.
- Set an expiry time for the API key and make a record of it for future reference.

## Installing the SDK

Install the File Security SDK package with pip:

```sh
python -m pip install visionone-filesecurity
```

## Using File Security Python SDK

Using File Security Python SDK to scan for malware involves the following basic steps:

1. Create an AMaaS handle object by specifying preferred Vision One region where scanning should be done and a valid API key.
2. Replace "YOUR_API_KEY_OR_TOKEN" and "YOUR_REGION" with your actual API key or token and the desired region.
3. Invoke file scan method to scan the target data.
4. Parse the JSON response returned by the scan APIs to determine whether the scanned data contains malware or not.

### Basic Sample Code

```python
api_key = "YOUR_API_KEY_OR_TOKEN"
region = "YOUR_REGION"

try:
    handle = amaas.grpc.init_by_region(region=region, api_key=api_key)
except Exception as err:
    print(err)

s = time.perf_counter()

try:
    result = amaas.grpc.scan_file(handle, file_name=filename, pml=pml, tags=tags)
    elapsed = time.perf_counter() - s
    print(f"scan executed in {elapsed:0.2f} seconds.")
    print(result)
except Exception as e:
    print(e)

amaas.grpc.quit(handle)
```

### AIO Sample Code

```python
api_key = "YOUR_API_KEY_OR_TOKEN"
region = "YOUR_REGION"

async def main():
    handle = amaas.grpc.aio.init_by_region(region=region, api_key=api_key)

    tasks = set()
    for file_name in file_list:
        task = asyncio.create_task(amaas.grpc.aio.scan_file(handle, file_name=file_name, pml=pml, tags=tags))
        tasks.add(task)

    s = time.perf_counter()

    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - s
    print(f"scan tasks are executed in {elapsed:0.2f} seconds.")

    await amaas.grpc.aio.quit(handle)
    return results

scan_results = asyncio.run(main())
for scan_result in scan_results:
        print(scan_result)
```

### Sample JSON Response

#### Concise Format

```json
{
  "scannerVersion": "1.0.0-29",
  "schemaVersion": "1.0.0",
  "scanResult": 1,
  "scanId": "74c7362b-8245-48be-81fe-b620a0409ef1",
  "scanTimestamp": "2024-04-09T03:17:18.26Z",
  "fileName": "EICAR_TEST_FILE-1.exe",
  "foundMalwares": [
    {
      "fileName": "Eicar.exe",
      "malwareName": "Eicar_test_file"
    }
  ],
  "fileSHA1": "96f11a72c53aac4b24a5e4899bc9f2341d0b7a83",
  "fileSHA256": "7dddcd0f64165f51291a41f49b6246cf85c3e6e599c096612cccce09566091f2"
}
```

#### Verbose Format

```json
{
  "scanType": "sdk",
  "objectType": "file",
  "timestamp": {
    "start": "2024-04-26T18:43:48.639Z",
    "end": "2024-04-26T18:43:49.941Z"
  },
  "schemaVersion": "1.0.0",
  "scannerVersion": "1.0.0-1",
  "fileName": "TRENDX_detect.exe",
  "rsSize": 356352,
  "scanId": "84947a19-b84a-4091-bb7d-8422ab5098a7",
  "accountId": "7423a980-b5af-4e28-bf0b-b58cdf623bb8",
  "result": {
    "atse": {
      "elapsedTime": 1004335,
      "fileType": 7,
      "fileSubType": 2,
      "version": {
        "engine": "23.57.0-1002",
        "lptvpn": 301,
        "ssaptn": 721,
        "tmblack": 253,
        "tmwhite": 227,
        "macvpn": 904
      },
      "malwareCount": 0,
      "malware": null,
      "error": null,
      "fileTypeName": "EXE",
      "fileSubTypeName": "VSDT_EXE_W32"
    },
    "trendx": {
      "elapsedTime": 296763,
      "fileType": 7,
      "fileSubType": 2,
      "version": {
        "engine": "23.57.0-1002",
        "tmblack": 253,
        "trendx": 331
      },
      "malwareCount": 1,
      "malware": [
        {
          "name": "Ransom.Win32.TRX.XXPE1",
          "fileName": "TRENDX_detect.exe",
          "type": "Ransom",
          "fileType": 7,
          "fileSubType": 2,
          "fileTypeName": "EXE",
          "fileSubTypeName": "VSDT_EXE_W32"
        }
      ],
      "error": null,
      "fileTypeName": "EXE",
      "fileSubTypeName": "VSDT_EXE_W32"
    }
  },
  "fileSHA1": "b448479b0a6a5d387c71600e1b75700ba7f42b0a",
  "fileSHA256": "4b7593109f81b5a770d440d8c28fa1457cd4b95d51b5d049fb301fc99c41da39",
  "appName": "V1FS"
}
```

When malicious content is detected in the scanned object, `scanResult` will show a non-zero value. Otherwise, the value will be `null`. Moreover, when malware is detected, `foundMalwares` will be non-empty containing one or more name/value pairs of `fileName` and `malwareName`. `fileName` will be filename of malware detected while `malwareName` will be the name of the virus/malware found.

## Python Client SDK API Reference

### Initialization

#### `def amaas.grpc.init_by_region(region: str, api_key: str, enable_tls: bool = True, ca_cert: str = None) -> grpc.Channel`

Creates a new instance of the grpc Channel, and provisions essential settings, including authentication/authorization credentials (API key), preferred service region, etc.

**_Parameters_**

| Parameter  | Description                                                                                                                                                                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| region     | The region you obtained your api key. Value provided must be one of the Vision One regions, e.g. `us-east-1`, `eu-central-1`, `ap-northeast-1`, `ap-southeast-2`, `ap-southeast-1`, `ap-south-1`, `me-central-1`, `ca-central-1`, `eu-west-2`, `af-south-1`, `ap-southeast-3`,etc. |
| api_key    | Your own Vision One API Key.                                                                                                                                                                                                                       |
| enable_tls | Enable or disable TLS. TLS should always be enabled when connecting to the AMaaS server. For more information, see the 'Ensuring Secure Communication with TLS' section.                                                                           |
| ca_cert    | `Optional` CA certificate used to connect to self hosted AMaaS server.                                                                                                                                                                             |

**_Return_**
A grpc Channel instance

#### `def amaas.grpc.aio.init_by_region(region: str, api_key: str, enable_tls: bool = True, ca_cert: str = None) -> grpc.aio.Channel`

Creates a new instance of the grpc aio Channel, and provisions essential settings, including authentication/authorization credentials (API key), preferred service region, etc.

**_Parameters_**

| Parameter  | Description                                                                                                                                                                                                                                        |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| region     | The region you obtained your api key. Value provided must be one of the Vision One regions, e.g. `us-east-1`, `eu-central-1`, `ap-northeast-1`, `ap-southeast-2`, `ap-southeast-1`, `ap-south-1`, `me-central-1`, `ca-central-1`, `eu-west-2`, `af-south-1`, `ap-southeast-3`, etc. |
| api_key    | Your own Vision One API Key.                                                                                                                                                                                                                       |
| enable_tls | Enable or disable TLS. TLS should always be enabled when connecting to the AMaaS server. For more information, see the 'Ensuring Secure Communication with TLS' section.                                                                           |
| ca_cert    | `Optional` CA certificate used to connect to self hosted AMaaS server.                                                                                                                                                                             |

**_Return_**
A grpc aio Channel instance

### Scan

#### `def amaas.grpc.scan_file(handle: grpc.Channel, file_name: str, tags: List[str], pml: bool = False, feedback: bool = False, verbose: bool = False) -> str`

Scan a file for malware and retrieves response data from the API.

**_Parameters_**

| Parameter | Description                                                                                                 |
| --------- | ----------------------------------------------------------------------------------------------------------- |
| handle    | The grpc Channel instance was created from the init function.                                               |
| file_name | The name of the file with the path of the directory containing the file to scan.                            |
| tags      | A list of strings to be used to tag the scan result. At most 8 tags with a maximum length of 63 characters. |
| pml       | Enable PML (Predictive Machine Learning) Detection.                                                         |
| feedback  | Enable SPN feedback for Predictive Machine Learning Detection                                               |
| verbose   | Enable log verbose mode                                                                                     |
| digest    | Calculate digests for cache search and result lookup                                                        |

**_Return_**
String the scanned result in JSON format.

#### `def amaas.grpc.aio.scan_file(handle: grpc.aio.Channel, file_name: str, tags: List[str], pml: bool = False, feedback: bool = False, verbose: bool = False) -> str`

AsyncIO Scan a file for malware and retrieves response data from the API.

**_Parameters_**

| Parameter | Description                                                                                                 |
| --------- | ----------------------------------------------------------------------------------------------------------- |
| handle    | The grpc aio Channel instance was created from the init function.                                           |
| file_name | The name of the file with the path of the directory containing the file to scan.                            |
| tags      | A list of strings to be used to tag the scan result. At most 8 tags with a maximum length of 63 characters. |
| pml       | Enable PML (Predictive Machine Learning) Detection.                                                         |
| feedback  | Enable SPN feedback for Predictive Machine Learning Detection                                               |
| verbose   | Enable log verbose mode                                                                                     |
| digest    | Calculate digests for cache search and result lookup                                                        |

**_Return_**
String the scanned result in JSON format.

### Cleaning Up

#### `def amaas.grpc.quit(handle: grpc.aio.Channel) -> None`

Remember to clean up the grpc Channel when you are done using it to release any allocated resources:

**_Parameters_**

| Parameter | Description                                               |
| --------- | --------------------------------------------------------- |
| handle    | The grpc Channel instance created from the init function. |

#### `def amaas.grpc.aio.quit(handle: grpc.aio.Channel) -> None`

Remember to clean up the grpc aio Channel when you are done using it to release any allocated resources:

**_Parameters_**

| Parameter | Description                                                   |
| --------- | ------------------------------------------------------------- |
| handle    | The grpc aio Channel instance created from the init function. |

## Error Handling

The File Security Python SDK raises `amaas.grpc.exception.AMaasException` for every error condition produced by `amaas.grpc` and `amaas.grpc.aio`. Each exception carries an `error_code` (a member of the `AMaasErrorCode` enum) and a formatted `message`; `str(exception)` renders both as `<CODE_NAME>: <message>`.

```python
from amaas.grpc.exception import AMaasException

try:
    result = amaas.grpc.scan_file(handle, file_name=filename, tags=tags)
except AMaasException as e:
    print(e.error_code, e.message)
except Exception as e:
    print(e)
```

Some conditions are detected by the SDK itself, independently of any network call: an unsupported region, a missing/unreadable file, invalid tags, or an unexpected message in the scan protocol stream. Everything else comes from the File Security service: the SDK catches `grpc.RpcError` (`grpc.aio.AioRpcError` in the asyncio client) and re-raises it as an `AMaasException`.

For most service errors the SDK preserves the gRPC status code and message text exactly as sent by the service; for two conditions — authentication failures and rate limiting — the SDK discards the service's own message and substitutes a fixed string of its own. Both the synchronous client and the asyncio client apply the same mapping.

The **Source** column classifies each error:

- **SDK-native** — produced entirely by the SDK on the client side, without a network call (unsupported region, missing/unreadable file, invalid tags, unexpected protocol message).
- **SDK-mapped** — triggered by a gRPC response from the service, but the caller-visible message is a fixed string produced by the SDK (authentication failures and rate limiting).
- **Service** — the service's gRPC code and message are relayed to the caller unchanged (via `MSG_ID_GRPC_ERROR`).

| gRPC status code (as received) | `AMaasErrorCode` / message seen by the caller | Cause | Source |
| --- | --- | --- | --- |
| — | `MSG_ID_ERR_INVALID_REGION`: `<region> is not a supported region, region value should be one of <list>` | Region passed to `init_by_region` is not a supported Vision One region | SDK-native |
| — | `MSG_ID_ERR_FILE_NOT_FOUND`: `Failed to open file. No such file or directory <path>.` | File passed to `scan_file` does not exist | SDK-native |
| — | `MSG_ID_ERR_FILE_NO_PERMISSION`: `Failed to open file. Permission denied to open <path>.` | No OS permission to read the file | SDK-native |
| — | `MSG_ID_ERR_INVALID_TAG`: `Invalid tag format: <tag>.` | A tag is empty or longer than 63 characters, checked client-side before the scan request is sent | SDK-native |
| — | `MSG_ID_ERR_TAG_NUMBER_EXCEED`: `Too many tags: <n>.` | More than 8 tags supplied, checked client-side before the scan request is sent | SDK-native |
| — | `MSG_ID_ERR_UNKNOWN_CMD` / `MSG_ID_ERR_UNKNOWN_STAGE` / `MSG_ID_ERR_UNEXPECTED_CMD_AND_STAGE`: `Received unknown command from server: <n>` / `Received unknown stage from server: <n>` / `Received unexpected command <n> and stage <n>.` | The scan protocol stream produced a command/stage the SDK does not recognize | SDK-native |
| — | `MSG_ID_ERR_UNEXPECTED_ERROR`: `Unexpected error encountered. <detail>` | Any other, non-gRPC exception raised while scanning (also used internally if an unsupported hash algorithm is requested) | SDK-native |
| `Unauthenticated` (16) | `MSG_ID_ERR_KEY_AUTH_FAILED`: `Invalid token or Api Key.` | Service rejected the request as `Unauthenticated` — covers a missing key, an invalid/expired key, and an account without file-scan permission. The SDK substitutes this fixed string for all three cases; the service's actual message is not shown to the caller | SDK-mapped |
| `Internal` (13), details containing `429` ¹ | `MSG_ID_ERR_RATE_LIMIT_EXCEEDED`: `Raised by the SDK library to indicate http 429 too many request error.` | Rate limit exceeded. The SDK detects this by scanning the raw error text for the substring `429` and substitutes this fixed string; the service's actual message is not shown to the caller | SDK-mapped |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `Too many tags. Decrease to eight tags or less.` | Too many tags (only reaches the service if the SDK's own client-side check didn't already catch it) | Service |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `Tag is too long. Decrease length to 63 characters or less.` | A tag longer than 63 characters (only reaches the service if the client-side check didn't already catch it) | Service |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `Tag is empty. Remove the tag or add at least one character.` | An empty tag | Service |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `cloudAccountId contains illegal characters (#, @)` | Illegal characters in a `cloudAccountId` tag | Service |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `Prefix format or length of SHA1 from the SDK is incorrect. Contact Support.` / `SHA1 format from the SDK is incorrect. Contact Support.` | Malformed SHA1 digest sent by the SDK | Service |
| `InvalidArgument` (3) | `MSG_ID_GRPC_ERROR`: `Prefix format or length of SHA256 from the SDK is incorrect. Contact Support.` / `SHA256 format from the SDK is incorrect. Contact Support.` | Malformed SHA256 digest sent by the SDK | Service |
| `NotFound` (5) | `MSG_ID_GRPC_ERROR`: `Customer ID not found. Contact Support.` | Account / customer ID not found | Service |
| `PermissionDenied` (7) | `MSG_ID_GRPC_ERROR`: `SDK feature is not enabled for this account. Contact your administrator to enable the SDK feature.` | The SDK feature is not enabled for the account | Service |
| `ResourceExhausted` (8) | `MSG_ID_GRPC_ERROR`: `This account has performed five scans in the last hour. Purchase and allocate credits to File Security or wait an hour to make five more scans.` | Hourly scan quota exhausted (Essential accounts) | Service |
| `ResourceExhausted` (8) | `MSG_ID_GRPC_ERROR`: `file size <n> is over maximum allowed size <m>` | Scanned file/buffer exceeds the maximum allowed size | Service |
| `ResourceExhausted` (8) | `MSG_ID_GRPC_ERROR`: `Cannot allocate resource. Try again later. If the issue persists, contact Support.` | Service could not allocate a scan resource | Service |
| `FailedPrecondition` (9) | `MSG_ID_GRPC_ERROR`: `Incorrect stage <n> from the SDK. Contact Support.` | Incorrect protocol stage | Service |
| `Unimplemented` (12) | `MSG_ID_GRPC_ERROR`: `Predictive Machine Learning is not supported. Contact Support.` | PML requested but not supported for the account/region | Service |
| `Internal` (13) | `MSG_ID_GRPC_ERROR`: `Failed to retrieve metadata. Try again later. If the issue persists, contact Support.` | Service could not retrieve request metadata | Service |
| `Internal` (13) | `MSG_ID_GRPC_ERROR`: `Network connection error. Try again later. If the issue persists, contact Support.` | Service-side network / connection error | Service |
| `Internal` (13) | `MSG_ID_GRPC_ERROR`: `Internal error. Try again later. If the issue persists, contact Support.` | Generic internal service error | Service |
| `Internal` (13) | `MSG_ID_GRPC_ERROR`: `Missing preamble information from the SDK. Contact Support.` | Missing preamble information in the scan request | Service |
| `Internal` (13) | `MSG_ID_GRPC_ERROR`: `Unclear scan result: <detail>. Contact Support.` | Service could not parse the scan result | Service |
| any other code (preserved) | `MSG_ID_GRPC_ERROR`: `Received gRPC status code: <code>, msg: <details>.` | Any other error relayed from the service, with the numeric gRPC code and message exactly as the service sent them | Service |

**Notes**

1. The service currently signals rate limiting with `Internal` and a details string containing `Http Error Code: 429`; the SDK matches on that substring rather than on a dedicated gRPC code, so this row is reached before the generic `MSG_ID_GRPC_ERROR` case below.
2. Rows marked `MSG_ID_GRPC_ERROR` are relayed from the service with the gRPC status code and message preserved exactly; `str(exception)` renders them as `MSG_ID_GRPC_ERROR: Received gRPC status code: <code>, msg: <message>.`. These messages are owned by the File Security service and may change independently of the SDK.
   The Python SDK does not expose Encode/Decode operations, so the service's encode/decode messages cannot occur here.
3. Engine findings such as `ATSE_*` codes are not errors — they are returned inside a successful scan result payload, not raised as an exception.

## Environment Variables

The following environment variables are supported by Python Client SDK and can be used in lieu of values specified as function arguments.

| Variable Name             | Description & Purpose                                                      | Valid Values               |
| ------------------------- | -------------------------------------------------------------------------- | -------------------------- |
| `TM_AM_SCAN_TIMEOUT_SECS` | Specify, in number of seconds, to override the default scan timeout period | 0, 1, 2, ... ; default=300 |

## Thread Safety

- scanFile() or scanBuffer() are designed to be thread-safe. It should be able to invoke scanFile() concurrently from multiple threads without protecting scanFile() with mutex or other synchronization mechanisms.

## Ensuring Secure Communication with TLS

The communication channel between the client program or SDK and the Trend Vision One™ File Security service is fortified with robust server-side TLS encryption. This ensures that all data transmitted between the client and Trend service remains thoroughly encrypted and safeguarded.
The certificate employed by server-side TLS is a publicly-signed certificate from Trend Micro Inc, issued by a trusted Certificate Authority (CA), further bolstering security measures.

The File Security SDK consistently adopts TLS as the default communication channel, prioritizing security at all times. It is strongly advised not to disable TLS in a production environment while utilizing the File Security SDK, as doing so could compromise the integrity and confidentiality of transmitted data.
