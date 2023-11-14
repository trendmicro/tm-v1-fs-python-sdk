import json
import urllib
import os

import boto3

import amaas.grpc

# define a bucket to test quarantine

quarantine_bucket = os.environ.get('QUARANTINEBUCKET')

v1_amaas_server = os.getenv('TM_AM_SERVER_ADDR')
v1_amaas_key = os.getenv('TM_AM_AUTH_KEY')

s3 = boto3.resource('s3')


def lambda_handler(event, context):
    # create v1fs connection handle
    handle = amaas.grpc.init(v1_amaas_server, v1_amaas_key, True)
    # or use v1 regions
    # handle = init_by_region(Your_V1_Region, v1_amaas_key, True)

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
        try:
            object = s3.Object(bucket, key)
            buffer = object.get().get('Body').read()
            scan_resp = amaas.grpc.scan_buffer(handle, buffer, key, ["test-tag"])
            scan_result = json.loads(scan_resp)
            if scan_result.get('scanResult', 0) > 0:
                quarantine(bucket, key)
        except Exception as e:
            print(e)
            print('Error scan object {} from bucket {}.'.format(key, bucket))

    amaas.grpc.quit(handle)


def quarantine(bucket: str, key: str):
    print(f"start to quarantine {bucket}, {key}")
    copy_source = {
        'Bucket': bucket,
        'Key': key
    }
    s3.meta.client.copy(copy_source, quarantine_bucket, f"{bucket}/{key}")

    s3.meta.client.delete_object(
        Bucket=bucket,
        Key=key
    )
