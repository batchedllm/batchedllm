from io import BytesIO
from dataclasses import dataclass, field
from typing import Self

from openai import OpenAI, AsyncOpenAI
from openai.types import FilePurpose
from openai.types.file_create_params import ExpiresAfter

from ...batch import Batch


@dataclass
class TextFile:
    filename: str
    _text: str = field(default_factory=str)

    @classmethod
    def from_batch(cls, filename: str, batch: Batch) -> Self:
        return cls(filename).write(batch.to_openai())

    def write(self, text: str) -> Self:
        self._text += text
        return self

    def get_size(self):
        raise NotImplementedError

    def create(
        self,
        client: OpenAI,
        purpose: FilePurpose,
        expires_after: ExpiresAfter | None = None,
        *,
        encoding: str = "utf-8",
        double_check: bool = False,
    ):
        # TODO: hashlib? do we need maximum len? do we need size comparison?
        file_name = f"{hash(self._text):.16}-{self.filename}"
        for file in client.files.list():
            if (
                file.filename == file_name
                and file.size == self.get_size()
                and file.purpose == purpose
            ):
                if double_check:
                    raise NotImplementedError

                return file

        return client.files.create(
            file=(file_name, BytesIO(self._text.encode(encoding))),
            purpose=purpose,
            expires_after=expires_after,
        )

    async def async_create(
        self,
        client: AsyncOpenAI,
        purpose: FilePurpose,
        expires_after: ExpiresAfter | None = None,
        *,
        encoding: str = "utf-8",
        double_check: bool = False,
    ):
        raise NotImplementedError
