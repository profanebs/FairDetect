# -*- coding: utf-8 -*-
"""judge.py - portable command-line scorer for FairDetect.

It reuses the same window pipeline and judge rules as the web console, but
prints to stdout instead of serving a page. Models come from config/models.json.

Examples
--------
  python judge/judge.py --list
  python judge/judge.py --config config/models.json essay.txt
  python judge/judge.py --config config/models.json --json essay.docx
  python judge/judge.py --config config/models.json --batch meta.jsonl --out results.jsonl

meta.jsonl lines: {"id": "...", "text_path": "relative/or/absolute.txt",
                   "task_type": "...", "generator": "..."}
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))


def _load_module(config_path):
    os.environ["FAIRDETECT_CONFIG"] = str(Path(config_path).resolve())
    import fairdetect_api as fd
    return fd


def _read_text(fd, path):
    path = Path(path)
    return fd.extract_text(path.name, path.read_bytes())


def _score(fd, text, judge_id):
    jg = next((j for j in fd.JUDGES if j["id"] == judge_id), None)
    if jg is None:
        raise SystemExit("unknown judge: %s (available: %s)"
                         % (judge_id, ", ".join(j["id"] for j in fd.JUDGES)))
    models = {}
    for mid in dict.fromkeys((jg["shield"], jg["spear"])):
        models[mid] = fd.score_text(mid, text)
    stat = jg.get("stat", "pct50")
    gm = models.get(jg["shield"]) or {}
    rm = models.get(jg["spear"]) or {}
    g, r = gm.get(stat), rm.get(stat)
    gs = rs = sw = None
    if stat == "mean":
        gs, rs, sw = gm.get("sents"), rm.get("sents"), gm.get("swords")
    verdict = fd.judge_verdict(g, r, jg, gs, rs, sw)
    return models, verdict


def _print_list(fd):
    print("config: %s" % fd.CONFIG_FILE)
    print("models:")
    for m in fd.MODELS:
        print("  %-16s %-6s %-8s %s" % (m["id"], m.get("role", ""),
                                         "ready" if m.get("available") else "MISSING",
                                         m.get("status", "")))
    print("judges:")
    for j in fd.JUDGES:
        print("  %-16s shield=%s spear=%s g0=%s r0=%s"
              % (j["id"], j["shield"], j["spear"], j.get("g0"), j.get("r0")))
    print("default_judge: %s" % fd.DEFAULT_JUDGE)


def _row(fd, item, text, judge_id):
    row = {"id": item.get("id", ""), "task_type": item.get("task_type", ""),
           "generator": item.get("generator", "")}
    try:
        models, verdict = _score(fd, text, judge_id)
    except Exception as e:
        row["error"] = "%s: %s" % (type(e).__name__, e)
        return row
    for mid, r in models.items():
        if not r:
            continue
        row["%s_mean" % mid] = r["mean"]
        row["%s_pct50" % mid] = r["pct50"]
        row["%s_nwin" % mid] = r["nwin"]
    if verdict:
        row["judge"] = verdict["rule"]
        row["judge_S"] = verdict["S"]
        row["band"] = verdict["band"]
        row["tier"] = verdict["tier"]
        row["flag"] = verdict["flag"]
        if verdict.get("ai_rate"):
            row["ai_rate"] = verdict["ai_rate"]["rate_word"]
    row["words"] = next((r.get("words") for r in models.values() if r), None)
    return row


def main():
    ap = argparse.ArgumentParser(description="FairDetect portable scorer")
    ap.add_argument("file", nargs="?", help="single .txt/.md/.docx file")
    ap.add_argument("--config", default=str(ROOT / "config" / "models.json"))
    ap.add_argument("--judge", default=None, help="judge id (default: config default_judge)")
    ap.add_argument("--list", action="store_true", help="list configured models and judges")
    ap.add_argument("--batch", help="meta.jsonl for batch scoring")
    ap.add_argument("--out", help="results jsonl path (batch mode)")
    ap.add_argument("--base", help="base dir for relative text_path (default: meta file dir)")
    ap.add_argument("--json", action="store_true", help="machine-readable single output")
    args = ap.parse_args()

    fd = _load_module(args.config)
    judge_id = args.judge or fd.DEFAULT_JUDGE
    if args.list:
        _print_list(fd)
        return
    if not judge_id:
        raise SystemExit("no judge configured; pass --judge or set default_judge in the config")

    if args.batch:
        meta_path = Path(args.batch)
        if not meta_path.exists():
            raise SystemExit("meta not found: %s" % meta_path)
        base = Path(args.base) if args.base else meta_path.parent
        rows = []
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            text_path = Path(item.get("text_path", ""))
            if not text_path.is_absolute():
                text_path = base / text_path
            try:
                text = _read_text(fd, text_path)
            except Exception as e:
                rows.append({"id": item.get("id", ""), "error": "%s: %s" % (type(e).__name__, e)})
                continue
            rows.append(_row(fd, item, text, judge_id))
        out_path = Path(args.out) if args.out else meta_path.with_suffix(".results.jsonl")
        with out_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        tiers = {}
        for row in rows:
            key = row.get("tier", "error")
            tiers[key] = tiers.get(key, 0) + 1
        print("scored %d items -> %s" % (len(rows), out_path))
        print("tiers: %s" % tiers)
        print("flags: %d" % sum(1 for row in rows if row.get("flag")))
        return

    if not args.file:
        ap.print_help()
        raise SystemExit(2)
    path = Path(args.file)
    row = _row(fd, {"id": path.stem}, _read_text(fd, path), judge_id)
    if args.json:
        print(json.dumps(row, ensure_ascii=False))
        return
    if row.get("error"):
        print("ERROR: %s" % row["error"])
        raise SystemExit(1)
    print("file   : %s  (%s words)" % (path.name, row.get("words")))
    for mid in dict.fromkeys((next(j for j in fd.JUDGES if j["id"] == judge_id))[k]
                             for k in ("shield", "spear")):
        if "%s_mean" % mid in row:
            print("model  : %-16s mean=%-6s pct50=%-6s windows=%s"
                  % (mid, row["%s_mean" % mid], row["%s_pct50" % mid], row["%s_nwin" % mid]))
    print("judge  : %s  S=%s (%s)  tier=%s%s"
          % (row["judge"], row["judge_S"], row["band"], row["tier"],
             "  FLAG" if row.get("flag") else ""))
    if "ai_rate" in row:
        print("ai_rate: %s%% (sentence share, length weighted)" % row["ai_rate"])


if __name__ == "__main__":
    main()
