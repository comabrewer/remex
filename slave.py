import asyncio
import inspect
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
            response_data = json.dumps(response).encode()
            writer.write(response_data + b"\n")
            await writer.drain()

    async def exec(self, request):
        request = SimpleNamespace(**request)
        if request.obj_id is None:
            fn_obj = globals()[request.fn_name]
        else:
            obj = self._objs[request.obj_id]
            fn_obj = getattr(obj, request.fn_name)

        if inspect.iscoroutinefunction(fn_obj):
            cr_obj = fn_obj(*request.args, **request.kwargs)
        elif inspect.isroutine(fn_obj) or inspect.isclass(fn_obj):
            async def coroutine():
                return fn_obj(*request.args, **request.kwargs)
            cr_obj = coroutine()
        else:
            async def coroutine():
                return fn_obj
            cr_obj = coroutine()

        try:
            result = await cr_obj
        except Exception as exc:
            response = {"type": "exception", "data": str(exc)}
        else:
            if self._is_json_serializable(result):
                response = {"type": "value", "data": result}
            else:
                result_id = id(result)
                self._objs[result_id] = result
                response = {
                    "type": "object",
                    "data": {
                        "class": type(result).__name__,
                        "obj_id": result_id,
                        "state": {} #vars(result)
                    }
                }
        response["tid"] = request.tid
        return response

    def _is_json_serializable(self, obj):
        try:
            json.dumps(obj)
        except TypeError:
            return False
        else:
            return True

    async def _make_async(self, fun, *args, **kwargs):
        return fun(*args, **kwargs)
