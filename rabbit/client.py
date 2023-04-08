import json
from asyncio import AbstractEventLoop

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from aiormq import AMQPConnectionError

from config.settings import QueueSettings


class Rabbit:
    connection_pool: Pool
    channel_pool: Pool

    def __init__(self, settings: QueueSettings = QueueSettings()):
        self.settings = settings

    async def __call__(self) -> "Rabbit":
        if not self.channel_pool:
            raise ValueError("channel_pool not available. Run setup() first.")
        return self

    async def setup(self, loop: AbstractEventLoop) -> None:
        self.connection_pool: Pool = Pool(  # type: ignore
            self.get_connection, max_size=2, loop=loop
        )
        self.channel_pool: Pool = Pool(  # type: ignore
            self.get_channel, max_size=10, loop=loop
        )

    async def get_connection(self) -> AbstractRobustConnection:
        try:
            return await aio_pika.connect_robust(
                f"amqp://"
                f"{self.settings.username}:"
                f"{self.settings.password}@"
                f"{self.settings.host}/"
            )
        except AMQPConnectionError:
            raise ConnectionError("You should first start the bet maker service")

    async def get_channel(self) -> aio_pika.Channel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    async def consume_messages(self) -> None:
        async with self.channel_pool.acquire() as channel:
            queue: aio_pika.Queue = await channel.declare_queue(  # type: ignore
                QueueSettings.queue_name_bets, auto_delete=False
            )
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():  # type: ignore
                        j = json.loads(message.body)  # type: ignore
                        print(j)

    async def publish(self, message: str) -> None:
        async with self.channel_pool.acquire() as channel:  # type: ignore
            await channel.default_exchange.publish(
                aio_pika.Message(message.encode()),
                self.settings.queue_name_events,
            )
