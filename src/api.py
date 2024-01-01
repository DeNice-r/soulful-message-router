from pydantic import BaseModel
from typing import Union, List

from src.util import AbcNoPublicConstructor
from src.attachment import Attachment

from abc import abstractmethod
from fastapi import Request
from os import environ


def send_message(unique_chat_id: str, text: str):
    """
    A function that sends a message to a user
    :param chat_id: a chat id
    :param text: a text to send
    :return: None
    """
    platform, chat_id = unique_chat_id.split('_')

    match platform:
        case 'viber':
            from src.platforms.viber.api import send_message as sm
        case 'facebook':
            from src.platforms.facebook.api import send_message as sm
        case 'telegram':
            from src.platforms.telegram.api import send_message as sm
        case _:
            raise ValueError('Unknown platform')

    sm(chat_id, text)
