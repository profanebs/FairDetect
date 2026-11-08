# -*- coding: utf-8 -*-
"""fairdetect_api.py - local console backend for FairDetect.

Serves the built frontend and a small JSON API on 127.0.0.1:8790 by default.

Endpoints:
  GET  /api/health
  GET  /api/models
  POST /api/jobs            {"files":[{"name","data_b64"}], "models":[...], "judges":[...]}
  GET  /api/jobs/<id>       status + results
  GET  /api/jobs/<id>/report   standalone HTML report
  GET  /api/jobs/<id>/pdf      PDF export via headless Edge/Chrome
  POST /score               {"model": "...", "text": "..."}      (Bearer token if configured)
  POST /batch               {"model": "...", "items": [...]}     (Bearer token if configured)
  GET  /                    static frontend

Models are configured in config/models.json. This repository ships without
weights; see docs/MODEL-CONTRACT.md.
"""
import base64
import html as html_mod
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from .adapters import build_adapter
except ImportError:  # running as a script: python server/fairdetect_api.py
    from adapters import build_adapter

ROOT = Path(__file__).resolve().parent.parent          # repo root
APP_DIST = ROOT / "app" / "dist"
STRINGS_FILE = Path(__file__).resolve().parent / "report_zh.json"
CONFIG_FILE = Path(os.environ.get("FAIRDETECT_CONFIG", str(ROOT / "config" / "models.json"))).resolve()
PORT = int(os.environ.get("FAIRDETECT_PORT", "8790"))
HOST = os.environ.get("FAIRDETECT_HOST", "127.0.0.1").strip() or "127.0.0.1"
WIN, STRIDE, CAP = 8, 2, 30   # defaults; per-model values come from config

ALIASES = {}


def load_config(path):
    """Load and validate config/models.json. Returns (models, judges, default_judge)."""
    if not path.exists():
        raise SystemExit("config not found: %s (copy config/models.example.json to config/models.json)" % path)
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data.get("models") or []
    judges = data.get("judges") or []
    if not isinstance(models, list) or not isinstance(judges, list):
        raise SystemExit("config error: 'models' and 'judges' must be lists")
    seen = set()
    for m in models:
        mid = str(m.get("id") or "").strip()
        if not mid or mid in seen:
            raise SystemExit("config error: missing or duplicate model id: %r" % mid)
        seen.add(mid)
        m["id"] = mid
        m["label"] = str(m.get("label") or mid)
        m["role"] = str(m.get("role") or "model")
        ALIASES[mid.lower()] = mid
        for alias in m.get("aliases") or []:
            ALIASES[str(alias).strip().lower()] = mid
    for j in judges:
        jid = str(j.get("id") or "").strip()
        if not jid:
            raise SystemExit("config error: judge without id")
        j["id"] = jid
        j["label"] = str(j.get("label") or jid)
        for key in ("shield", "spear"):
            ref = j.get(key)
            if ref not in seen:
                raise SystemExit("config error: judge %s references unknown model %r" % (jid, ref))
        j.setdefault("mode", "or")
        j.setdefault("stat", "mean" if j["mode"] == "or" else "pct50")
    default_judge = data.get("default_judge") or (judges[0]["id"] if judges else None)
    if default_judge and default_judge not in {j["id"] for j in judges}:
        raise SystemExit("config error: default_judge %r not found" % default_judge)
    return models, judges, default_judge


MODELS, JUDGES, DEFAULT_JUDGE = load_config(CONFIG_FILE)
_ADAPTERS = {}
for _m in MODELS:
    try:
        _a = build_adapter(_m, ROOT)
        _ADAPTERS[_m["id"]] = _a
        _m["available"] = bool(_a.available())
        _m["status"] = _a.status()
    except Exception as _e:
        _ADAPTERS[_m["id"]] = None
        _m["available"] = False
        _m["status"] = "%s: %s" % (type(_e).__name__, _e)

if JUDGES:
    _default = next((j for j in JUDGES if j["id"] == DEFAULT_JUDGE), JUDGES[0])
    JUDGE_SHIELD = _default["shield"]
    JUDGE_SPEAR = _default["spear"]
else:
    JUDGE_SHIELD = None
    JUDGE_SPEAR = None

_STR = {}
if STRINGS_FILE.exists():
    _STR = json.loads(STRINGS_FILE.read_text(encoding="utf-8"))

# machine-facing auth (score/batch only; health and the browser UI stay open)
TOKEN_FILE = Path(os.environ.get("FAIRDETECT_TOKEN_FILE", str(ROOT / "server" / "service-token.txt")))
TOKEN = os.environ.get("FAIRDETECT_CONSOLE_TOKEN", "").strip()
if not TOKEN and TOKEN_FILE.exists():
    TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()


