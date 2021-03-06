import pytest
import asyncio
from proxima import ProxyRequestHandler
from aiohttp.test_utils import loop_context
from proxima.test_utils import TestClient
from aiohttp import web
import aiohttp
from aiohttp import HttpVersion11, StreamReader
from multidict import CIMultiDict
from unittest import mock


class MockClientSession:
    def __init__(self, loop):
        self.loop = loop
        self.forwarded = None

    async def request(self, method, url, *,
                params=None,
                data=None,
                headers=None,
                skip_auto_headers=None,
                auth=None,
                allow_redirects=True,
                max_redirects=10,
                encoding='utf-8',
                version=None,
                compress=None,
                chunked=None,
                expect100=False,
                read_until_eof=True):
        self.forwarded = headers.get('forwarded')
        if url == 'http://localhost/':
            return MockClientGetResponse(self.loop)
        elif url == 'http://localhost/post':
            response = MockClientPostResponse(self.loop, data)
            await response.feed()
            return response
        elif url == 'http://localhost/error':
            return MockClientErrorResponse(self.loop)
        elif url == 'http://localhost/redirect':
            return MockClientRedirectResponse(self.loop)
        else:
            assert False, "Should not reach"


class MockClientGetResponse:
    def __init__(self, loop):
        self.status = '200'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'blah')
        self.content.feed_eof()

    def close(self):
        pass


class MockClientErrorResponse:
    def __init__(self, loop):
        self.status = '500'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'blah')
        self.content.feed_eof()

    def close(self):
        pass


class MockClientRedirectResponse:
    def __init__(self, loop):
        self.status = '302'
        self.headers = CIMultiDict({'location': '/somewhere_else'})
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'')
        self.content.feed_eof()

    def close(self):
        pass


class MockClientPostResponse:
    def __init__(self, loop, data):
        self.status = '200'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.data = data
        # self.content.feed_data(b'got: ')
        # self.content.feed_data(data)
        # self.content.feed_eof()

    async def feed(self):
        self.content.feed_data(b'got: ')
        self.content.feed_data(await self.data)
        self.content.feed_eof()

    def close(self):
        pass


@pytest.yield_fixture
def loop():
    with loop_context() as loop:
        yield loop


@pytest.fixture
def client_session(loop):
    return MockClientSession(loop)


@pytest.fixture
def handler(loop, client_session):
    return ProxyRequestHandler('http://localhost',
                               client_session, loop=loop)


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


@asyncio
async def test_proxy_forwarded(test_client):
    resp = await test_client.get('/', headers={'host': 'localhost'})
    assert (test_client.handler.client_session.forwarded ==
            'host=localhost;proto=http')


@asyncio
async def test_proxy_backend_errors(test_client):
    resp = await test_client.get('/error')
    assert resp.status == 500


@asyncio
async def test_proxy_redirect(test_client):
    resp = await test_client.get('/redirect', allow_redirects=False)
    assert resp.status == 302
    assert resp.headers['location'] == '/somewhere_else'

# encoding, how does it work? I think it is used to encode the
# data if it's a string, but ours is an IOBase I suspect
