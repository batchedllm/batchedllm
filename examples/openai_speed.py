#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "openai",
#   "batchedllm @ git+https://github.com/batchedllm/batchedllm.git@main",
# ]
# ///

import os
import random
import asyncio
from time import perf_counter

from openai import AsyncOpenAI # ty: ignore[unresolved-import]
from batchedllm import Manager

PROMPTS = [
    "Come up with 4 words describing rain.",
    "Come up with 4 words describing space.",
    "Come up with 4 words describing plants.",
    "Come up with 4 words describing coffee.",
]
CONCURRENCY = 4


async def main() -> None:
    client = AsyncOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.environ.get("OPENAI_MODEL", "gpt-5-nano")

    # using openAI directly
    sequential_started = perf_counter()
    sequential_outputs = []
    for prompt in PROMPTS:
        # call 1 by 1
        response = await client.chat.completions.create(
            model=model,
            # random.randint to prevent caching
            messages=[
                {"role": "user", "content": f"{random.randint(0, 99)}. {prompt}"}
            ],
        )
        # process separetly
        try:
            sequential_outputs.append(response.choices[0].message.content.strip())
        except (AttributeError, IndexError, TypeError):
            sequential_outputs.append(repr(response))
    sequential_elapsed = perf_counter() - sequential_started

    # using Manager
    batched_started = perf_counter()
    manager = Manager(client, concurrency=CONCURRENCY, progress_bar=True)
    for prompt in PROMPTS:
        # same call name and parameters
        manager.chat.completions.create(
            model=model,
            # random.randint to prevent caching
            messages=[
                {"role": "user", "content": f"{random.randint(0, 99)}. {prompt}"}
            ],
        )

    # now we collect results
    batched_raw = await manager.process()

    # and process them already in list
    batched_outputs = []
    for response in batched_raw:
        try:
            batched_outputs.append(response.choices[0].message.content.strip())
        except (AttributeError, IndexError, TypeError):
            batched_outputs.append(repr(response))
    batched_elapsed = perf_counter() - batched_started

    print(f"Model                  : {model}")
    print(f"Prompts                : {len(PROMPTS)}")
    print(f"Batched concurrency    : {CONCURRENCY}")

    print()
    print(f"Sequential async OpenAI: {sequential_elapsed:.2f}s")
    print(f"BatchedLLM manager     : {batched_elapsed:.2f}s")
    if batched_elapsed < sequential_elapsed:
        print(f"Speedup                : {sequential_elapsed / batched_elapsed:.2f}x")

    print()
    print("Results")
    for prompt, sequential, batched in zip(
        PROMPTS, sequential_outputs, batched_outputs
    ):
        print(f"- Prompt               : {prompt}")
        print(f"  Sequential           : {sequential}")
        print(f"  Batched              : {batched}")


if __name__ == "__main__":
    asyncio.run(main())
