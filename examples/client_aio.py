import argparse
import time
import asyncio

import amaas.grpc.aio


async def main(args):
    if args.region:
        handle = amaas.grpc.aio.init_by_region(args.region, args.api_key, args.tls, args.ca_cert)
    else:
        handle = amaas.grpc.aio.init(args.addr, args.api_key, args.tls, args.ca_cert)

    tasks = set()
    for file_name in args.filename:
        task = asyncio.create_task(
            amaas.grpc.aio.scan_file(
                channel=handle, file_name=file_name, pml=args.pml,
                tags=args.tags, feedback=args.feedback, verbose=args.verbose, digest=args.digest)
        )
        tasks.add(task)

    s = time.perf_counter()

    results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - s

    print(f"scan tasks are executed in {elapsed:0.2f} seconds.")

    await amaas.grpc.aio.quit(handle)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--filename', action='store', nargs='+', required=True,
                        help='list of files to be scanned')
    parser.add_argument('-a', '--addr', action='store', default='127.0.0.1:50051', required=False,
                        help='gRPC server address and port (default 127.0.0.1:50051)')
    parser.add_argument('-r', '--region', action='store',
                        help='AMaaS service region; e.g. us-east-1 or eu-central-1')
    parser.add_argument('--api_key', action='store',
                        help='api key for authentication')
    parser.add_argument('--tls', action=argparse.BooleanOptionalAction, default=False,
                        help='enable/disable TLS gRPC ')
    parser.add_argument('--ca_cert', action='store',
                        help='CA certificate')
    parser.add_argument('--pml', action=argparse.BooleanOptionalAction, default=False,
                        help='enable/disable predictive machine learning detection')
    parser.add_argument('-t', '--tags', action='store', nargs='+',
                        help='list of tags')
    parser.add_argument('--feedback', action=argparse.BooleanOptionalAction, default=False,
                        help='enable/disable feedback for predictive machine learning detection')
    parser.add_argument('-v', '--verbose', action=argparse.BooleanOptionalAction, default=False,
                        help='enable/disable log verbose mode')
    parser.add_argument('--digest', action=argparse.BooleanOptionalAction, default=True,
                        help='enable/disable digest calculation')

    arguments = parser.parse_args()

    scan_results = asyncio.run(main(arguments))

    for scan_result in scan_results:
        print(scan_result)
