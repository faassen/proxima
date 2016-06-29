import aiohttp
import aiohttp.server
from urllib.parse import urljoin
import asyncio
from functools import partial


class ProxyRequester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client = aiohttp.ClientSession()

    async def request(self, message, payload):
        return await self.client.request(
            method=message.method,
            url=self.make_url(message.path))

    def make_url(self, path):
        return urljoin(self.base_url, path)


class ProxyRequestHandler(aiohttp.server.ServerHttpProtocol):
    def __init__(self, requester, *args, **kw):
        super().__init__(*args, **kw)
        self.requester = requester

    async def handle_request(self, message, payload):
        client_response = await self.requester.request(message, payload)
        response = aiohttp.Response(
            self.writer, client_response.status)
        response.add_headers(*client_response.headers.items())
        response.send_headers()
        async for slice in client_response.content.iter_any():
            response.write(slice)
        await response.write_eof()
        client_response.close()


def main():
    loop = asyncio.get_event_loop()
    requester = ProxyRequester('http://localhost:8000')
    f = loop.create_server(
        partial(ProxyRequestHandler, requester, debug="True"),
        '0.0.0.0', '7000')
    srv = loop.run_until_complete(f)
    print("serving on", srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
