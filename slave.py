import asyncio
from types import SimpleNamespace
import json

class PC:

    def __init__(self, ip):
        self.ip = ip

    async def run(self, dst):
        print(f"Sending packets from {self.ip} to {dst}")
        await asyncio.sleep(1)


class RemoteSlave:
    """Runs on remote PC and executes commands.

    Has mapping of ids to objects.
    When receiving exec, creates new task.
    Has loop that checks fiished tasks.
    """

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self._objs = dict()


    async def connect(self):
        self.server = await asyncio.start_server(
            self.handle_conn, '127.0.0.1', 8888)

    async def run(self):
        async with self.server:
            await self.server.serve_forever()

    async def handle_conn(self, reader, writer):
        while True:
            data = await reader.readuntil()
            request = json.loads(data.decode())
            response = await self.exec(request)
            writer.write(json.dumps(response).encode() + b"\n")
            await writer.drain()

    async def exec(self, request):
        request = SimpleNamespace(**request)
        if request.obj_id is None:
            coroutine = self._make_async(globals()[request.fn_name], *request.args, **request.kwargs)
        else:
            obj = self._objs[request.obj_id]
            coroutine = getattr(obj, request.fn_name)(*request.args, **request.kwargs)
        try:
            result = await coroutine
        except Exception as exc:
            response = {"type": "exception", "data": str(exc)}
        else:
            if self._is_remotable(result):
                print("foo")
                result_id = id(result)
                self._objs[result_id] = result
                response = {
                    "type": "remote",
                    "data": {
                        "class": str(type(result)),
                        "obj_id": result_id,
                        "state": vars(result)
                    }
                }
            else:
                response = {"type": "result", "data": result}
        response["tid"] = request.tid
        return response

    def _is_remotable(self, obj):
        try:
            json.dumps(obj)
        except TypeError:
            return True
        else:
            return False

    async def _make_async(self, fun, *args, **kwargs):
        return fun(*args, **kwargs)
