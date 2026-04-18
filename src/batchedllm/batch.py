import json
from typing import overload
from dataclasses import dataclass, field


# TODO: add iter
@dataclass
class Batch:
    global_system_prompt: str | None = None
    _messages: list = field(default_factory=list)

    @overload
    def add_messages(
        self, messages_or_user: str, assistant: str, *, system_prompt: str | None = None
    ): ...
    @overload
    def add_messages(
        self,
        messages_or_user: list,
        assistant: None = None,
        *,
        system_prompt: str | None = None,
    ): ...
    def add_messages(
        self,
        messages_or_user: list | str,
        assistant: str | None = None,
        *,
        system_prompt: str | None = None,
    ):
        if isinstance(messages_or_user, str) and isinstance(assistant, str):
            # (str, str) case
            messages = [
                {"role": "user", "content": messages_or_user},
                {"role": "assistant", "content": assistant},
            ]

            sys_prompt = system_prompt or self.global_system_prompt
            if sys_prompt:
                messages.insert(0, {"role": "system", "content": sys_prompt})

        elif isinstance(messages_or_user, list) and assistant is None:
            # ([], None) case
            if len(messages_or_user) == 0:
                raise ValueError("Can't add empty messages")

            if system_prompt:
                if messages_or_user[0]["role"] != "system":
                    messages = [
                        {"role": "system", "content": system_prompt}
                    ] + messages_or_user
                else:
                    raise ValueError("Can't set system message if one already exists")
            else:
                messages = messages_or_user

        else:
            raise TypeError("Unknown combination of arguments")

        self._messages.append(messages)

    def to_openai(self) -> str:
        return "\n".join([json.dumps({"messages": m}) for m in self._messages])
