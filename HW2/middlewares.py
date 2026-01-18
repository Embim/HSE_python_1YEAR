from aiogram import BaseMiddleware
from aiogram.types import Message
from logger import log

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        log.info(f"Сообщение {event.text}")
        return await handler(event, data)