import asyncio
import remote
import slave


class PC:

    def __init__(self, ip):
        self.ip = ip

    async def run(self, dst):
        print(f"Sending packets from {self.ip} to {dst}")
        await asyncio.sleep(1)


async def main():
    node = slave.RemoteSlave("127.0.0.1", 8888)
    await node.connect()
    asyncio.create_task(node.run())

    cmder = remote.RemoteCmder("127.0.0.1", 8888)
    await cmder.connect()
    asyncio.create_task(cmder.run())

    # low-level API
    proxy = await cmder.exec(None, "PC", ip="127.0.0.1")
    # print("run")
    await cmder.exec(proxy.obj_id, "run", dst="DST")

    # high-level API with proxy object
    proxy_pc = await cmder.create("PC", ip="127.0.0.1")
    await proxy_pc.run(dst="DST")


if __name__ == "__main__":
    asyncio.run(main())