from typing import Optional, Awaitable

from tornado.web import RequestHandler
from redis import asyncio as aioredis
# import asyncio
from concurrent.futures import ThreadPoolExecutor


class BaseHandler(RequestHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Content-type', 'application/json')
        self.set_header('Content-type', 'application/octet-stream')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, PUT, PATCH, OPTIONS')
        self.set_header('Access-Control-Allow-Headers',
                        'Content-Type, access_token, Access-Control-Allow-Origin, Access-Control-Allow-Headers, '
                        'X-Requested-By, Access-Control-Allow-Methods')

    async def options(self, *args, **kwargs):
        self.set_status(200)
        await self.finish()
    # # 设置多线程
    # executer = ThreadPoolExecutor(10)


class RedisHandler(BaseHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.redis_conn = aioredis.StrictRedis(**self.settings["redis"], decode_responses=True)
