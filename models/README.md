# Models

Put your own checkpoints here. This directory is ignored by git; no weights
are shipped with the repository.

Expected layout for the default `config/models.json`:

```
models/
  shield/
    config.json
    tokenizer.json
    tokenizer_config.json
    special_tokens_map.json
    model.safetensors        (or pytorch_model.bin)
  spear/
    ...
```

A "checkpoint" is any Hugging Face `AutoModelForSequenceClassification`
directory fine-tuned to distinguish AI text from human text. Binary models
(2 labels) use softmax; single-logit models use sigmoid. The AI label is read
from `id2label` when `ai_label_index` is `"auto"`.

You can also use one model as both shield and spear; see
`config/models.single.example.json`. For a local LLM endpoint, see
`config/models.openai.example.json`. For a custom HTTP scorer, see
`config/models.http.example.json`.

See `docs/MODEL-CONTRACT.md` for the full contract.
