"""Daily floor coin-in forecast. Freeze date 2025-04-30: train Jan-Apr, test May-Jun.
Only inputs known at the freeze: weekday, and events whose announced_date <= freeze."""
import duckdb, sys, json, pandas as pd, numpy as np
D = sys.argv[1]
con = duckdb.connect(); con.execute(f"SET file_search_path='{D}'")
pdy = con.sql("SELECT gaming_date, local_weekday, coin_in_usd::DOUBLE ci FROM 'data/1_prepared_views/property_day.parquet' ORDER BY 1").df()
ev = con.sql("SELECT event_id, name, event_type, start_date, end_date, announced_date FROM 'data/4_context/events.parquet'").df()
FREEZE = pd.Timestamp("2025-04-30")
known = ev[pd.to_datetime(ev.announced_date) <= FREEZE]
unknown = ev[pd.to_datetime(ev.announced_date) > FREEZE]
pdy["event"] = None; pdy["etype"] = None
for _, e in ev.iterrows():
    m = (pdy.gaming_date >= pd.Timestamp(e.start_date)) & (pdy.gaming_date <= pd.Timestamp(e.end_date))
    pdy.loc[m, "event"] = e["name"]; pdy.loc[m, "etype"] = {"sports_viewing":"leisure_weekend","festival":"leisure_weekend"}.get(e.event_type, e.event_type)
    pdy.loc[m, "event_known"] = pd.Timestamp(e.announced_date) <= FREEZE
train = pdy[pdy.gaming_date <= FREEZE].copy(); test = pdy[pdy.gaming_date > FREEZE].copy()
# baseline: constant training mean
base = train.ci.mean()
# model A: weekday mean (training days without events, so events don't inflate weekday levels)
tr_clean = train[train.event.isna()]
wd = tr_clean.groupby("local_weekday").ci.mean()
# model B: weekday mean x event-type multiplier from training residuals (sports/festival/promo vs convention)
train["wdpred"] = train.local_weekday.map(wd)
mult = (train[train.event.notna()].assign(r=lambda x: x.ci / x.wdpred).groupby("etype").r.mean())
def predB(r):
    p = wd[r.local_weekday]
    if r.event is not None and r.get("event_known", False) and r.etype in mult.index:
        p *= mult[r.etype]
    return p
for d in (train, test):
    d["pred_base"] = base
    d["pred_wd"] = d.local_weekday.map(wd)
    d["pred_wd_ev"] = d.apply(predB, axis=1)
def mae(d, c): return float((d.ci - d[c]).abs().mean())
def mape(d, c): return float(((d.ci - d[c]).abs() / d.ci).mean())
bias = {c: float((test[c]-test.ci).mean()) for c in ["pred_base","pred_wd","pred_wd_ev"]}; print("bias", bias)
res = {c: {"mae": mae(test, c), "mape": mape(test, c), "train_mae": mae(train, c)} for c in ["pred_base", "pred_wd", "pred_wd_ev"]}
print(json.dumps(res, indent=1)); print(wd.round(0).to_dict()); print(mult.round(3).to_dict())
print("unknown at freeze:", unknown.name.tolist())
# residual analysis per event (full window, weekday-only model) to estimate promo uplift
pdy["wdpred"] = pdy.local_weekday.map(wd)
pdy["resid"] = pdy.ci - pdy.wdpred
print(pdy[pdy.event.notna()].groupby("event").agg(days=("ci", "size"), ci=("ci", "mean"), resid=("resid", "mean"), ratio=("resid", lambda r: 0)).round(0))
# check pull-forward: week before / after tournament
for e in ["Gilded Ace Winter Slot Tournament", "Gilded Ace Locals Appreciation Week", "Super Bowl LIX weekend", "EDC Las Vegas festival weekend"]:
    r = ev[ev.name == e].iloc[0]; s, t = pd.Timestamp(r.start_date), pd.Timestamp(r.end_date)
    w = lambda a, b: pdy[(pdy.gaming_date >= a) & (pdy.gaming_date <= b)].resid.sum()
    print(e, "event resid", round(w(s, t)), "7d before", round(w(s - pd.Timedelta(days=7), s - pd.Timedelta(days=1))), "7d after", round(w(t + pd.Timedelta(days=1), t + pd.Timedelta(days=7))))
out = pd.concat([train.assign(split="train"), test.assign(split="test")])
out["gaming_date"] = out.gaming_date.dt.strftime("%Y-%m-%d")
# July 2025 baseline for measuring the actions: same method refit on all Jan-Jun non-event days (no July events known).
full_wd = pdy[pdy.event.isna()].groupby("local_weekday").ci.mean()
jul = pd.DataFrame({"gaming_date": pd.date_range("2025-07-01", "2025-07-30")})
jul["local_weekday"] = jul.gaming_date.dt.strftime("%a"); jul["pred"] = jul.local_weekday.map(full_wd)
abs_err = (test.ci - test.pred_wd_ev).abs()
q90 = float(abs_err.quantile(0.9))
july = {"total": float(jul.pred.sum()), "q90_abs_err_day": q90, "daily": [[d.strftime("%Y-%m-%d"), w, float(p)] for d, w, p in zip(jul.gaming_date, jul.local_weekday, jul.pred)]}
print("July baseline total", round(july["total"]), "q90 abs err/day", round(q90))
json.dump({"july": july, "metrics": res, "weekday_means": wd.to_dict(), "event_multipliers": mult.to_dict(), "freeze": "2025-04-30",
           "unknown_events": unknown.name.tolist(),
           "daily": out[["gaming_date", "local_weekday", "ci", "pred_base", "pred_wd", "pred_wd_ev", "split", "event"]].to_dict("records")},
          open("build/model.json", "w"), default=float)
