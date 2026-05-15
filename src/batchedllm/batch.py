import json
from typing import overload, Callable
from dataclasses import dataclass, field


# TODO: add iter
@dataclass
class Batch:
    global_system_prompt: str | None = None
    _messages: list = field(default_factory=list)

    @overload
    def add_messages(
        self,
        messages_or_user: str,
        assistant: None = ...,
        *,
        system_prompt: str | None = ...,
    ): ...
    @overload
    def add_messages(
        self, messages_or_user: str, assistant: str, *, system_prompt: str | None = ...
    ): ...
    @overload
    def add_messages(
        self,
        messages_or_user: list,
        assistant: None = ...,
        *,
        system_prompt: str | None = ...,
    ): ...
    def add_messages(
        self,
        messages_or_user: list | str,
        assistant: str | None = None,
        *,
        system_prompt: str | None = None,
    ):
        """
        adds new batch, intendet for in-context learning

        system_prompt can override global_system_prompt

        accepts:
        * (str, None) -> adds string as user message (for testing)
        * (str, str)  -> adds strings as user and assistant messages (for training)
        * ([], None)  -> adds list as provided messages (for other uses)
        """

        sys_prompt = system_prompt or self.global_system_prompt

        if isinstance(messages_or_user, str) and assistant is None:
            # (str, None) case
            messages = [
                {"role": "user", "content": messages_or_user},
            ]

            if sys_prompt:
                messages.insert(0, {"role": "system", "content": sys_prompt})

        elif isinstance(messages_or_user, str) and isinstance(assistant, str):
            # (str, str) case
            messages = [
                {"role": "user", "content": messages_or_user},
                {"role": "assistant", "content": assistant},
            ]

            if sys_prompt:
                messages.insert(0, {"role": "system", "content": sys_prompt})

        elif isinstance(messages_or_user, list) and assistant is None:
            # ([], None) case
            if len(messages_or_user) == 0:
                raise ValueError("Can't add empty messages")

            if sys_prompt:
                if messages_or_user[0]["role"] == "system":
                    raise ValueError("Can't set system message if one already exists")

                messages = [
                    {"role": "system", "content": sys_prompt}
                ] + messages_or_user
            else:
                messages = messages_or_user

        else:
            raise TypeError(
                f"Unknown type combination of arguments. Expected (str, None), (str, str) or (list, None), got: ({type(messages_or_user)}, {assistant})"
            )

        self._messages.append(messages)

    def to_jsonl(self, preprocess: Callable[[list], dict] | None = None) -> str:
        """
        convert to jsonl format with optional preprocess function, intended for hypertuning where you need to specify method, model, etc
        """
        return "\n".join([json.dumps(preprocess(m) if preprocess is not None else m) for m in self._messages])

    @classmethod
    def from_jsonl(cls, text: str, global_system_prompt: str | None = None, preprocess: Callable[[dict | list], list] | None = None):
        new_instance = cls(global_system_prompt)
        for line in text.split("\n"):
            message = json.loads(line)
            if preprocess is not None:
                message = preprocess(message)
            new_instance.add_messages(message)
        return new_instance
