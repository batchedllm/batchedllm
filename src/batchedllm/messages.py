from typing import TypedDict, overload, Literal, Sequence, Any


class SystemMessage(TypedDict):
    role: Literal["system", "developer"]
    content: str


class UserMessage(TypedDict):
    role: Literal["user"]
    content: str


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: str  # | Any


type Message = SystemMessage | UserMessage | AssistantMessage  # | Any


class Messages(list):
    """helper for creating messages without boilerplate"""

    @overload
    @classmethod
    def parse(
        cls,
        messages_or_user: str,
        assistant: None = None,
        *,
        system_prompt: str,
    ) -> Sequence[SystemMessage | UserMessage]: ...
    @overload
    @classmethod
    def parse(
        cls,
        messages_or_user: str,
        assistant: None = None,
        *,
        system_prompt: None = None,
    ) -> Sequence[UserMessage]: ...
    @overload
    @classmethod
    def parse(
        cls, messages_or_user: str, assistant: str, *, system_prompt: str
    ) -> Sequence[SystemMessage | UserMessage | AssistantMessage]: ...
    @overload
    @classmethod
    def parse(
        cls, messages_or_user: str, assistant: str, *, system_prompt: None = None
    ) -> Sequence[UserMessage | AssistantMessage]: ...
    @overload
    @classmethod
    def parse(
        cls,
        messages_or_user: list[Message],
        assistant: None = None,
        *,
        system_prompt: str,
    ) -> Sequence[AssistantMessage | Message]: ...
    @overload
    @classmethod
    def parse(
        cls,
        messages_or_user: list[Message],
        assistant: None = None,
        *,
        system_prompt: None = None,
    ) -> Sequence[Message]: ...
    @classmethod
    def parse(
        cls,
        messages_or_user: list[Message] | str,
        assistant: str | None = None,
        *,
        system_prompt: str | None = None,
    ) -> Sequence[Message]:
        """
        parse messages from type

        accepts:
        * (str, None) -> adds string as user message (usefull for testing)
        * (str, str)  -> adds strings as user and assistant messages (usefull for training)
        * ([], None)  -> adds list as provided messages (for other cases)
        """
        # (str, None) case
        if isinstance(messages_or_user, str) and assistant is None:
            messages = [
                UserMessage({"role": "user", "content": messages_or_user}),
            ]
        # (str, str) case
        elif isinstance(messages_or_user, str) and isinstance(assistant, str):
            messages = [
                UserMessage({"role": "user", "content": messages_or_user}),
                AssistantMessage({"role": "assistant", "content": assistant}),
            ]
        # ([], None) case
        elif isinstance(messages_or_user, list) and assistant is None:
            if len(messages_or_user) == 0:
                raise ValueError("Can't add empty messages")
            messages = messages_or_user
        else:
            raise TypeError(
                f"Unknown type combination of arguments. Expected (str, None), (str, str) or (list, None), got: ({type(messages_or_user)}, {assistant})"
            )

        if system_prompt:
            if messages[0]["role"] == "system":
                raise ValueError("Can't set system message if one already exists")

            messages = [
                SystemMessage({"role": "system", "content": system_prompt})
            ] + messages

        return messages


#     def with_system_message(self, content: str, role: Literal["system", "developer"] = "system") -> Sequence[UserMessage|Message]:
#         return  list(self) + [SystemMessage(role=role, content=content)]


#     def with_user_message(self, content: str) -> Sequence[UserMessage|Message]:
#         return  list(self) + [UserMessage(role="user", content=content)]

#     def with_assistant_message(self, content: str) -> Sequence[UserMessage|Message]:
#         return  list(self) + [AssistantMessage(role="assistant", content=content)]

# m = Messages().with_user_message("what's up?").with_assistant_message("nothing much, what's up with you?")
