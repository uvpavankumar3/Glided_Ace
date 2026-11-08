"""Writes APPENDIX.md (Claims & Evidence, priced actions, sensitivity, AI disclosure) from build/data.json."""
import json, sys
d = json.load(open(sys.argv[1])); out = sys.argv[2]
f = lambda v: ("−" if v < 0 else "") + f"${abs(v):,.0f}"
L = ["# Appendix — Claims & Evidence", "",
     "Fictional casino, synthetic data (release 0.9.0-draft). Full window Jan 1–Jun 30, 2025. Every figure is reproducible with `./run.sh <path-to-dashboard-royale>`. The same table is on the dashboard's *Claims & evidence* page.", ""]
for c in d["claims"]:
    L += [f"## {c['id']}. {c['claim']}", "", f"- **Table / query:** {c['query']}", f"- **Result:** {c['result']}",
          f"- **Alternative explanation tested:** {c['alt']}", f"- **Limitation:** {c['limit']}", f"- **Dashboard page:** `#{c['page']}`", ""]
P = d["plan"]
L += ["## Priced actions (30 days from July 1, 2025)", "", "Cost = qty × (unit cost + daily cost × max(0, 30 − lead days)).", "",
      "| Action | Target | Cost | Why (cause) | Expected effect | Uncertainty | Measurement |", "|---|---|---|---|---|---|---|"]
for a in P["actions"]:
    L.append(f"| {a['name']} ({a['id']}) | {a['target']} | {f(a['cost'])} | {a['why']} | {a['effect']} | {a['uncertainty']} | {a['measure']} |")
L += ["", f"**Total spent {f(P['total'])}; kept {f(P['kept'])}.**", "", "### Sensitivity (theo-equivalent value: 30 days / 90 days if the effect persists)", "",
      "| Action | Cost | Low | Base | High |", "|---|---|---|---|---|"]
for r in P["sensitivity"]:
    L.append(f"| {r['action']} | {f(r['cost'])} | " + " | ".join(f"{r[k]['label']}: {f(r[k]['v30'])} / {f(r[k]['v90'])}" for k in ("low", "base", "high")) + " |")
t = P["sens_totals"]
L.append(f"| **Total** | **{f(P['total'])}** | " + " | ".join(f"**{f(t[k]['v30'])} / {f(t[k]['v90'])}**" for k in ("low", "base", "high")) + " |")
L += ["", "### Considered and not funded", ""]
for r in P["rejected"]:
    L.append(f"- **{r['what']}** ({r['id']}, {r['cost']}): {r['why']}")
L += ["", "## Model validation", "",
      f"- Freeze date {d['model']['freeze']}: trained on Jan–Apr, tested on May–Jun (61 unseen days). Inputs: weekday, and events announced by the freeze date.",
      f"- MAE: constant mean {f(d['model']['metrics']['pred_base']['mae'])}/day; weekday mean {f(d['model']['metrics']['pred_wd']['mae'])}; weekday + known events {f(d['model']['metrics']['pred_wd_ev']['mae'])} (chosen).",
      f"- July baseline (refit on Jan–Jun, frozen before July): {f(d['model']['july']['total'])} floor coin-in, 90% daily error band ±{f(d['model']['july']['q90_abs_err_day'])}. Used as the counterfactual when measuring the actions.", "",
      "## AI-use disclosure", "",
      "- **Claude (Anthropic)** was used to explore the data, write the analysis pipeline (DuckDB/pandas), build the single-file HTML dashboard, and draft this appendix, the write-up, the Devpost text and the video script.",
      "- All numbers come from the pipeline in `pipeline/` run on the official challenge data. I reviewed the method choices (luck z-score, peer and location indices, time-based model holdout, action pricing) and the conclusions.",
      "- No AI-generated data was used. Real outside data is limited to the public files shipped in the challenge repo (LVCVA, NOAA weather, Missouri Gaming Commission)."]
open(out, "w").write("\n".join(L) + "\n")
print("appendix lines", len(L))
