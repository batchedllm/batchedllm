from dataclasses import dataclass, field

from openai import OpenAI, AsyncOpenAI

from ...batch import Batch
from .file import TextFile


@dataclass
class FinetuningSupervisor:
    client: OpenAI
    train: Batch = field(default_factory=Batch)
    validation: Batch = field(default_factory=Batch)
    test: Batch = field(default_factory=Batch)
    global_system_prompt: str | None = None # TODO: needs to be a property to update batches?
    _finetuning_jobs: list = field(default_factory=list)

    def __post_init__(self):
        if self.global_system_prompt:
            self.train.global_system_prompt = self.global_system_prompt
            self.validation.global_system_prompt = self.global_system_prompt
            self.test.global_system_prompt = self.global_system_prompt

    def create_finetuning_job(self, model: str):
        train_file = TextFile.from_batch("train.jsonl", self.train).create(self.client, "finetuning")
        validation_file = TextFile.from_batch("validate.jsonl", self.train).create(self.client, "finetuning")

        return  self.client.fine_tuning.jobs.create(
            training_file=train_file.id,
            validation_file=validation_file.id,
            model=model,
        )

    def check(self):
        pass

    def check_until_completion(self, delat: int = 10):
        pass

    def run_test(self) -> dict[str, list[str | None]]:
        job2response: dict[str, list[str | None]] = {}
        for job in self._finetuning_jobs:
            pass
        return job2response
