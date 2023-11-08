import argparse
import sys
import time

import amaas.grpc
from distutils.util import strtobool

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--filename', action='store', default=sys.argv[0],
                        help='file to be scanned')
    parser.add_argument('-a', '--addr', action='store', default='127.0.0.1:50051', required=False,
                        help='gRPC server address and port (default 127.0.0.1:50051)')
    parser.add_argument('-r', '--region', action='store',
                        help='AMaaS service region; e.g. us-1 or dev')
    parser.add_argument('--api_key', action='store',
                        help='api key for authentication')
    parser.add_argument('--tls', type=lambda x: bool(strtobool(x)), default=False,
                        help='enable TLS gRPC ')
    parser.add_argument('--ca_cert', action='store',
                        help='CA certificate')
    parser.add_argument('-t', '--tags', action='store', nargs='+',
                        help='list of tags')

    args = parser.parse_args()

    if args.region:
        handle = amaas.grpc.init_by_region(args.region, args.api_key, args.tls, args.ca_cert)
    else:
        handle = amaas.grpc.init(args.addr, args.api_key, args.tls, args.ca_cert)

    s = time.perf_counter()

    try:
        result = amaas.grpc.scan_file(handle, args.filename, args.tags)
        elapsed = time.perf_counter() - s
        print(f"scan executed in {elapsed:0.2f} seconds.")
        print(result)
    except Exception as e:
        print(e)

    amaas.grpc.quit(handle)
