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

#### ```def amaas.grpc.init_by_region(region: str, api_key: str, enable_tls: bool = True, ca_cert: str = None) -> grpc.Channel```

Creates a new instance of the grpc Channel, and provisions essential settings, including authentication/authorization credentials (API key), preferred service region, etc.

**_Parameters_**

| Parameter  | Description                                                                                                                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| region     | The region you obtained your api key.  Value provided must be one of the Vision One regions, e.g. `us-east-1`, `eu-central-1`, `ap-northeast-1`, `ap-southeast-2`, `ap-southeast-1`, `ap-south-1`, `me-central-1`, etc. |
| api_key    | Your own Vision One API Key.                                                                                                                                                                            |
| enable_tls | Enable or disable TLS. TLS should always be enabled when connecting to the AMaaS server. For more information, see the 'Ensuring Secure Communication with TLS' section.                                |
| ca_cert    | `Optional` CA certificate used to connect to self hosted AMaaS server.                                                                                                                                              |

**_Return_**
A grpc Channel instance

#### ```def amaas.grpc.aio.init_by_region(region: str, api_key: str, enable_tls: bool = True, ca_cert: str = None) -> grpc.aio.Channel```

Creates a new instance of the grpc aio Channel, and provisions essential settings, including authentication/authorization credentials (API key), preferred service region, etc.

**_Parameters_**

| Parameter  | Description                                                                                                                                                                                             |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| region     | The region you obtained your api key.  Value provided must be one of the Vision One regions, e.g. `us-east-1`, `eu-central-1`, `ap-northeast-1`, `ap-southeast-2`, `ap-southeast-1`, `ap-south-1`, `me-central-1`, etc. |
| api_key    | Your own Vision One API Key.                                                                                                                                                                            |
| enable_tls | Enable or disable TLS. TLS should always be enabled when connecting to the AMaaS server. For more information, see the 'Ensuring Secure Communication with TLS' section.                                |
| ca_cert    | `Optional` CA certificate used to connect to self hosted AMaaS server.                                                                                                                                              |

**_Return_**
A grpc aio Channel instance

### Scan

#### ```def amaas.grpc.scan_file(handle: grpc.Channel, file_name: str, tags: List[str], pml: bool = False, feedback: bool = False, verbose: bool = False) -> str```

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

#### ```def amaas.grpc.aio.scan_file(handle: grpc.aio.Channel, file_name: str, tags: List[str], pml: bool = False, feedback: bool = False, verbose: bool = False) -> str```

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

#### ```def amaas.grpc.quit(handle: grpc.aio.Channel) -> None```

Remember to clean up the grpc Channel when you are done using it to release any allocated resources:

**_Parameters_**

| Parameter | Description                                               |
| --------- | --------------------------------------------------------- |
| handle    | The grpc Channel instance created from the init function. |

#### ```def amaas.grpc.aio.quit(handle: grpc.aio.Channel) -> None```

Remember to clean up the grpc aio Channel when you are done using it to release any allocated resources:

**_Parameters_**

| Parameter | Description                                                   |
| --------- | ------------------------------------------------------------- |
| handle    | The grpc aio Channel instance created from the init function. |

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
