import pytest
import asyncio
from proxima import ProxyRequestHandler
from aiohttp.test_utils import loop_context
from proxima.test_utils import TestClient
from aiohttp import web
import aiohttp
from aiohttp import HttpVersion11, StreamReader
from unittest import mock


class MockClientGetResponse:
    def __init__(self, loop):
        self.status = '200'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'blah')
        self.content.feed_eof()

    def close(self):
        pass


class MockClientPostResponse:
    def __init__(self, loop, data):
        self.status = '200'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'got: ' + data)
        self.content.feed_eof()

    def close(self):
        pass


class MockRequester:
    def __init__(self, loop):
        self.loop = loop

    async def request(self, message, payload):
        if message.path == '/':
            return MockClientGetResponse(self.loop)
        elif message.path == '/post':
            data = await payload.read()
            return MockClientPostResponse(self.loop, data)

class MockMessage:
    def __init__(self, path, method):
        self.path = path
        self.method = method
        self.version = HttpVersion11


class MockPayload:
    def __init__(self):
        pass


@pytest.yield_fixture
def loop():
    with loop_context() as loop:
        yield loop


@pytest.fixture
def handler(loop):
    requester = MockRequester(loop)
    return ProxyRequestHandler(requester, loop=loop, debug=True)


@pytest.yield_fixture
def test_client(handler, loop):
    client = TestClient(handler, loop)
    yield client
    client.close()


def asyncio(f):
    def test(loop, test_client):
        loop.run_until_complete(f(test_client))
    return test


@asyncio
async def test_proxy_get(test_client):
    resp = await test_client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert text == 'blah'


@asyncio
async def test_proxy_post(test_client):
    resp = await test_client.post('/post', data=b'DATA')
    assert resp.status == 200
    text = await resp.text()
    assert text == 'got: DATA'
