# -*- coding: utf-8 -*-
"""check_setup.py - verify that FairDetect can see its config and models.

Usage:
  python scripts/check_setup.py
  python scripts/check_setup.py --score examples/human_style.txt
  python scripts/check_setup.py --config config/models.openai.example.json --score examples/human_style.txt
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "models.json"))
    ap.add_argument("--score", help="run one file through the default judge")
    args = ap.parse_args()

    import os
    os.environ["FAIRDETECT_CONFIG"] = str(Path(args.config).resolve())
    import fairdetect_api as fd

    print("config      : %s" % fd.CONFIG_FILE)
    print("frontend    : %s (%s)" % (fd.APP_DIST, "found" if (fd.APP_DIST / "index.html").is_file() else "MISSING"))
    print("default     : %s" % fd.DEFAULT_JUDGE)
    print()
    print("models:")
    ready = 0
    for m in fd.MODELS:
        flag = "READY  " if m.get("available") else "MISSING"
        ready += 1 if m.get("available") else 0
        print("  [%s] %-16s %-10s %s" % (flag, m["id"], m.get("role", ""), m.get("status", "")))
    print()
    print("judges:")
    for j in fd.JUDGES:
        print("  %-16s shield=%-16s spear=%-16s g0=%-6s r0=%s"
              % (j["id"], j["shield"], j["spear"], j.get("g0"), j.get("r0")))
    print()

    if ready == 0:
        print("No model is ready. Put a checkpoint under models/ and edit config/models.json.")
        print("See docs/MODEL-CONTRACT.md for the expected layout.")
        raise SystemExit(1)

    if args.score:
        path = Path(args.score)
        text = fd.extract_text(path.name, path.read_bytes())
        judge_id = fd.DEFAULT_JUDGE
        jg = next(j for j in fd.JUDGES if j["id"] == judge_id)
        print("scoring %s with judge %s ..." % (path, judge_id))
        models = {}
        try:
            for mid in dict.fromkeys((jg["shield"], jg["spear"])):
                models[mid] = fd.score_text(mid, text)
        except Exception as e:
            print("ERROR: %s: %s" % (type(e).__name__, e))
            raise SystemExit(1)
        stat = jg.get("stat", "pct50")
        gm = models.get(jg["shield"]) or {}
        rm = models.get(jg["spear"]) or {}
        gs = gm.get("sents") if stat == "mean" else None
        rs = rm.get("sents") if stat == "mean" else None
        sw = gm.get("swords") if stat == "mean" else None
        v = fd.judge_verdict(gm.get(stat), rm.get(stat), jg, gs, rs, sw)
        for mid, r in models.items():
            if r:
                print("  %-16s mean=%s pct50=%s windows=%s"
                      % (mid, r["mean"], r["pct50"], r["nwin"]))
        if v:
            print("  judge S=%s (%s) tier=%s%s"
                  % (v["S"], v["band"], v["tier"], " FLAG" if v["flag"] else ""))
            if v.get("ai_rate"):
                print("  ai_rate=%s%% (sentence share, length weighted)" % v["ai_rate"]["rate_word"])
        else:
            print("  no verdict (text too short or scores missing)")
    print()
    print("OK" if ready else "NOT READY")


if __name__ == "__main__":
    main()
