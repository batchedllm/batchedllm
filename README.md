# BatchedLLM
like itertools.batched but for calling LLM

[![Ruff and Ty and PyTest checks](https://github.com/batchedllm/batchedllm/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/batchedllm/batchedllm/actions/workflows/lint_and_test.yml)

## Example
Run the OpenAI speed comparison example with `uv --script`:

```sh
OPENAI_BASE_URL=<url or https://api.openai.com/v1> OPENAI_MODEL=<model or gpt-5-nano> OPENAI_API_KEY=sk-... uv run --script examples/openai_speed.py
```
