# Trend Vision One File Security Python SDK User Guide

The Trend Vision One File Security Python SDK empowers developers to craft applications seamlessly integrating with the cloud-based Trend Vision One anti-malware file scanning service. This ensures a thorough scan of data and artifacts within the applications, identifying potential malicious elements.

This guide outlines the steps to establish your development environment and configure your project, laying the foundation for utilizing the File Security Python SDK effectively.

## Requirements

- Python 3.7 or newer
- Trend Vision One account with a chosen region - for more information, see the [Trend Vision One documentation](https://docs.trendmicro.com/en-us/enterprise/trend-micro-xdr-help/Home).
- A Trend Vision One API key with proper role - for more information, see the [Trend Vision One API key documentation](https://docs.trendmicro.com/en-us/enterprise/trend-vision-one/administrative-setti/accountspartfoundati/api-keys.aspx).

## Installation

Install the File Security SDK package with pip:

   ```sh
   python -m pip install visionone-filesecurity
   ```

## Obtain an API Key

The File Security SDK requires a valid API Key provided as parameter to the SDK client object. It can accept Trend Vision One API keys. 

When obtaining the API Key, ensure that the API Key is associated with the region that you plan to use. It is important to note that Trend Vision One API Keys are associated with different regions, please refer to the region flag below to obtain a better understanding of the valid regions associated with the respective API Key.

If you plan on using a Trend Vision One region, be sure to pass in region parameter when running custom program with File Security SDK to specify the region of that API key and to ensure you have proper authorization. The list of supported Trend Vision One regions can be found at API Reference section below.

1. Login to the Trend Vision One.
2. Create a new Trend Vision One API key:

* Navigate to the Trend Vision One User Roles page.
* Verify that there is a role with the "Run file scan via SDK" permissions enabled. If not, create a role by clicking on "Add Role" and "Save" once finished.
* Directly configure a new key on the Trend Vision One API Keys page, using the role which contains the "Run file scan via SDK" permission. It is advised to set an expiry time for the API key and make a record of it for future reference.

## Run SDK

### Run with File Security SDK examples

1. Go to `/examples/` in current directory.

   ```sh
   cd examples/
   ```

2. There are two Python examples in the folder, one with regular file i/o and one with asynchronous file i/o

   ```text
   client_aio.py
   client.py
   ```

3. Current Python examples support following command line arguments

   | Command Line Arguments                 | Value                    | Optional |
   | :------------------ | :----------------------- | :------- |
   | --region or -r | The region you obtained your API key.  Value provided must be one of the Vision One regions, e.g. `us-east-1`, `eu-central-1`, `ap-northeast-1`, `ap-southeast-2`, `ap-southeast-1`, etc. | Yes, either -r or -a
   | --addr or -a   | Trend Vision One File Security server, such as: fs-sdk-_REGION_.xdr.trendmicro.com:443 | Yes, either -r or -a      |
   | --api_key      | Vision One API Key              | No       |
   | --filename or -f |        File to be scanned            | No       |

4. Run one of the examples.

   Make sure to customize the example program by configuring it with the API key from your Vision One account, found in your Vision One Dashboard. Assign the value of your Vision One Region's `API_KEY` to the variable and set `FILENAME` to the desired target file.

   ```sh
   python3 client.py -f FILENAME -r us-1 --api_key API_KEY
   ```

   or

   using File Security server address `-a` instead of region `-r`:

   ```sh
   python3 client.py -f FILENAME -a fs-sdk-_REGION_.xdr.trendmicro.com:443 --api_key API_KEY
   ```

   or

   using asynchronous IO example program:

   ```sh
   python3 client_aio.py -f FILENAME -a fs-sdk-_REGION_.xdr.trendmicro.com:443 --api_key API_KEY
   ```

### Code Examples

```python
import json
import amaas.grpc

handle = amaas.grpc.init(YOUR_FILE_SECURITY_SERVER, YOUR_VISION_ONE_KEY, True)

result = amaas.grpc.scan_file(args.filename, handle)
print(result)

result_json = json.loads(result)
print("Got scan result: %d" % result_json['scanResult'])

amaas.grpc.quit(handle)

```

to use asyncio with  coroutines and tasks,

```python:
import json
import pprint
import asyncio
import amaas.grpc.aio

async def scan_files():
   handle = amaas.grpc.aio.init(YOUR_FILE_SECURITY_SERVER, YOUR_VISION_ONE_KEY, True)

   tasks = [asyncio.create_task(amaas.grpc.aio.scan_file(file_name, handle))]

   scan_results = await asyncio.gather(*tasks)

   for scan_result in scan_results:
      pprint.pprint(json.loads(scan_result))

   await amaas.grpc.aio.quit(handle)


asyncio.run(scan_files())

```
