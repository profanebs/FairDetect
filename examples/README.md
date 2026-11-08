# Examples

Two synthetic texts for smoke-testing the pipeline:

- `human_style.txt`: an informal, first-person paragraph with specific observations.
- `ai_style.txt`: a generic, polished policy paragraph.

They are **not** real submissions and are not evaluation data. A working model
should usually score `ai_style.txt` higher than `human_style.txt`, but nothing
in this repository guarantees that: the scores depend entirely on the model you
attach.

On the original FairDetect pair, `human_style.txt` is itself flagged (the spear
model gives it a high score). That is the known false-positive problem, not a
bug in the example. It is included on purpose: a demo that only shows clean
passes would hide the main limitation.

Use them with:

```powershell
python scripts/check_setup.py --score examples/human_style.txt
python scripts/check_setup.py --score examples/ai_style.txt
```
