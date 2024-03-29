import hashlib
import hmac
import json
from typing import List

from starlette.requests import Request

from src.event import Event
from src.attachment import Attachment, AttachmentType
from src.platforms.facebook import api
from src.platforms.facebook.model import Model

from os import environ, path
from dotenv import load_dotenv

load_dotenv()
facebook_verification_token = environ["FACEBOOK_VERIFICATION_TOKEN"]
facebook_app_secret = environ["FACEBOOK_APP_SECRET"]


class FacebookEvent(Event):
    original: Model  # this is needed to tell pydantic that original is a Model

    @property
    def platform_name(self) -> str:
        return 'facebook'

    @property
    def chat_id(self) -> int | str:
        return self.original.entry[0].messaging[0].sender.id

    @property
    def text(self) -> str:
        return self.original.entry[0].messaging[0].message.text

    def _get_attachments(self) -> List[Attachment]:
        attachments = []
        original_attachments = self.original.entry[0].messaging[0].message.attachments
        if original_attachments is None:
            return attachments
        for attachment in original_attachments:
            url = attachment.payload.url
            file_name = path.splitext(url.split('/')[-1].split('?')[0])

            try:
                attachment_type = AttachmentType(attachment.type)
            except ValueError:
                continue

            attachments.append(
                Attachment(
                    name=file_name[0],
                    extension=file_name[-1],
                    type_=attachment_type,
                    url=url
                )
            )
        return attachments

    @staticmethod
    async def is_request_authentic(request: Request) -> bool:
        try:
            raw_body = await request.body()
            body = json.loads(raw_body.decode("utf-8"))
            signature_hash = request.headers.get("X-Hub-Signature-256").split("=")[1]
            h = hmac.new(facebook_app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
            if signature_hash == h and body["object"] == "page":
                return True
        except:
            return False
        return False

    @staticmethod
    def is_json_valid(json_data: dict) -> Model | None:
        try:
            return Model(**json_data)
        except:
            return None

    def send_message(self, text) -> None:
        api.send_message(self.chat_id, text)
