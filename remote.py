"""
slave = Slave()
await slave.connect()
pc = slave.create("PC")
  reponse = await remote.exec()

await pc.connect() # or sync: get attributes
  self.trafficgen = await exec(self.id, getattr, "trafficgen")
pc.launch_server()


"""

import asyncio
import functools
import json

class Proxy:
    """TODO: add sync method that gets dict?"""

    def __init__(self, cls_name, obj_id, state, remex):
        self.cls_name = cls_name
        self.obj_id = obj_id
        self.remex = remex
        self.__dict__.update(state)

   def __getattr__(self, attr):
       return functools.partial(self.remex.exec, fn_name=attr, obj_id=self.obj_id)


class RemoteCmder:
    """Runs on local PC and transmits commands."""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self._tid = 0
        self._pending_requests = {}

    async def connect(self):
        """connect to remote server"""
        self.reader, self.writer = await asyncio.open_connection(
            self.ip, self.port)

    async def run(self):
        while True:
            raw = await self.reader.readuntil()
            response = json.loads(raw.decode())
            tid = response["tid"]
            self._pending_requests[tid].set_result(response)

    def disconnect(self):
        """Destroy all objects"""

    async def exec(self, obj_id, fn_name, *args, **kwargs):
        request = {
            "obj_id": obj_id,
            "fn_name": fn_name,
            "args": args,
            "kwargs": kwargs,
        }
        print(f"Sending request {request}...")
        response = await self._send(request)
        print(f"Got response {response}")

        if response["type"] == "exception":
            raise Exception(response["data"])
        elif response["type"] == "result":
            return response["data"]
        elif response["type"] == "remote":
            data = response["data"]
            proxy = Proxy(data["class"], data["obj_id"], data["state"], self)
            return proxy

    async def create(self, cls_name, *args, **kwargs):
        proxy = await self.exec(None, cls_name, *args, **kwargs)
        return proxy

    async def _send(self, request):
        request["tid"] = self._tid

        future = asyncio.Future()
        self._pending_requests[self._tid] = future
        self._tid += 1
        self.writer.write(json.dumps(request).encode() + b"\n")
        await self.writer.drain()
        await future
        return future.result()
