#!/bin/bash
for i in {1..100}
do
  python client.py -f client.py -a $TM_AM_SERVER_ADDR --api_key $TM_AM_AUTH_KEY
done