def T(key, default=""):
    return _STR.get(key, default)


# ---------------- text utils ----------------
def split_sentences(text):
    t = re.sub(r"\s+", " ", str(text)).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", t)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def windows_idx(n, win=WIN, stride=STRIDE, cap=CAP):
    if n < 4:
        return []
    if n <= win:
        return [(0, n)]
    out, i = [], 0
    while i + win <= n and len(out) < cap:
        out.append((i, i + win))
        i += stride
    tail = (max(0, n - win), n)
    if len(out) < cap and out and tail != out[-1]:
        out.append(tail)
    return out


def extract_text(name, raw):
    if name.lower().endswith(".docx"):
        import io
        import docx
        d = docx.Document(io.BytesIO(raw))
        parts = [x.text for x in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                for c in row.cells:
                    parts.append(c.text)
        return re.sub(r"\n{3,}", "\n\n", "\n".join(x for x in parts if x and x.strip())).strip()
    return raw.decode("utf-8", errors="replace")


# ---------------- scoring ----------------
_GPU_LOCK = threading.Lock()


def score_text(mid, text):
    spec = next((m for m in MODELS if m["id"] == mid), None)
    if spec is None:
        raise ValueError("unknown model: %s" % mid)
    adapter = _ADAPTERS.get(mid)
    if adapter is None:
        raise RuntimeError("model is not configured: %s" % mid)
    win = int(spec.get("win_sentences", WIN))
    stride = int(spec.get("stride_sentences", STRIDE))
    cap = int(spec.get("cap_windows", CAP))
    sents = split_sentences(text)
    idx = windows_idx(len(sents), win, stride, cap)
    if not idx:
        return None
    ws = [" ".join(sents[a:b]) for a, b in idx]
    with _GPU_LOCK:
        sc = adapter.score(ws)
    if len(sc) != len(ws):
        raise RuntimeError("adapter %s returned %d scores for %d windows" % (mid, len(sc), len(ws)))
    per = [[] for _ in range(len(sents))]
    for (a, b), s in zip(idx, sc):
        for j in range(a, b):
            per[j].append(s)
    means = [float(sum(v) / len(v)) for v in per if v]
    pct50 = 100 * sum(1 for x in means if x >= 0.5) / max(1, len(means))
    pct80 = 100 * sum(1 for x in means if x >= 0.8) / max(1, len(means))
    s90 = 100 * sum(1 for x in sc if x >= 0.9) / max(1, len(sc))
    words = len(re.findall(r"[A-Za-z']+", text))
    swords = [len(re.findall(r"[A-Za-z']+", s)) for s in sents]
    return {"pct50": round(pct50, 1), "pct80": round(pct80, 1), "s90": round(s90, 1),
            "mean": round(sum(sc) / max(1, len(sc)), 3), "mx": round(max(sc), 3),
            "mean100": round(100 * sum(sc) / max(1, len(sc)), 1),
            "nwin": len(sc), "words": words, "windows": [round(x, 4) for x in sc],
            "nsent": len(sents), "sents": [round(x, 4) for x in means], "swords": swords}


def judge_verdict(g, r, jg, gs=None, rs=None, sw=None):
    """gs/rs = per-sentence mean scores of shield/spear (optional), sw = per-sentence word counts."""
    if g is None or r is None:
        return None
    if jg.get("mode") == "or":
        # mean-bar rule: caught iff shield_mean >= g0 OR spear_mean >= r0 (both 0-1)
        s = 100.0 * max(g, r)
        fired = (g >= jg["g0"]) or (r >= jg["r0"])
        flag = (not fired) and r >= 0.90
        tier = "caught" if fired else "t2"
    else:
        s = max(g, r) if (g >= jg["g0"] or (jg["r0"] > 0 and r >= jg["r0"])) else g
        flag = (s < 20 and r >= 90)
        tier = "caught" if r >= 20 else ("t2" if s < 20 else "t1")
    band = "low" if s < 20 else ("mid" if s < 80 else "high")
    out = {"rule": jg["id"], "g": g, "r": r, "S": round(s, 1), "tier": tier, "band": band, "flag": flag}
    # AI reference rate: share of the document that crosses the SAME bar, sentence by sentence
    if jg.get("mode") == "or" and gs and rs and len(gs) == len(rs):
        n = len(gs)
        flags = [(a >= jg["g0"]) or (b >= jg["r0"]) for a, b in zip(gs, rs)]
        nf = sum(1 for f in flags if f)
        if sw and len(sw) == n and sum(sw) > 0:
            tot_w = float(sum(sw))
            fw = float(sum(w for f, w in zip(flags, sw) if f))
        else:
            tot_w, fw = float(n), float(nf)
        out["ai_rate"] = {"basis": "sentence", "rate_word": round(100 * fw / max(1.0, tot_w), 1),
                          "rate_sent": round(100 * nf / max(1, n), 1), "n_flagged": nf, "n_sent": n,
                          "g0": jg["g0"], "r0": jg["r0"]}
    return out


def resolve_model(name_in):
    return ALIASES.get(str(name_in or "").strip().lower())


def svc_doc(name_in, text):
    t0 = time.time()
    mid = resolve_model(name_in)
    if not mid:
        return {"model": name_in, "error": "unknown model: %s" % name_in, "ms": 0}
    try:
        r = score_text(mid, text)
    except Exception as e:
        return {"model": name_in, "error": "%s: %s" % (type(e).__name__, e),
                "ms": int((time.time() - t0) * 1000)}
    if r is None:
        return {"model": name_in, "error": "text too short (<4 sentences)", "ms": int((time.time() - t0) * 1000)}
    return {"model": name_in, "ai_rate": round(r["pct50"]), "pct50": r["pct50"], "pct80": r["pct80"],
            "s90": r["s90"], "mean": r["mean"], "mx": r["mx"], "nwin": r["nwin"], "words": r["words"],
            "ms": int((time.time() - t0) * 1000)}


# ---------------- jobs ----------------
JOBS = {}
JOBS_LOCK = threading.Lock()


def _model_by_id(mid):
    return next((m for m in MODELS if m["id"] == mid), None)


def _judge_by_id(jid):
    return next((j for j in JUDGES if j["id"] == jid), None)


def validate_job_request(body):
    """Normalize and validate a /api/jobs request; raise ValueError with a clear message."""
    model_ids = []
    for raw in body.get("models") or []:
        mid = resolve_model(raw)
        if not mid:
            raise ValueError("unknown model: %s" % raw)
        if mid not in model_ids:
            model_ids.append(mid)
    raw_judges = body.get("judges")
    if raw_judges is None:
        raw_judges = [DEFAULT_JUDGE] if DEFAULT_JUDGE else []
    judge_ids = []
    for raw in raw_judges:
        jid = str(raw)
        if not _judge_by_id(jid):
            raise ValueError("unknown judge: %s" % jid)
        if jid not in judge_ids:
            judge_ids.append(jid)
    if not model_ids and not judge_ids:
        raise ValueError("select at least one model or judge")
    need = set(model_ids)
    for jid in judge_ids:
        jg = _judge_by_id(jid)
        need.add(jg["shield"])
        need.add(jg["spear"])
    missing = [mid for mid in sorted(need) if not (_model_by_id(mid) or {}).get("available")]
    if missing:
        raise ValueError("model not configured: %s (edit %s; see /api/models)" % (", ".join(missing), CONFIG_FILE))
    return model_ids, judge_ids


def run_job(job):
    job["status"] = "running"
    files = job["files"]
    model_ids = list(job["models"])
    judge_ids = list(job["judges"])
    need = set(model_ids)
    for jid in judge_ids:
        jg = _judge_by_id(jid)
        need.add(jg["shield"])
        need.add(jg["spear"])
    for mid in need:
        if mid not in model_ids:
            model_ids.append(mid)
    total = len(files)
    for fi, f in enumerate(files):
        job["current"] = f["name"]
        res = {"name": f["name"], "error": None, "models": {}, "judge": {},
               "_size": "%.1f KB" % (len(f["data"]) / 1024.0)}
        try:
            text = extract_text(f["name"], f["data"])
            if len(text.split()) < 30:
                res["error"] = "text too short"
            else:
                res["_text"] = text
                for mid in model_ids:
                    r = score_text(mid, text)
                    if r:
                        res["models"][mid] = r
                for jid in judge_ids:
                    jg = _judge_by_id(jid)
                    stat = jg.get("stat", "pct50")
                    gm = res["models"].get(jg["shield"], {})
                    rm = res["models"].get(jg["spear"], {})
                    g, r = gm.get(stat), rm.get(stat)
                    gs = rs = sw = None
                    if stat == "mean":
                        gs, rs, sw = gm.get("sents"), rm.get("sents"), gm.get("swords")
                    v = judge_verdict(g, r, jg, gs, rs, sw)
                    if v:
                        res["judge"][jid] = v
        except Exception as e:
            res["error"] = "%s: %s" % (type(e).__name__, e)
        job["results"].append(res)
        job["done"] = fi + 1
    job["status"] = "done"
    job["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")


def start_job(body):
    model_ids, judge_ids = validate_job_request(body)
    files = []
    for f in body.get("files", []):
        files.append({"name": f.get("name", "unnamed"), "data": base64.b64decode(f.get("data_b64", ""))})
    job = {"id": uuid.uuid4().hex[:12], "files": files, "models": model_ids,
           "judges": judge_ids, "status": "queued", "done": 0, "total": len(files),
           "current": "", "results": [], "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    with JOBS_LOCK:
        JOBS[job["id"]] = job
    threading.Thread(target=run_job, args=(job,), daemon=True).start()
    return job


# ---------------- report ----------------
def bar_color(pct):
    if pct is None:
        return "#999"
    if pct < 20:
        return "#2e9e5b"
    if pct < 50:
        return "#c9a227"
    if pct < 80:
        return "#e07a1f"
    return "#c0392b"


def para_breaks(text, sents):
    """Display-only heuristic: sentence indices that start a new paragraph.

    Never used for scoring - the scorer always sees the flat sentence list.
    """
    out, cur = set(), 0
    for i, s in enumerate(sents):
        probe = s[:30]
        if len(probe) < 8:
            continue
        j = text.find(probe, cur)
        if j < 0:
            j = text.find(probe)
            if j < 0:
                continue
        cur = j + 1
        if i and re.search(r"\n\s*\n", text[max(0, j - 60):j]):
            out.add(i)
    return out


BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
PDF_DIR = ROOT / "ops-reports" / "pdf"


def report_pdf(job_id):
    """Render the standalone report page to a real PDF via headless Edge/Chrome.

    Returns the PDF path, or None when no browser is installed / printing failed.
    Each call uses a throwaway profile directory: reusing one profile makes a
    second headless run attach to the first and exit without writing a file.
    """
    exe = next((p for p in BROWSERS if Path(p).exists()), None)
    if not exe:
        return None
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    out = PDF_DIR / ("FairDetect-%s.pdf" % job_id)
    if out.exists():
        try:
            out.unlink()
        except OSError:
            pass
    profile = Path(tempfile.mkdtemp(prefix="fairdetect-pdf-"))
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--user-data-dir=%s" % profile,
           "--print-to-pdf=%s" % out,
           "http://127.0.0.1:%d/api/jobs/%s/report" % (PORT, job_id)]
    try:
        subprocess.run(cmd, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return None
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    # Edge can exit before the PDF is fully flushed. Wait for a stable file.
    last, stable = -1, 0
    for _ in range(80):
        if out.exists():
            size = out.stat().st_size
            if size > 1000 and size == last:
                stable += 1
                if stable >= 2:
                    return out
            else:
                stable = 0
            last = size
        time.sleep(0.25)
    return None


def report_html(job):
    esc = html_mod.escape
    RULES = tuple(j["id"] for j in JUDGES)
    jid = job.get("id", "")
    blocks = []
    for res in job["results"]:
        b = ['<section class="sub">']
        meta = res["models"].get(JUDGE_SPEAR) or next(iter(res["models"].values()), {})
        text = res.get("_text", "")
        sents = split_sentences(text)
        rule = next((x for x in RULES if res["judge"].get(x)), None)
        j = res["judge"].get(rule) if rule else None
        jg = next((x for x in JUDGES if x["id"] == rule), {}) if rule else {}
        # per-sentence scores of the headline judge pair (mean-bar rules only)
        gs = rs = thr = None
        if jg.get("mode") == "or":
            gs = res["models"].get(jg["shield"], {}).get("sents")
            rs = res["models"].get(jg["spear"], {}).get("sents")
            if gs and rs and len(gs) == len(rs) == len(sents):
                thr = (jg["g0"], jg["r0"])
            else:
                gs = rs = None
        if rs is None:  # fallback: spear model, window-share rule
            rs = res["models"].get(JUDGE_SPEAR, {}).get("sents")
            if rs and len(rs) != len(sents):
                rs = None
        # ---- 1. cover page
        b.append('<div class="band"><span>%s</span><span>%s &nbsp; %s</span></div>'
                 % (esc(T("cover_caption", "Cover Page")), esc(T("band_submission", "Submission ID")), esc(jid)))
        b.append('<p class="inst">%s</p>' % esc(T("cover_inst", "FairDetect local detector")))
        b.append('<h1 class="doc">%s</h1>' % esc(res["name"]))
        if res["error"]:
            b.append('<p class="err">%s</p></section>' % esc(res["error"]))
            blocks.append("\n".join(b))
            continue
        b.append('<h2 class="dh">%s</h2>' % esc(T("doc_details", "Document Details")))
        b.append('<div class="cover"><div class="kv">')
        for k, v in ((T("detail_judge", "Judge rule"), ", ".join(job.get("judges", [])) or "-"),
                     (T("detail_size", "File size"), res.get("_size") or "-"),
                     (T("detail_time", "Checked at"), job.get("finished") or "-"),
                     (T("detail_windows", "Windows"), str(meta.get("nwin", "?")))):
            b.append('<div class="row"><p class="k">%s</p><p class="v">%s</p></div>' % (esc(str(k)), esc(str(v))))
        b.append('</div><div class="box">')
        for v in ("%s %s" % (len(sents) if sents else "-", T("unit_sentences", "sentences")),
                  "%s %s" % ("{:,}".format(meta.get("words", 0)), T("unit_words", "words")),
                  "%s %s" % ("{:,}".format(len(text)), T("unit_chars", "characters"))):
            b.append('<p class="v">%s</p>' % esc(v))
        b.append("</div></div>")
        # ---- 2. AI writing overview
        b.append('<div class="band"><span>%s</span><span>%s &nbsp; %s</span></div>'
                 % (esc(T("ov_caption", "AI Writing Overview")), esc(T("band_submission", "Submission ID")), esc(jid)))
        ar = j.get("ai_rate") if j else None
        if ar:
            rate = ar["rate_word"]
            basis = T("ov_basis_sentence", "sentence-level bar, length weighted")
            extra = T("ov_extra_sentence", "sentence share %.1f%% (%d/%d)") % (ar["rate_sent"], ar["n_flagged"], ar["n_sent"])
        else:
            rate = (res["models"].get(JUDGE_SPEAR) or {}).get("pct50")
            basis = T("ov_basis_window", "window-level share")
            extra = T("ov_extra_window", "no per-sentence rate for this judge, falling back to window share")
        head = ("%d%% %s" % (int(round(rate)), T("ov_suffix", "detected as AI"))) if rate is not None else esc(T("ov_na", "n/a"))
        b.append('<div class="row2"><div class="colL">')
        b.append('<p class="ovhead">%s</p>' % head)
        b.append('<p class="ovsub">%s</p>' % esc(T("ov_sub", "share of text flagged as likely AI")))
        b.append('<p class="ovsub2">%s</p>' % esc(basis))
        if ar:
            b.append('<p class="tile">%d %s &nbsp;&nbsp; %.1f%%</p>'
                     % (ar["n_flagged"], esc(T("ov_suspect", "suspect sentences")), ar["rate_word"]))
            b.append('<p class="tilecap">%s</p>' % esc(T("ov_suspect_cap", "sentences flagged")))
        b.append('<p class="ovsub2">%s</p>' % esc(extra))
        if j:
            if jg.get("mode") == "or":
                b.append('<p class="verdict"><span class="pil %s">%s</span> &nbsp; %s: %s %s %.2f %s %s %s %.2f &nbsp;|&nbsp; %s %.3f / %s %.3f &nbsp;|&nbsp; S=%.1f%s</p>'
                         % (esc(j["tier"]), esc(T("tier_" + j["tier"], j["tier"])),
                            esc(T("verdict_bar", "bar")), esc(T("shield", "Shield")), esc(T("thr_ge", ">=")), jg["g0"],
                            esc(T("or_word", "or")), esc(T("spear", "Spear")), esc(T("thr_ge", ">=")), jg["r0"],
                            esc(T("shield", "Shield")), j["g"], esc(T("spear", "Spear")), j["r"], j["S"],
                            " &nbsp;|&nbsp; FLAG" if j["flag"] else ""))
            else:
                b.append('<p class="verdict"><span class="pil %s">%s</span> &nbsp; S=%s%s</p>'
                         % (esc(j["tier"]), esc(T("tier_" + j["tier"], j["tier"])), j["S"],
                            " &nbsp;|&nbsp; FLAG" if j["flag"] else ""))
        b.append('</div><div class="colR"><div class="cbox"><p class="ct">%s</p><p class="cb">%s</p></div></div></div>'
                 % (esc(T("caution_title", "Caution: review required.")), esc(T("caution_body", "AI detection is not exact."))))
        b.append('<div class="disc"><h3>%s</h3><p>%s</p></div>'
                 % (esc(T("disclaimer_title", "Disclaimer")), esc(T("disclaimer_body", "Research use only."))))
        # ---- 3. AI writing submission (the document itself)
        b.append('<div class="band"><span>%s</span><span>%s &nbsp; %s</span></div>'
                 % (esc(T("body_caption", "AI Writing Submission")), esc(T("band_submission", "Submission ID")), esc(jid)))
        if sents and (gs or rs):
            brk = para_breaks(text, sents)
            paras, cur_p, n_hit = [], [], 0
            for i, s in enumerate(sents):
                if i in brk and cur_p:
                    paras.append("".join(cur_p))
                    cur_p = []
                gg = gs[i] if gs else None
                rr = rs[i] if rs else None
                if gg is not None and rr is not None and thr:
                    pv = 100.0 * max(gg, rr)
                    hit = (gg >= thr[0]) or (rr >= thr[1])
                    tip = "%s %.2f / %s %.2f" % (T("shield", "Shield"), gg, T("spear", "Spear"), rr)
                elif rr is not None:
                    pv = 100.0 * rr
                    hit = rr >= 0.5
                    tip = "%s %.2f" % (T("spear", "Spear"), rr)
                else:
                    cur_p.append("%s " % esc(s))
                    continue
                if hit:
                    n_hit += 1
                    cls = "hl1" if pv < 50 else ("hl2" if pv < 80 else "hl3")
                    cur_p.append('<span class="%s" title="%s">%s%s</span> '
                                 % (cls, esc(tip), '<b class="an">%d</b>' % n_hit, esc(s)))
                else:
                    cur_p.append('<span title="%s">%s</span> ' % (esc(tip), esc(s)))
            if cur_p:
                paras.append("".join(cur_p))
            b.append("".join('<p class="body">%s</p>' % p for p in paras))
            b.append('<p class="legend"><i class="hl1"></i>%s<i class="hl2"></i>%s<i class="hl3"></i>%s</p>'
                     % (esc(T("lg_l1", "at the bar")), esc(T("lg_l2", "score >= 0.5")), esc(T("lg_l3", "score >= 0.8"))))
            b.append('<p class="note">%s</p>' % esc(T("body_note", "sentence scores are window means")))
        else:
            b.append('<p class="err">%s</p>' % esc(T("short_doc", "text too short")))
        # ---- 4. appendix (internal detail, collapsed)
        b.append('<details class="app"><summary>%s</summary>' % esc(T("appendix", "Model detail")))
        b.append('<table class="scores"><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
            T("model", "Model"), T("score", "Score"), T("mean", "Mean"), T("words", "words")))
        for spec in MODELS:
            r = res["models"].get(spec["id"])
            if not r:
                continue
            b.append('<tr><td>%s</td><td><span class="chip" style="background:%s">%s</span></td><td>%s</td><td>%s</td></tr>' % (
                esc(spec["label"]), bar_color(r["pct50"]), r["pct50"], r["mean100"], r["words"]))
        b.append("</table>")
        for rule2 in RULES:
            j2 = res["judge"].get(rule2)
            if not j2:
                continue
            jg2 = next((x for x in JUDGES if x["id"] == rule2), {})
            bar = ""
            if jg2.get("mode") == "or":
                bar = " [%s %.2f / %s %.2f | %s>=%.2f, %s>=%.2f]" % (
                    T("shield", "Shield"), j2["g"], T("spear", "Spear"), j2["r"],
                    T("shield", "Shield"), jg2["g0"], T("spear", "Spear"), jg2["r0"])
            ar2 = j2.get("ai_rate")
            b.append('<p class="judge">%s %s: S=%s (%s)%s%s%s</p>' % (
                T("judge", "Judge"), rule2.upper(), j2["S"], esc(T("tier_" + j2["tier"], j2["tier"])),
                (" | FLAG" if j2["flag"] else ""),
                (" | AI&nbsp;&nbsp;%.1f%%" % ar2["rate_word"]) if ar2 else "", bar))
        b.append('<p class="note">%s</p>' % esc(T("lg_sep", "window strip")))
        for spec in MODELS:
            r = res["models"].get(spec["id"])
            if not r:
                continue
            cells = "".join('<span class="w" style="background:%s" title="%.2f"></span>' % (
                bar_color(v * 100), v) for v in r["windows"])
            b.append('<div class="wrow"><span class="wlabel">%s</span>%s</div>' % (esc(spec["label"]), cells))
        b.append("</details>")
        b.append("</section>")
        blocks.append("\n".join(b))
    _tpl = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>__TITLE__</title><style>
body{font-family:"Noto Sans","Segoe UI","Microsoft YaHei",sans-serif;max-width:816px;margin:0 auto;padding:26px 34px 56px;color:#191919;background:#fff;font-size:13px;-webkit-font-smoothing:antialiased}
.hd{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #191919;padding-bottom:8px;margin-bottom:30px}
.hd h1{font-family:"Lexend Deca","Segoe UI","Microsoft YaHei",sans-serif;font-size:19px;font-weight:500;margin:0}
.hd p{margin:0;font-size:10px;color:#636363}
.sub{margin:0 0 46px}
.band{display:flex;justify-content:space-between;align-items:center;font-size:10px;color:#191919;border-bottom:1px solid #e6e6e6;padding-bottom:5px;margin:0 0 22px}
.inst{font-size:11px;color:#636363;margin:0 0 5px}
h1.doc{font-family:"Lexend Deca","Segoe UI","Microsoft YaHei",sans-serif;font-size:23px;font-weight:500;margin:0 0 24px;line-height:1.3;word-break:break-all}
h2.dh{font-size:13px;font-weight:600;margin:0 0 12px}
.cover{display:flex;gap:30px;margin:0 0 34px;align-items:flex-start}
.kv{flex:1.4 1 0;min-width:0}
.kv .row{margin:0 0 10px}
.kv .k{font-size:11px;font-weight:600;color:#636363;margin:0}
.kv .v{font-size:11px;color:#191919;margin:2px 0 0;word-break:break-all}
.box{flex:1 1 0;background:#f8f8f8;padding:12px 16px;min-width:140px}
.box .v{font-size:11px;margin:0 0 7px}
.box .v:last-child{margin-bottom:0}
.row2{display:flex;gap:26px;align-items:flex-start}
.colL{flex:1.2 1 0;min-width:0}
.colR{flex:1 1 0;min-width:0}
.ovhead{font-family:"Lexend Deca","Segoe UI","Microsoft YaHei",sans-serif;font-size:23px;font-weight:500;margin:0 0 8px}
.ovsub{font-size:11px;margin:0 0 6px;line-height:1.6}
.ovsub2{font-size:10px;color:#636363;margin:6px 0 0;line-height:1.6}
.tile{font-size:13px;font-weight:600;margin:16px 0 3px}
.tilecap{font-size:10px;color:#636363;margin:0 0 2px;line-height:1.6}
.verdict{font-size:10px;color:#191919;margin:16px 0 0;line-height:1.7}
.pil{display:inline-block;padding:2px 9px;border-radius:10px;font-size:10px;font-weight:600}
.pil.caught{background:#d0e8f9;color:#123f66}
.pil.t2{background:#efefef;color:#4a4a4a}
.pil.t1{background:#d0e8f9;color:#123f66}
.cbox{background:#d0e8f9;color:#2d2d2d;padding:11px 13px;border-radius:3px}
.cbox .ct{font-size:11px;font-weight:600;margin:0 0 4px}
.cbox .cb{font-size:10px;margin:0;line-height:1.65}
.disc{margin:26px 0 0}
.disc h3{font-size:11px;font-weight:600;color:#636363;margin:0 0 5px}
.disc p{font-size:10px;color:#636363;margin:0;line-height:1.7}
.body{font-size:14px;line-height:1.95;margin:0 0 14px;word-break:break-word}
.hl1{background:#d0e8f9;padding:1px 0}
.hl2{background:#a9d6f6;padding:1px 0}
.hl3{background:#79c0ef;padding:1px 0}
.an{font-size:9px;vertical-align:super;margin-right:2px;color:#123f66;font-weight:600}
.legend{font-size:10px;color:#636363;margin:18px 0 0}
.legend i{display:inline-block;width:11px;height:11px;margin:0 4px 0 11px;vertical-align:-1px}
.legend i:first-child{margin-left:0}
.note{font-size:10px;color:#8a8a8a;margin:10px 0 0;line-height:1.7}
.err{font-size:11px;color:#c0392b}
.app{margin:30px 0 0;border-top:1px solid #e6e6e6;padding-top:10px}
.app summary{font-size:11px;color:#636363;cursor:pointer}
table.scores{border-collapse:collapse;margin:14px 0;font-size:11px}
table.scores th,table.scores td{border:1px solid #ededed;padding:4px 8px;text-align:left}
.chip{display:inline-block;min-width:34px;text-align:center;color:#fff;border-radius:3px;padding:1px 5px;font-size:10px}
.judge{font-size:11px;margin:3px 0}
.wrow{display:flex;align-items:center;gap:6px;margin:3px 0}
.wlabel{width:170px;font-size:10px;color:#636363;text-align:right}
.w{width:15px;height:12px;border-radius:2px;display:inline-block}
.foot{margin:34px 0 0;border-top:1px solid #e6e6e6;padding-top:10px;font-size:10px;color:#8a8a8a;line-height:1.7}
@media print{body{max-width:none;padding:0 10mm 12mm}.row2,.cover,.disc,.sub{page-break-inside:avoid}.band{page-break-after:avoid}}
</style></head><body>
<div class="hd"><h1>__TITLE__</h1><p>__SUBLINE__</p></div>
__BLOCKS__
<div class="foot">__FOOT__</div>
</body></html>"""
    title = T("report_title", "FairDetect Report")
    subline = "%s %s &nbsp;|&nbsp; %s %s &nbsp;|&nbsp; %s %d" % (
        T("generated_at", "Generated"), esc(job.get("finished") or time.strftime("%Y-%m-%d %H:%M")),
        T("band_submission", "Submission ID"), esc(jid),
        T("files", "files"), len(job["results"]))
    return (_tpl.replace("__TITLE__", esc(title))
                .replace("__SUBLINE__", subline)
                .replace("__BLOCKS__", "\n".join(blocks))
                .replace("__FOOT__", esc(T("report_footer", "Local research use only."))))


# ---------------- http ----------------
CTYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
          ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon",
          ".json": "application/json", ".pdf": "application/pdf"}


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _auth_ok(self):
        if not TOKEN:
            return True
        return self.headers.get("Authorization", "") == "Bearer " + TOKEN

    def _send(self, code, data, ctype="application/json; charset=utf-8", fname=None):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        elif isinstance(data, str):
            data = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if fname:
            self.send_header("Content-Disposition", 'attachment; filename="%s"' % fname)
        if ctype.startswith("text/html") or ctype.startswith("application/json"):
            self.send_header("Cache-Control", "no-store")   # always serve the current UI / report
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/health", "/api/health"):
            return self._send(200, {"ok": True,
                                    "models": [{"id": m["id"], "available": bool(m.get("available"))}
                                               for m in MODELS],
                                    "default_judge": DEFAULT_JUDGE})
        if path == "/api/models":
            models_out = [{"id": m["id"], "label": m["label"], "role": m.get("role", "model"),
                           "available": bool(m.get("available")), "status": m.get("status", "")}
                          for m in MODELS]
            judges_out = [{k: j.get(k) for k in ("id", "label", "shield", "spear", "mode", "stat", "g0", "r0")}
                          for j in JUDGES]
            return self._send(200, {"models": models_out, "judges": judges_out,
                                    "default_judge": DEFAULT_JUDGE,
                                    "judge_shield": JUDGE_SHIELD, "judge_spear": JUDGE_SPEAR})
        m = re.match(r"^/api/jobs/([0-9a-f]+)$", path)
        if m:
            job = JOBS.get(m.group(1))
            if not job:
                return self._send(404, {"error": "no such job"})
            # underscore keys (full document text etc.) stay server-side
            results = [{k: v for k, v in res.items() if not k.startswith("_")} for res in job["results"]]
            return self._send(200, {"id": job["id"], "status": job["status"], "done": job["done"],
                                    "total": job["total"], "current": job["current"], "results": results})
        m = re.match(r"^/api/jobs/([0-9a-f]+)/report$", path)
        if m:
            job = JOBS.get(m.group(1))
            if not job:
                return self._send(404, {"error": "no such job"})
            return self._send(200, report_html(job), "text/html; charset=utf-8")
        m = re.match(r"^/api/jobs/([0-9a-f]+)/pdf$", path)
        if m:
            job = JOBS.get(m.group(1))
            if not job:
                return self._send(404, {"error": "no such job"})
            fp = report_pdf(job["id"])
            if not fp:
                return self._send(500, {"error": "pdf export failed (headless Edge/Chrome missing or timed out)"})
            return self._send(200, fp.read_bytes(), "application/pdf", fname=fp.name)
        # static
        rel = "index.html" if path == "/" else path.lstrip("/")
        fp = (APP_DIST / rel).resolve()
        if APP_DIST in fp.parents and fp.is_file():
            ctype = CTYPES.get(fp.suffix.lower(), "application/octet-stream")
            return self._send(200, fp.read_bytes(), ctype)
        return self._send(404, {"error": "not found", "hint": "frontend not built? run npm run build in app/"})

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception as e:
            return self._send(400, {"error": "bad request: %s" % e})
        if path == "/api/jobs":
            try:
                job = start_job(body)
                return self._send(200, {"id": job["id"], "total": job["total"]})
            except Exception as e:
                return self._send(400, {"error": "%s: %s" % (type(e).__name__, e)})
        if path == "/score":
            if not self._auth_ok():
                return self._send(401, {"error": "unauthorized"})
            return self._send(200, svc_doc(body.get("model"), body.get("text", "")))
        if path == "/batch":
            if not self._auth_ok():
                return self._send(401, {"error": "unauthorized"})
            t0 = time.time()
            rows = []
            for item in body.get("items", []):
                out = svc_doc(body.get("model"), item.get("text", ""))
                out["id"] = item.get("id")
                rows.append(out)
            return self._send(200, {"model": body.get("model"), "results": rows,
                                    "ms": int((time.time() - t0) * 1000)})
        return self._send(404, {"error": "not found"})


def main():
    srv = ThreadingHTTPServer((HOST, PORT), H)
    where = "http://127.0.0.1:%d" % PORT if HOST in ("127.0.0.1", "localhost") else "http://%s:%d" % (HOST, PORT)
    print("FairDetect console on %s  frontend: %s  token: %s  config: %s"
          % (where, APP_DIST, "on" if TOKEN else "OFF", CONFIG_FILE), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
