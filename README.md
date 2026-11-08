# The Gilded Ace — Luck, Location, or a Leak?

Dashboard Royale submission for TAMU Datathon 2026. The casino is fictional and all of its data is synthetic.

**Open the dashboard:** `build/index.html` is one self-contained file. Open it in any modern browser (Chrome, Edge, Firefox, Safari). It needs no server, no internet and no install. For a public link, put `index.html` on GitHub Pages.

## What judges can do in the dashboard

| Judge task | Where |
|---|---|
| Change the analysis period | **Analysis period** selectors in the header. They apply to Overview, Machines, Demand, Downtime, Players and Comps. The selection is kept in the URL, so any view can be shared. |
| Drill into one bank or guest group | **Machines** / **Downtime** have zone and bank selectors, and you can click a bank on the floor map. **Players** has a guest-group selector (region, age band, tier). |
| See how the model was validated | **Model** page: frozen Apr 30, trained Jan–Apr, tested May–Jun, MAE vs. a constant-mean baseline. |
| Trace a recommendation to its evidence | **$100K plan**: each action has a "Trace to evidence" link, and the **Claims & evidence** page lists the query, result, alternative tested and limitation. |

## Rebuild from the data

```sh
git clone --depth 1 https://github.com/tamu-datathon-org/dashboard-royale.git
python3 -m pip install -r requirements.txt   # Python 3.11+
./run.sh ./dashboard-royale                  # writes build/index.html
```

| Step | File | Does |
|---|---|---|
| 1 | `pipeline/01_machine_day.py` | Joins active machine-days with meters and game math; computes the per-machine luck σ |
| 2 | `pipeline/02_model.py` | Daily coin-in forecast with a time-based holdout (freeze 2025-04-30) |
| 3 | `pipeline/03_build_data.py` | Pre-aggregates everything the dashboard needs into `data.json` (about 0.5 MB) |
| 4 | `pipeline/04_classify.py` | Reference machine diagnosis, mirrored in the dashboard's JavaScript |
| 5 | `pipeline/05_plan.py` | Prices the $100K actions (catalogue lead-day formula) and writes the claims table |
| 6 | `pipeline/06_assemble.py` | Embeds `data.json` into `pipeline/template.html` → `build/index.html` |
| 7 | `pipeline/07_docs.py` | Regenerates `APPENDIX.md` from the same data |

## Key definitions

- **Hold** = Σ house win ÷ Σ coin-in (a ratio of sums).
- **Theo** = Σ bet × (1 − RTP).
- **Luck z** = (house win − theo) ÷ √(Σbet² × payout variance).
- **Peer index** = a machine's theo per available hour ÷ the same game's rate in the same zone (leave-one-out).
- **Location index** = the same game's rate in this zone ÷ its floor-wide rate.
- The 1,018 off-floor rows are excluded. Availability uses `scheduled_seconds`, which handles the DST day.

## Files

- `WRITEUP.md` — the 400-word write-up
- `APPENDIX.md` — the Claims & Evidence appendix, priced actions, and the AI-use disclosure
- `VIDEO_SCRIPT.md` — the 2-minute walkthrough script