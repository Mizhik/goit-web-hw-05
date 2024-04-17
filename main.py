import asyncio
import logging
from req_privat import count_date

import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


async def request(url: str) -> dict | str:
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Не вийшло в мене взнати курс. Приват не відповідає :)"


async def get_exchange():
    response = await request('https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
    return str(response)

async def get_exchange_date(date):
    response = await count_date(int(date))
    return str(response)

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                exchange = await get_exchange()
                await self.send_to_clients(exchange)
            elif message.startswith("exchange"):
                parts = message.split()
                exchange = await get_exchange_date(parts[1])
                await self.send_to_clients(exchange)
            elif message == 'Hello server':
                await self.send_to_clients("Привіт мої карапузи!")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()


if __name__ == '__main__':
    asyncio.run(main())