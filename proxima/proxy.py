import aiohttp
import aiohttp.server
from urllib.parse import urljoin
import asyncio
from aiohttp.web_reqrep import Request
from functools import partial


class ProxyRequestHandler(aiohttp.server.ServerHttpProtocol):
    def __init__(self, base_url, client_session, *args, **kw):
        super().__init__(*args, **kw)
        self.base_url = base_url
        self.client_session = client_session

    def make_url(self, path):
        return urljoin(self.base_url, path)


    async def handle_request(self, message, payload):
        # XXX what is secure_proxy_ssl_header all about?
        request = Request(None, message, payload, self.transport,
                          self.reader, self.writer)
        headers = message.headers
        if request.host:
            headers.add('Forwarded', 'host=%s;proto=%s' % (
                request.host, request.scheme))
        client_response = await self.client_session.request(
            method=message.method,
            url=self.make_url(message.path),
            headers=headers,
            data=payload.read(),
            version=message.version,
            allow_redirects=False)
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
    client_session = aiohttp.ClientSession()
    f = loop.create_server(
        partial(ProxyRequestHandler, 'http://localhost:5000', client_session),
        '0.0.0.0', '7000')
    srv = loop.run_until_complete(f)
    print("serving on", srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
