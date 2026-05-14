import pytest  # noqa

from batchedllm.integration.openai import FinetuningSupervisor


def test_generally_works(mockAI):
    fs = FinetuningSupervisor(mockAI)  # noqa
