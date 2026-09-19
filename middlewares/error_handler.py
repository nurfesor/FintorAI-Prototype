# file: middlewares/error_handler.py
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logging.exception("Unhandled exception occurred: %s", e)
            message_to_answer = None
            if isinstance(event, Update):
                if event.message:
                    message_to_answer = event.message
                elif event.callback_query and event.callback_query.message:
                    message_to_answer = event.callback_query.message
            if message_to_answer:
                await message_to_answer.answer("😕 Что-то пошло не так. Пожалуйста, попробуйте позже.")
            return True
