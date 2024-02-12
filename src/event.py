from pydantic import BaseModel
from typing import Union, List

from src.util import AbcNoPublicConstructor
from src.attachment import Attachment

from abc import abstractmethod
from fastapi import Request
from os import environ


class Event(metaclass=AbcNoPublicConstructor):
    """
    Event class for all messengers with a private constructor.
    It stores text, chat_id and original request body
    """
    original: BaseModel
    __attachments: List[Attachment] | None = None

    def __init__(self, original: BaseModel) -> None:
        if not isinstance(original, BaseModel):
            raise ValueError("original must be a pydantic BaseModel subclass")

        self.original = original

    @property
    def unique_id(self) -> str:
        """
        A method that returns a unique id for an event
        :return: a unique id
        """
        return f'{self.platform_name}_{self.chat_id}'

    @classmethod
    def create(cls, data: BaseModel) -> "Event":
        """
        A class method that creates an event from respective pydantic model
        :param data: an incoming request body, already checked for validity and in pydantic model format
        :return: an event object
        """
        if cls is Event:
            raise NotImplementedError("create should never be called on Event directly")
        return cls._create(data)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """
        A property that returns the name of the platform
        :return: platform name
        """
        raise NotImplementedError("platform_name is a subclass-implemented property")

    @property
    @abstractmethod
    def chat_id(self) -> int | str:
        """
        A property that returns a chat id
        :return: a chat id
        """
        raise NotImplementedError("chat_id is a subclass-implemented property")

    @property
    @abstractmethod
    def text(self) -> str:
        """
        A property that returns message text
        :return: a text
        """
        raise NotImplementedError("text is a subclass-implemented property")

    @property
    @abstractmethod
    def attachments(self) -> List[Attachment]:
        """
        A property that returns message attachments
        :return: List[Attachment]
        """
        if self.__attachments is None:
            self.__attachments = self._get_attachments()

        return self.__attachments

    @abstractmethod
    def _get_attachments(self) -> List[Attachment]:
        """
        A method that gathers message attachments
        :return: List[Attachment]
        """
        raise NotImplementedError("text is a subclass-implemented property")

    def download_attachments(self, save: bool = True) -> List[str | bytes | None]:
        """
        A method that downloads message attachments
        :param save: if True, saves attachments to local storage and returns paths
        :return: List[str | bytes | None]
        """
        return [attachment.download(save) for attachment in self.attachments]

    @classmethod
    async def create_if_valid(cls, request: Request) -> Union["Event", None]:
        """
        A class method that creates an event from json if it is valid
        :param request: an incoming request object
        :return: an event object or None if request is invalid
        """
        data = await cls.is_request_valid(request)
        if data:
            return cls.create(data)
        return None

    @classmethod
    async def is_request_valid(cls, request: Request) -> BaseModel | None:
        """
        A static method that checks if json is valid for this event
        :param request: an incoming request object
        :return: True if request is valid, False otherwise
        """
        return (await cls.is_request_authentic(request)) and cls.is_json_valid(await request.json())

    @staticmethod
    @abstractmethod
    async def is_request_authentic(request: Request) -> bool:
        """
        A static method that checks if request comes from a valid place
        :param request: an incoming request object
        :return: True if request is valid, False otherwise
        """
        raise NotImplementedError("is_request_authentic is a subclass-implemented method")

    @staticmethod
    @abstractmethod
    def is_json_valid(json_data: dict) -> BaseModel | None:
        """
        A static method that checks if json is valid for this event
        :param json_data: an incoming request body in json format
        :return: True if json is valid, False otherwise
        """
        raise NotImplementedError("is_json_valid is a subclass-implemented method")

    @abstractmethod
    def send_message(self, text: str) -> None:
        """
        A method that sends given message to the chat in the messenger the event was received from
        :param text: a message to send
        :return: None
        """
        raise NotImplementedError("send_message is a subclass-implemented method")


class EventFactory:
    @staticmethod
    async def create_event(request: Request, is_message_required=True) -> Event:
        """
        A static method that decides exact class for an event and creates it from json
        :param request: an incoming request object
        :param is_message_required: if True, raises ValueError if message is not present in the request, even if event is valid
        :return an event object
        """
        for messenger in Event.__subclasses__():
            evt = await messenger.create_if_valid(request)
            if evt is None:
                continue
            if is_message_required and not evt.text:
                raise ValueError("Message is required")
            return evt

        raise ValueError("Unknown request origin")
