# BatchedLLM
like itertools.batched but for calling LLM

## Example
Run the OpenAI speed comparison example with `uv --script`:

```sh
OPENAI_BASE_URL=<url or https://api.openai.com/v1> OPENAI_MODEL=<model or gpt-5-nano> OPENAI_API_KEY=sk-... uv run --script examples/openai_speed.py
```
