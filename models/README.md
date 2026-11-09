# Models

This directory holds the checkpoints the console and CLI load.

## Option A: use the released checkpoints (recommended)

The Judge 4.0 pair is published as a GitHub release asset:

1. Download `fairdetect-models-v4.zip` from the **models-v4** release on this repository's Releases page.
2. Extract it into this directory. You should end up with:

```
models/
  shield/          <- r11-shield ep1 (conservative classifier)
    config.json
    model.safetensors
    tokenizer.json
    tokenizer_config.json
  spear/           <- r10-spear ep0 (aggressive classifier)
    config.json
    model.safetensors
    tokenizer.json
    tokenizer_config.json
```

3. Verify:

```bash
python scripts/check_setup.py
```

Both models should print `READY`.

SHA256 of the archive:

```
DF49D454B11EACE6FB5FA657DE4B2AD3A6ED425041A9C1A7E9814820FE975749
```

Licence: research and evaluation use only, non-commercial. The checkpoints were fine-tuned on corpora with non-commercial or no-redistribution terms; those terms pass through to the weights. See `docs/LIMITS.md` §13.

## Option B: bring your own checkpoint

Put any Hugging Face `AutoModelForSequenceClassification` directory here. This directory is ignored by git; only this README is tracked.

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

A "checkpoint" is any Hugging Face `AutoModelForSequenceClassification` directory fine-tuned to distinguish AI text from human text. Binary models (2 labels) use softmax; single-logit models use sigmoid. The AI label is read from `id2label` when `ai_label_index` is `"auto"`.

You can also use one model as both shield and spear; see `config/models.single.example.json`. For a local LLM endpoint, see `config/models.openai.example.json`. For a custom HTTP scorer, see `config/models.http.example.json`.

See `docs/MODEL-CONTRACT.md` for the full contract.
