import pytest  # noqa

from batchedllm.integration.openai import TextFile


def test_generally_works():
    file = TextFile("train.jsonl")  # noqa
