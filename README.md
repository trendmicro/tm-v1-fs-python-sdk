# Trend Vision One File Security SDK for Python

Trend Vision One File Security is a Software Development Kit (SDK) for Python, which allows Python developers to write software interacting with Trend Vision One anti-malware file scanning service. It is used to build file scanning applications on top of the Trend Vision One platform.

## Requirements

- Trend Vision One account with a chosen region - for more information, see the [Trend Vision One account document](https://docs.trendmicro.com/en-us/enterprise/trend-micro-xdr-help/Home).
- A Trend Vision One API key - for more information, see the [Trend Vision One API key documentation](https://docs.trendmicro.com/en-us/enterprise/trend-vision-one/administrative-setti/accountspartfoundati/api-keys.aspx).
- Python 3.7 or newer


## Installation

Install the SDK package with pip:

   ```sh
   python -m pip install visionone-filesecurity
   ```

## Authentication

To authenticate with the API, you need an Trend Vision One API key. Sign up for a [Trend Vision One account](https://docs.trendmicro.com/en-us/enterprise/trend-vision-one.aspx) and follow the instructions on [Manage Trend Vision One API Keys](https://docs.trendmicro.com/en-us/enterprise/trend-vision-one/administrative-setti/accountspartfoundati/api-keys.aspx) to obtain an API key.

When creating a Trend Vision One account, choose a region for the account. All of the account data, as well as the security data for the Trend Vision One security services in the account, is stored in that region. For more information, see the [Trend Vision One regions documentation](https://docs.trendmicro.com/en-us/enterprise/trend-vision-one.aspx).

## Documentation

Documentation for the client SDK is available on [Here](README.md) and [Read the Docs](https://cloudone.trendmicro.com/docs/).

## Run SDK

### Run with Vision One File Security SDK examples

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

   | Command Line Arguments                 | Value                                                                                                               | Optional |
   | :------------------ |:--------------------------------------------------------------------------------------------------------------------| :------- |
   | --region or -r | vision one region options=[us-east-1 eu-central-1 ap-northeast-1 ap-southeast-2 ap-southeast-1]                     | Yes, either -r or -a
   | --addr or -a   | Trend Vision One Amaas server, such as: antimalware.us-1.cloudone.trendmicro.com:443                                | Yes, either -r or -a      |
   | --api_key      | Vision One \<API KEY\>                                                                                              | No       |
   | --filename or -f | File to be scanned                                                                                                  | No       |

4. Run one of the examples.

   The example program needs to be configured with your Vision One account's api key which is available in your Vision One Dashboard. Set `API_KEY` from corresponding Vision One Account to its value and `FILENAME` to the target file:

   ```sh
   python3 client.py -f FILENAME -r us-1 --api_key API_KEY
   ```

   or

   using Antimalware Service server address `-a` instead of region `-r`:

   ```sh
   python3 client.py -f FILENAME -a antimalware.us-1.cloudone.trendmicro.com:443 --api_key API_KEY
   ```

   or

   using asynchronous IO example program:

   ```sh
   python3 client_aio.py -f FILENAME -a antimalware.us-1.cloudone.trendmicro.com:443 --api_key API_KEY
   ```

### Code Examples

```python
import json
import amaas.grpc

handle = amaas.grpc.init(YOUR_TMFS_SERVER, YOUR_VISION_ONE_KEY, True)

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
   handle = amaas.grpc.aio.init(YOUR_TMFS_SERVER, YOUR_VISION_ONE_KEY, True)

   tasks = [asyncio.create_task(amaas.grpc.aio.scan_file(file_name, handle))]

   scan_results = await asyncio.gather(*tasks)

   for scan_result in scan_results:
      pprint.pprint(json.loads(scan_result))

   await amaas.grpc.aio.quit(handle)


asyncio.run(scan_files())

```

## More Resources

- [License](https://github.com/trendmicro/tm-v1-fs-python-sdk/blob/main/LICENSE)
- [Changelog](https://github.com/trendmicro/cloudone-antimalware-python-sdk/blob/main/CHANGELOG.md)
- [Notice](https://github.com/trendmicro/cloudone-antimalware-python-sdk/blob/main/NOTICE)
