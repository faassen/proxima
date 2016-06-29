from aiohttp.test_utils import (
    TestClient as BaseTestClient, ClientSession, unused_port)


# XXX a hack to make it work with handlers, really should be its base
# behavior
class TestClient(BaseTestClient):
    def __init__(self, handler, loop, protocol="http"):
        self._loop = loop
        self.port = unused_port()
        self._handler = handler
        self._server = loop.run_until_complete(loop.create_server(
            lambda: handler, '127.0.0.1', self.port
        ))
        self._session = ClientSession(loop=self._loop)
        self._root = "{}://127.0.0.1:{}".format(
            protocol, self.port
        )
        self._closed = False

    def close(self):
        if not self._closed:
            loop = self._loop
            loop.run_until_complete(self._session.close())
            self._server.close()
            loop.run_until_complete(self._server.wait_closed())
            #loop.run_until_complete(self._handler.finish_connections())
            self._closed = True
