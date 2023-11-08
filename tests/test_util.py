import grpc
import pytest
from unittest.mock import patch, call, mock_open

import amaas.grpc.util


#
# Test _init_by_region_util is invoked with correct arguments.
#
@patch("amaas.grpc.util._init_util")
def test_init_by_region_util(utilmock):
    amaas.grpc.util._init_by_region_util("au-1", "dummy_key")

    utilmock.assert_called_with('antimalware.au-1.cloudone.trendmicro.com:443', 'dummy_key', True, None, False)


#
# Test insecure channel is created.
#
def test_insecure_channel():
    channel = amaas.grpc.util._init_by_region_util('us-1', None, False, None, False)
    assert type(channel) == grpc._channel.Channel


#
# Test insecure aio channel is created.
#
def test_aio_insecure_channel():
    channel = amaas.grpc.util._init_by_region_util('us-1', None, is_aio_channel=True)
    assert type(channel) == grpc.aio._channel.Channel


#
# Test secure channel is created.
#
def test_secure_channel():
    channel = amaas.grpc.util._init_by_region_util('us-1', None, True, None, False)
    assert type(channel) == grpc._channel.Channel


#
# Test secure aio channel is created.
#
def test_aio_secure_channel():
    channel = amaas.grpc.util._init_by_region_util('us-1', None, True, None, is_aio_channel=True)
    assert type(channel) == grpc.aio._channel.Channel


#
# Test default SSL only channel.
#
@patch('grpc.secure_channel')
def test_def_ssl_only_channel(channel_mock):
    amaas.grpc.util._init_by_region_util('us-1', None, True, None, False)

    args = channel_mock.call_args.args
    assert type(args[1]._credentials) == grpc._cython.cygrpc.SSLChannelCredentials


#
# Test SSL only channel.
#
#@patch("builtins.open", new_callable=mock_open, read_data=SERVER_CERT)
@patch('grpc.secure_channel')
def test_ssl_only_channel(channel_mock):
    amaas.grpc.util._init_by_region_util('us-1', None, True, "fake_server_cert.pem", False)

    args = channel_mock.call_args.args
    assert type(args[1]._credentials) == grpc._cython.cygrpc.SSLChannelCredentials


#
# Test api key composite channel credential.
#
@patch('amaas.grpc.util._GrpcAuth')
@patch('grpc.secure_channel')
def test_composite_channel_with_apikey(channel_mock, auth_mock):
    channel = amaas.grpc.util._init_by_region_util('us-1', "abcabc12345678", True, "fake_server_cert.pem", False)

    auth_mock.assert_called_with('ApiKey abcabc12345678',)

    args = channel_mock.call_args.args
    assert type(args[1]._credentials) == grpc._cython.cygrpc.CompositeChannelCredentials

