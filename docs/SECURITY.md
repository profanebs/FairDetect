# Security

FairDetect is a local research tool, not a hardened service.

## Default posture

- The HTTP server binds `127.0.0.1` by default.
- `/api/jobs` has no authentication. Anyone who can reach the port can submit files and read job results.
- `/score` and `/batch` require a Bearer token **if** `FAIRDETECT_CONSOLE_TOKEN` or `server/service-token.txt` is set. If neither is set, they are open.
- There is no TLS, no rate limiting, no audit log, and no multi-user isolation.
- Uploaded files are held in memory and are lost on restart. Reports and PDFs are written to `ops-reports/` in plain text.

## If you enable LAN access

Set `FAIRDETECT_HOST=0.0.0.0` only when you need it, and always set a token:

```powershell
$env:FAIRDETECT_HOST = "0.0.0.0"
$env:FAIRDETECT_CONSOLE_TOKEN = "a-long-random-string"
python server/fairdetect_api.py
```

A token protects `/score` and `/batch`, **not** `/api/jobs`. Put the server behind a firewall or a reverse proxy if it is reachable by untrusted networks. Do not expose it to the public internet.

## Adapters and outbound requests

- `hf` makes no network calls after the model is downloaded.
- `openai` sends window text to the configured `base_url`. If that is a remote service, the text leaves your machine.
- `http` sends window text to the configured `url`.
- All adapters ignore system proxy settings so that localhost endpoints work. This also means a misconfigured remote URL will connect directly.

## Secrets

Do not put secrets in `config/models.json`. Use `${ENV_VAR}` expansion or `api_key_env`:

```json
{
  "adapter": "openai",
  "base_url": "http://127.0.0.1:11434/v1",
  "model": "qwen2.5:7b",
  "api_key_env": "LOCAL_LLM_API_KEY"
}
```

`server/service-token.txt` is git-ignored.

## Reporting a problem

This is an archived research prototype. If you find a security issue that could affect users, open a GitHub issue with a minimal reproduction. Do not include student data or secrets in the report.
