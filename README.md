# BatchedLLM
like itertools.batched but for calling LLM

[![Ruff and Ty and PyTest checks](https://github.com/batchedllm/batchedllm/actions/workflows/lint_and_test.yml/badge.svg)](https://github.com/batchedllm/batchedllm/actions/workflows/lint_and_test.yml)

## What? Why? How?
This is a wrapper for any async client to limit amount of concurent requests. More features are planned, like caching and budget restrictions.

Sometimes you work with large dataset and model with mixed reasoning where one requst responds immidiately while another waits for what feels like eternity. This tool helps you minimize time waiting while adding some usefull features, like error handling (more features are planned).

The principle behind is overwriting python attribute getters (__getattrs__) and call functions (__call__) and storing them till later evaluation. This also means that clients can change, but the tool doesn't need to.
The intended use is for LLM clients to limit concurency, but, theoretically, and async object can be wrapped to limit its concurency and manage errors.

## Example
Run the OpenAI speed comparison example with `uv --script`:

```sh
OPENAI_BASE_URL=<url or https://api.openai.com/v1> OPENAI_MODEL=<model or gpt-5-nano> OPENAI_API_KEY=sk-... uv run --script examples/openai_speed.py
```
