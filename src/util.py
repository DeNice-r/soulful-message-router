import os
import logging
import uuid
import datetime
from abc import ABC
from typing import Type, Any, TypeVar
import requests
from dotenv import load_dotenv

load_dotenv()
local_storage_path = os.environ["LOCAL_STORAGE_PATH"]

def no_personnel_error(event, user_id, is_assigned=False):
    if is_assigned:
        message = "Ой-йой! Здається, ваш оператор тимчасово втратив зв'язок. Він повернеться найближчим часом."
    else:
        message = "Пробачте, зараз немає операторів онлайн 🥲. Ми зв'яжемося з вами найближчим часом. Поки що ви можете описати своє питання. Дякуємо за розуміння 🙏🏼."
    event.send_message(message)
    logging.warning(f'Bounced a user with id {user_id}')

def generate_file_path(file_name: str, file_type: str) -> str:
    if not file_name or not file_type:
        raise ValueError("file_name and file_type cannot be empty")
    extension = os.path.splitext(file_name)[1]
    local_path = os.path.join(
        local_storage_path,
        file_type,
        datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S") + '_' + str(uuid.uuid4()) + extension)
    return os.path.normpath(local_path)


def save_file(file_path: str, file_content: bytes, make_dirs=True) -> str | None:
    try:
        directory = os.path.dirname(file_path)
        if make_dirs and directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
        return file_path
    except FileNotFoundError:
        logging.error(f"Error: could not find file path {file_path}.")
    except IsADirectoryError:
        logging.error(f"Error: {file_path} is a directory.")
    except PermissionError:
        logging.error(f"Error: permission denied for {file_path}.")
    except Exception as e:
        logging.error(f"Error: an unexpected error occurred while saving the file:\n{e}")
    return None


def save_image(file_name: str, file_content: bytes) -> str:
    local_path = generate_file_path(file_name, AttachmentType.Image.value)
    return save_file(local_path, file_content) or ""


def download_file(url: str) -> bytes | None:
    try:
        response = requests.get(url)
        if response.ok:
            return response.content
    except Exception as e:
        logging.error(f"Error: an unexpected error occurred while downloading the file:\n{e}")
    return None


def download_attachment(attachment: 'Attachment', save=True) -> str | bytes | None:
    if save:
        path = generate_file_path(f'{attachment.name}.{attachment.extension}', attachment.type_.value)
        return save_file(path, download_file(attachment.url))
    return download_file(attachment.url)


T = TypeVar("T")


class NoPublicConstructor(type):
    """
    Metaclass that ensures a private constructor

    If a class uses this metaclass like this:

        class SomeClass(metaclass=NoPublicConstructor):
            pass

    If you try to instantiate your class (`SomeClass()`),
    a `TypeError` will be thrown.
    """

    def __call__(cls, *args, **kwargs):
        raise TypeError(
            f"{cls.__module__}.{cls.__qualname__} has no public constructor"
        )

    def _create(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        return super().__call__(*args, **kwargs)  # type: ignore


class AbcNoPublicConstructor(ABC, NoPublicConstructor):
    """
    A class to use as a metaclass that inherits both ABC and NoPublicConstructor
    """
    pass


from src.attachment import AttachmentType, Attachment
