from os import environ
import os
import logging
import uuid
import datetime
from abc import ABC
from typing import Type, Any, TypeVar
import requests
from dotenv import load_dotenv
from random import choice as random_choice
import boto3
from botocore.exceptions import ClientError

load_dotenv()
local_storage_path = environ.get("LOCAL_STORAGE_PATH")

def send_missed_a_message_email(to: str, chat_id: int):
    ses_client = boto3.client(
        'ses',
        region_name=environ.get('AWS_REGION'),
        aws_access_key_id=environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=environ.get('AWS_SECRET_ACCESS_KEY')
    )

    try:
        response = ses_client.send_email(
            Source=f'Чат Soulful <notifications@{environ.get("AWS_SES_FROM_IDENTITY")}>',
            Destination={
                'ToAddresses': [to]
            },
            Message={
                'Subject': {
                    'Data': 'У вас нове повідомлення на Soulful'
                },
                'Body': {
                    'Html': {
                        'Data': f"Ви отримали нове повідомлення на Soulful в чаті #{chat_id}. <a href=http://{'soulful.pp.ua' if environ.get('STAGE') == 'prod' else 'localhost'}/chat>Перейдіть на платформу, щоб відповісти</a>."
                    }
                }
            }
        )
    except ClientError as e:
        print("An error occurred: ", e.response['Error']['Message'])

def choose_personnel(personnel_ids: list[str]):
    return random_choice(personnel_ids) if personnel_ids else None

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
