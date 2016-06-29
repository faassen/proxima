import pytest
import asyncio
from proxima import ProxyRequestHandler
from aiohttp.test_utils import loop_context
from proxima.test_utils import TestClient
from aiohttp import web
import aiohttp
from aiohttp import HttpVersion11, StreamReader
from unittest import mock


class RequestHandler(aiohttp.server.ServerHttpProtocol):
    async def handle_request(self, message, payload):
          response = aiohttp.Response(
              self.writer, 200, http_version=message.version
          )
          response.add_header('Content-Type', 'text/html')
          response.add_header('Content-Length', '18')
          response.send_headers()
          response.write(b'<h1>It Works!</h1>')
          await response.write_eof()


#class MockContent:
#     def iter_any(self):
#         async def read_func():
#             await "Foo"
#             await "Bar"
#             await "Baz"
#         return AsyncStreamIterator(read_func)


class MockClientResponse:
    def __init__(self, loop):
        self.status = '200'
        self.headers = {}
        self.content = StreamReader(loop=loop)
        self.content.feed_data(b'blah')
        self.content.feed_eof()

    def close(self):
        pass

class MockRequester:
    def __init__(self, loop):
        self.loop = loop

    async def request(self, message, payload):
        return MockClientResponse(self.loop)


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

    # loop.create_server(
    #     partial(ProxyRequestHandler, requester, debug="True"),
    #     '0.0.0.0', '7000')
    
    # async def handle(request):
    #    return web.Response(body=b"Hello, world")
    # result = web.Application(loop=loop)
    # result.router.add_route('GET', '/', handle)
    # return result


@pytest.yield_fixture
def test_client(handler, loop):
    client = TestClient(handler, loop)
    yield client
    client.close()


def wrap(f):
    def test(loop, test_client):
        loop.run_until_complete(f(test_client))
    return test

# def test_get_route(loop, test_client):
#     def test_get_route():
#         nonlocal test_client
#         resp = yield from test_client.request("GET", "/")
#         assert resp.status == 200
#         text = yield from resp.text()
#         assert "Hello, world" in text

#     loop.run_until_complete(test_get_route())

# @wrap
# async def test_2(test_client):
#     resp = await test_client.request("GET", "/")
#     assert resp.status == 200
#     text = await resp.text()
#     assert "Hello, world" in text

@wrap
async def test_3(test_client):
    resp = await test_client.request('GET', '/')
    assert resp.status == 200
    text = await resp.text()
    assert text == 'blah'

# @pytest.mark.asyncio
# async def test_proxy():
#     srv = ProxyRequestHandler(MockRequester())

#     transport = mock.Mock()

#     srv.connection_made(transport)
#     srv.writer = mock.Mock()

#     message = mock.Mock()
#     message.headers = []
#     message.version = (1, 1)
#     await srv.handle_request(message, mock.Mock())

#     content = b''.join(
#         [c[1][0] for c in list(srv.writer.write.mock_calls)])
#     assert content == b'blah'

# @pytest.mark.asyncio
# async def test_proxy():
#     h = ProxyRequestHandler(MockRequester())
#     await h.handle_request(MockMessage('/', 'GET'), MockPayload())
#     assert r == "Foo"
