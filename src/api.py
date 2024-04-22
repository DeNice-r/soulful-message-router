from pydantic import BaseModel
from typing import Union, List

from src.util import AbcNoPublicConstructor
from src.attachment import Attachment

from abc import abstractmethod
from fastapi import Request
from os import environ

from src.platforms.viber.api import send_message as sm1
from src.platforms.facebook.api import send_message as sm2
from src.platforms.telegram.api import send_message as sm3

platform_sm = {
    'viber': sm1,
    'facebook': sm2,
    'telegram': sm3
}


def send_message(unique_chat_id: str, text: str):
    """
    A function that sends a message to a user
    :param unique_chat_id: a chat id prefixed with a platform name (e.g. 'viber_1234567890')
    :param text: a text to send
    :return: None
    """
    platform, chat_id = unique_chat_id.split('_')

    if platform not in platform_sm:
        raise ValueError(f"Platform {platform} is not supported")

    print(f"Sending message to {unique_chat_id} via {platform}")
    platform_sm[platform](chat_id, text)
