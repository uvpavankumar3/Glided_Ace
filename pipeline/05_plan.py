"""Computes the $100K plan figures and the Claims & Evidence list; merges them into data.json."""
import json, sys, pandas as pd, numpy as np
P = sys.argv[1]
d = json.load(open(P))
md = pd.read_parquet("build/md.parquet")
cl = pd.read_pickle("build/class.pkl")
days = pd.DataFrame(d["days"]); days["d"] = pd.to_datetime(days.d)
A = {a["id"]: a for a in d["actions"]}
fmt0 = lambda v: f"${v:,.0f}"
def cost(aid, q):
    a = A[aid]; return q * (a["unit_cost"] + a["daily"] * max(0, 30 - a["lead"]))
# --- Back Forty natural experiment ---
def zstats(a, b):
    x = md[(md.gaming_date >= a) & (md.gaming_date < b) & (md.bank_id != "B-51")]; n = x.gaming_date.nunique()
    b40 = x[x.zone_name == "Back Forty"]; o = x[x.zone_name != "Back Forty"]
    return {"days": int(n), "b40_theo_day": b40.theo_usd.sum() / n, "other_theo_day": o.theo_usd.sum() / n,
            "b40_rate": b40.theo_usd.sum() / b40.available_hours.sum(), "other_rate": o.theo_usd.sum() / o.available_hours.sum()}
pre, clo, post = zstats("2025-02-03", "2025-03-03"), zstats("2025-03-03", "2025-04-07"), zstats("2025-04-07", "2025-05-05")
b40_base = md[(md.gaming_date >= "2025-04-07") & (md.zone_name == "Back Forty")]
b40_day = b40_base.theo_usd.sum() / b40_base.gaming_date.nunique()
eff_days_way = 30 - A["A-WAYFINDING"]["lead"]
way_cost = cost("A-WAYFINDING", 1)
way = {"cost": way_cost, "eff_days": eff_days_way, "b40_theo_day": b40_day, "breakeven_lift": way_cost / (b40_day * eff_days_way),
       "scen": {f"{int(l*100)}%": l * b40_day * eff_days_way for l in (0, 0.03, 0.08)}, "pre": pre, "closure": clo, "post": post,
       "closure_drop": clo["b40_theo_day"] / pre["b40_theo_day"] - 1, "others_change": clo["other_theo_day"] / pre["other_theo_day"] - 1}
# --- M-1158 inspection ---
r = cl[cl.id == "M-1158"].iloc[0]
x = md[md.machine_id == "M-1158"]
insp_cost = cost("A-INSPECT", 1)
excess_day = -(x.house_win_usd.sum() - x.theo_usd.sum()) / len(x)
insp = {"cost": insp_cost, "hit": r.pp / r.sp, "hit_cfg": r.hitp, "hit_z": r.hit_z, "luck": r.luck, "luck_z": r.z, "excess_day": excess_day,
        "eff_days": 30 - A["A-INSPECT"]["lead"], "value_if_fixed": excess_day * (30 - A["A-INSPECT"]["lead"]), "spins_month": r.sp / 6}
# --- comp pilot ---
pg = pd.DataFrame(d["pgrp"], columns=["mo","rg","ag","tr","n","ci","po","net","theo","comp","face","nc","pe","pr","ahead","gam","pos","contrib"])
pg["per"] = np.where(pg.mo <= 3, "before", "after")
cp = pg.groupby("per").agg(comp=("comp","sum"), theo=("theo","sum"), n=("n","sum"), nc=("nc","sum"), pr=("pr","sum"), face=("face","sum"))
cp["months"] = [2, 4] if list(cp.index) == ["after", "before"] else [4, 2]
cp = cp.assign(reinv=cp.comp / cp.theo, comp_mo=cp.comp / cp.months, theo_mo=cp.theo / cp.months, pts_per_face=cp.pr / cp.face, nc_mo=cp.nc / cp.months)
cdl = pd.DataFrame(d["comp_daily"], columns=["d", "n", "pts", "face", "cost"])
ma = cdl[(cdl.d >= "2025-03-01") & (cdl.d < "2025-05-01")]; mj = cdl[cdl.d >= "2025-05-01"]
bal = pg.groupby("mo")[["pe", "pr"]].sum().cumsum(); balance = float(bal.pe.iloc[-1] - bal.pr.iloc[-1])
ppf_b, ppf_a = cp.loc["before", "pts_per_face"], cp.loc["after", "pts_per_face"]
comp = {"cost": cost("A-COMP-PILOT", 1), "before": cp.loc["before"].to_dict(), "after": cp.loc["after"].to_dict(),
        "extra_cost_mo": cp.loc["after", "comp_mo"] - cp.loc["before", "comp_mo"], "revert_cost": cost("A-COMP-CHANGE", 1),
        "cost_day_ma": ma.cost.sum() / ma.d.nunique(), "cost_day_mj": mj.cost.sum() / mj.d.nunique(),
        "n_day_ma": ma.n.sum() / ma.d.nunique(), "n_day_mj": mj.n.sum() / mj.d.nunique(),
        "balance_pts": balance, "balance_face_old": balance / ppf_b, "balance_face_new": balance / ppf_a}
comp["cost_chg"] = comp["cost_day_mj"] / comp["cost_day_ma"] - 1; comp["n_chg"] = comp["n_day_mj"] / comp["n_day_ma"] - 1
# --- rejected options ---
fl = pd.DataFrame(d["faults"], columns=["gd","h","wait","dur","cost","mfr","mid"])
floor_rate = md.theo_usd.sum() / md.available_hours.sum()
wait_lost_day = fl.wait.sum() * floor_rate / 181
rid = fl[fl.mfr == "Ridgeline"]
lt = pd.DataFrame(d["mm"], columns=["mi","mo","zi","bi","ti","days","ci","hw","theo","lv","ah","sh","oh","f","dh","lt","co","sp","pp","rs","rss","rn"])
mfr_of = {i: m[1] for i, m in enumerate(d["machines"])}
lt["mfr"] = lt.mi.map(mfr_of)
rid_month = (rid.cost.sum() + lt[lt.mfr == "Ridgeline"]["lt"].sum()) / 6
pm_cost = cost("A-PREVENTIVE", 1); pm_days = 30 - A["A-PREVENTIVE"]["lead"]
n_rid = int((pd.DataFrame(d["machines"])[1] == "Ridgeline").sum())
pm_downtime_cost = 1.5 * 94 * floor_rate
model = d["model"]
dd = pd.DataFrame(model["daily"])
tour = dd[dd.event == "Gilded Ace Winter Slot Tournament"]
loc = dd[dd.event == "Gilded Ace Locals Appreciation Week"]
hold = days.hw.sum() / days.ci.sum()
b10 = cl.sort_values("hw").head(10)
rejected = [
    {"id": "A-REPLACE-LEASE / A-REPLACE-BUY", "what": "Replace the manager's bottom 10",
     "cost": f"${cost('A-REPLACE-LEASE',10):,.0f} leased (16 operating days) or ${cost('A-REPLACE-BUY',10):,.0f} purchased (over budget)",
     "why": "None of the 8 bottom-10 machines still on the floor is weak against same-game peers. Two were already retired and replaced (M-1118, M-1120). The slot where M-1120 sat was refilled with the same title (M-5076) and still ranks last, so the slot is the problem, not the cabinet. Adding bank B-51 (+$%s/day of theo in that bank) did not raise floor theo, so new machines mostly take play from neighbours." % f"{5434:,.0f}"},
    {"id": "A-TECH-SHIFT", "what": "Add a technician to a shift", "cost": f"${cost('A-TECH-SHIFT',1):,.0f}",
     "why": f"All fault waiting time over six months cost about ${wait_lost_day*30:,.0f} of theo per 30 days at the floor rate. Even eliminating waits entirely would not repay one technician. The April-May wait spike came from unfilled roster slots, not a structural shortage: fill planned shifts instead."},
    {"id": "A-PREVENTIVE", "what": "Preventive maintenance, Ridgeline (runner-up)", "cost": f"${pm_cost:,.0f}",
     "why": f"Ridgeline has {n_rid} machines (30%) but {len(rid)} of {len(fl)} faults. Faults plus lost theo cost about ${rid_month:,.0f}/month. After the 7-day lead and about ${pm_downtime_cost:,.0f} of sweep downtime, it needs roughly a {(pm_cost+pm_downtime_cost)/(rid_month*pm_days/30):.0%} fault reduction inside 23 days to break even. No data shows what a sweep achieves, so it's runner-up. Fund it if the vendor can show a fault-reduction record."},
    {"id": "A-PROMO", "what": "Promotion weekend (runner-up)", "cost": f"${cost('A-PROMO',1):,.0f}",
     "why": f"The February slot tournament ran about {tour.ci.sum()/tour.pred_wd.sum()-1:.0%} above the weekday model. The week-long Locals event was followed by below-model weeks. One success and one mixed result is too thin to bet $15k on, and promotions must avoid targeting heavy losers."},
]
plan = {"actions": [
    {"id": "A-INSPECT", "name": "Inspect & verify paytable of M-1158", "qty": 1, "target": "M-1158 (Back Forty, B-31, Desert Gold)", "cost": insp_cost,
     "why": f"Its hit rate is {insp['hit']:.1%} against a configured {insp['hit_cfg']:.1%} (z = {insp['hit_z']:.0f}) over {r.sp:,.0f} spins, and house win is ${-insp['luck']:,.0f} below theo (luck z = {insp['luck_z']:.1f}). No other machine has |hit z| above 3. That pattern points to the machine paying differently from its published math (a configuration lead), not bad luck.",
     "effect": f"If the configuration is corrected, house win returns to theo: about ${excess_day:,.0f}/day, or ${insp['value_if_fixed']:,.0f} over the 29 days after the 1-day lead.",
     "uncertainty": "The inspection produces information, not a guaranteed finding. It is a lead to inspect, not proof of wrongdoing or of a fault.",
     "measure": f"Re-measure hit rate over the next ~{insp['spins_month']:,.0f} spins (one month). The standard error is about 0.14 pp, so a return to {insp['hit_cfg']:.1%} ±0.3 pp settles it. Also track luck z for the month.",
     "evidence": "machines"},
    {"id": "A-WAYFINDING", "name": "Wayfinding & signage refresh: Back Forty", "qty": 1, "target": "Zone Back Forty (Z-B40)", "cost": way_cost,
     "why": f"The same games earn {1-cl[cl.zone=='Back Forty'].loc_idx.median():.0%} less per available hour in Back Forty than on the floor average. When the Main Entrance to Back Forty walkway closed (Mar 3–Apr 7), Back Forty theo fell {-way['closure_drop']:.0%} while the rest of the floor changed {way['others_change']:+.1%}. The lost play was not recaptured elsewhere, so access and visibility drive this zone.",
     "effect": f"Break-even is a {way['breakeven_lift']:.1%} lift on ${b40_day:,.0f}/day of Back Forty theo over {eff_days_way} effective days. Scenarios: 0% → $0; 3% → ${way['scen']['3%']:,.0f}; 8% → ${way['scen']['8%']:,.0f}.",
     "uncertainty": "There's no direct signage history, and the closure shows access matters, not that signs fix it. The comparison periods differ in their events.",
     "measure": f"Difference-in-differences: Back Forty theo per available hour vs. other zones, 20 days after vs. 28 days before. The frozen July forecast (${model['july']['total']/1e6:,.1f}M floor coin-in, ±${model['july']['q90_abs_err_day']/1e3:,.0f}k/day 90% error band) checks that any Back Forty lift isn't just a floor-wide swing. Also coverage-adjusted Back Forty entry counts. Freeze the metric before launch.",
     "evidence": "demand"},
    {"id": "A-COMP-PILOT", "name": "Comp-rate pilot with control group", "qty": 1, "target": "Tracked players, randomised 50/50", "cost": comp["cost"],
     "why": f"On May 1 the points price of a comp fell from {ppf_b:.1f} to {ppf_a:.1f} points per comp dollar. Compared with Mar–Apr, redemptions per day rose only {comp['n_chg']:+.0%} and comp cost per day {comp['cost_chg']:+.0%}, within the drift that was already there. Tracked theo per month stayed flat (${comp['before']['theo_mo']:,.0f} vs ${comp['after']['theo_mo']:,.0f}). Meanwhile the {comp['balance_pts']/1e6:,.0f}M unredeemed points are now worth about ${comp['balance_face_new']/1e6:,.0f}M in comps at menu price, up from ${comp['balance_face_old']/1e6:,.0f}M at the old rate. The change has no measured return and doubles the comp liability.",
     "effect": f"Information first. If the control arm (old rate) shows equal theo and visits, revert floor-wide ({fmt0(comp['revert_cost'])}) next month. That halves the comp value of the outstanding points again. Comp costs during the pilot still flow through POS cogs.",
     "uncertainty": "Two post-change months, seasonality, and a 30-day pilot may be too short to detect small visit effects. Pre-register a minimum detectable effect.",
     "measure": "Per-member theo, visits, comp cost and redemption rate, treatment vs. control, with a pre-registered primary metric (theo per member). Randomisation removes seasonality; the July forecast flags any floor-wide shock during the pilot. The pilot cannot be combined with a floor-wide comp change.",
     "evidence": "comps"}],
    "rejected": rejected, "budget": 100000}
plan["total"] = sum(a["cost"] for a in plan["actions"]); plan["kept"] = 100000 - plan["total"]
# ---- sensitivity: theo-equivalent value, 30-day horizon and 90 days if the effect persists ----
wd_ = way["b40_theo_day"]; ins_d = insp["excess_day"]
sens = [
 {"action": "Inspect M-1158", "cost": insp_cost, "low": ("Nothing found", 0, 0),
  "base": ("50% chance it's a configuration fault, fixed on day 2", 0.5 * ins_d * 29, 0.5 * ins_d * 89),
  "high": ("Fault confirmed and fixed on day 2", ins_d * 29, ins_d * 89)},
 {"action": "Back Forty wayfinding", "cost": way_cost, "low": ("No lift", 0, 0),
  "base": ("3% lift on Back Forty theo", 0.03 * wd_ * 20, 0.03 * wd_ * 80),
  "high": ("8% lift (a quarter of the closure drop)", 0.08 * wd_ * 20, 0.08 * wd_ * 80)},
 {"action": "Comp-rate pilot", "cost": comp["cost"], "low": ("Old rate loses play: keep new rate", 0, 0),
  "base": ("No difference: revert in August", 0, 0),
  "high": ("No difference: revert; cost/day back to Mar–Apr level", 0, (comp["cost_day_mj"] - comp["cost_day_ma"]) * 60)},
]
for r in sens:
    for k in ("low", "base", "high"):
        lab, v30, v90 = r[k]; r[k] = {"label": lab, "v30": v30, "v90": v90}
plan["sensitivity"] = sens
plan["sens_totals"] = {k: {"v30": sum(r[k]["v30"] for r in sens), "v90": sum(r[k]["v90"] for r in sens)} for k in ("low", "base", "high")}
fmt = lambda v: ("−" if v < 0 else "") + f"${abs(v):,.0f}"
# weather and contribution robustness
import duckdb as _dd
_wx = pd.DataFrame(d["weather"], columns=["d", "t", "p"]); _md = pd.DataFrame(model["daily"]); _md = _md.merge(_wx, left_on="gaming_date", right_on="d")
_md["res"] = _md.ci / _md.pred_wd - 1
wxc = _md.res.corr(_md.t); wx_rain_n = int((_md.p > 0.5).sum()); wx_rain = _md[_md.p > 0.5].res.mean(); wx_dry = _md[_md.p <= 0.5].res.mean()
_cg = md.groupby("machine_id").agg(hw=("house_win_usd", "sum"), co=("contribution_after_supplied_costs_usd", "sum"))
contrib_overlap = len(set(_cg.co.nsmallest(10).index) & set(_cg.hw.nsmallest(10).index)); neg_contrib = int((_cg.co < 0).sum())
claims = [
 {"id": "C1", "claim": "The manager's bottom 10 are not weak machines: 9 of 10 sit in Back Forty, 2 were already retired in-window, and 1 is a payout anomaly.", "page": "machines",
  "query": "prepared_daily_view (active) ⋈ machine_day ⋈ game_math → per machine: SUM(house_win), SUM(theo), luck z = (win−theo)/√Σ(bet²·var), peer index vs same theme+zone (leave-one-out)",
  "result": f"0 of 8 remaining machines below 0.90 of same-game peers; bottom-10 luck = {fmt(b10.luck.sum())} on {fmt(b10.theo.sum())} theo", "alt": "Bad luck: tested with volatility-based z; only M-1158 (z −4.6) is beyond chance. Location: tested with location index (zone/theme vs floor/theme ≈ 0.65 for Back Forty).", "limit": "Peer groups are small (2–12 machines); position within a bank isn't modelled."},
 {"id": "C2", "claim": f"Back Forty earns ~{1-cl[cl.zone=='Back Forty'].loc_idx.median():.0%} less per available hour on identical games; the walkway closure cut it {-way['closure_drop']:.0%} with no recapture elsewhere.", "page": "demand",
  "query": "theo / available_hours by zone, 4 weeks before / during (Mar 3–Apr 7) / 4 weeks after the W-ENT-B40 closure, excl. new bank B-51", "result": f"B40 {fmt(pre['b40_theo_day'])} → {fmt(clo['b40_theo_day'])} → {fmt(post['b40_theo_day'])}/day; rest of floor {fmt(pre['other_theo_day'])} → {fmt(clo['other_theo_day'])}", "alt": "Seasonality: other zones flat during closure, B40 recovered within a week of reopening.", "limit": "Periods contain different events (Super Bowl vs basketball/conventions)."},
 {"id": "C3", "claim": f"M-1158 pays out more often than its configuration: hit rate {insp['hit']:.1%} vs {insp['hit_cfg']:.1%}.", "page": "machines",
  "query": "SUM(payout_positive_spins)/SUM(paid_spins) vs game_math.hit_probability; binomial z", "result": f"z = {insp['hit_z']:.0f}; house win {fmt(-insp['luck'])} below theo", "alt": "Luck: a binomial z of 124 is not chance; next-largest |z| on the floor is < 3.", "limit": "A lead to inspect, not proof of a fault or wrongdoing."},
 {"id": "C4", "claim": "Adding machines redistributes play: bank B-51 (Mar 24) took ~$5.4k/day of theo but floor theo did not rise.", "page": "demand",
  "query": "Zone theo/day, Feb 24–Mar 23 vs Apr 7–May 4", "result": "Floor $132.2k → $131.2k/day; B-51 $5.4k/day; Center Pit ex-B51 $36.8k → $34.5k", "alt": "Seasonal decline masking a gain: possible; April LVCVA visitors were down 5% YoY.", "limit": "One install event; confounded with B40 reopening."},
 {"id": "C5", "claim": f"Downtime cost ~{fmt(lt["lt"].sum())} of theo (≈{lt["lt"].sum()/days.theo.sum():.2%} of theo); Ridgeline (30% of machines) caused {len(rid)/len(fl):.0%} of faults.", "page": "downtime",
  "query": "Σ(scheduled − available hours) × machine-month theo per available hour; operations fault_repair by manufacturer", "result": f"{lt.dh.sum():,.0f} machine-hours down; Ridgeline {len(rid)} of {len(fl)} faults", "alt": "Ridgeline machines played more (more spins → more faults)? Ridgeline theo/hour is not above floor average.", "limit": "Lost theo assumes the machine would have played at its own monthly rate."},
 {"id": "C6", "claim": "Fault waits doubled when day/swing technician slots went unfilled (Apr 14–May 25).", "page": "downtime",
  "query": "shift_roster slot_tech actual < planned; operations wait = work_started − opened", "result": f"avg wait {fl[(fl.gd<'2025-04-14')|(fl.gd>'2025-05-31')].wait.mean():.2f} h outside vs {fl[(fl.gd>='2025-04-14')&(fl.gd<='2025-05-31')].wait.mean():.2f} h inside the gap window", "alt": "More faults in the window? Fault counts were lower in Apr–May.", "limit": "Grave-shift (1 tech) waits are long all year; not caused by the gap."},
 {"id": "C7", "claim": "Tracked player results are concentrated: top 10% of players account for ~56% of net losses; 16% finished ahead.", "page": "players",
  "query": "player_period summed per player (coin-in > 0); sorted net losses", "result": f"Top 1% {d['concentration']['All tracked players']['top_loss'][ '1']:.1%}, top 10% {d['concentration']['All tracked players']['top_loss']['10']:.1%}; ahead {d['concentration']['All tracked players']['ahead']:.1%}", "alt": "Concentration is just play volume? Theo concentration is similar (top 10% = 64% of theo), so losses track exposure, not unusual luck.", "limit": "Carded play only (~66% of coin-in); uncarded guests invisible."},
 {"id": "C8", "claim": f"The May 1 comp-rate cut halved the points price of comps but moved redemptions only {comp['n_chg']:+.0%} and comp cost {comp['cost_chg']:+.0%} (vs Mar–Apr), with flat tracked theo and visits. It roughly doubled the comp value of unredeemed points.", "page": "comps",
  "query": "loyalty_ledger redeem: points ÷ face value per day; redemptions & economic cost per day; player_period Σpoints earned − redeemed", "result": f"{ppf_b:.1f} → {ppf_a:.1f} pts per comp $; {comp['balance_pts']/1e6:,.0f}M points outstanding ≈ ${comp['balance_face_old']/1e6:,.0f}M → ${comp['balance_face_new']/1e6:,.0f}M menu value", "alt": "Demand would have fallen without it (June LVCVA visitors −11% YoY)? Can't rule out → randomised pilot.", "limit": "Only 2 post-change months; not randomised; points balance resets each year."},
 {"id": "C9", "claim": f"A weekday model forecasts daily coin-in with {model['metrics']['pred_wd']['mape']:.1%} error (MAE {fmt(model['metrics']['pred_wd']['mae'])}) vs {model['metrics']['pred_base']['mape']:.1%} for a constant mean.", "page": "model",
  "query": "Train Jan–Apr (freeze Apr 30), test May–Jun; events used only if announced by the freeze date", "result": f"Weekday+events MAE {fmt(model['metrics']['pred_wd_ev']['mae'])}", "alt": "Trend model? Test bias is small (+$10k/day weekday model) so trend adds little.", "limit": "Locals Week was announced after the freeze and is excluded; only 2 test months."},
 {"id": "C11", "claim": "Weather does not explain demand: daily coin-in residuals don't track temperature.", "page": "demand",
  "query": "weekday-model residual (actual ÷ weekday mean − 1) vs NOAA daily max temperature and rain (Las Vegas airport, real data)", "result": f"corr(residual, tmax) = {wxc:.2f}; {wx_rain_n} rain days averaged {wx_rain:+.1%} vs {wx_dry:+.1%} on dry days", "alt": "This is itself the alternative tested for the Feb–Jun softening.", "limit": "Only 5 rain days; calendar dates vs gaming dates differ for 6 hours."},
 {"id": "C12", "claim": "The bottom 10 is the same when ranked by contribution after supplied costs (leases, service, power, repairs).", "page": "machines",
  "query": "prepared_daily_view: SUM(contribution_after_supplied_costs_usd) per machine, active days", "result": f"{contrib_overlap} of 10 machines overlap; {neg_contrib} machines have negative contribution", "alt": "Leased machines' fees could change the ranking; they don't, materially.", "limit": "Supplied costs are partial (no rent, tax, depreciation, full staffing)."},
 {"id": "C10", "claim": f"Our observed hold ({hold:.2%}) is in line with real Missouri slot hold (~9.6%).", "page": "demand",
  "query": "property_day Σhouse win/Σcoin-in vs benchmark_state_monthly Σagr/Σhandle", "result": "Monthly hold 9.36–9.83% vs Missouri 9.48–9.71%", "alt": "Different market mix; benchmark is context only, not a target.", "limit": "Missouri is a different, regional market."},
]
claims.sort(key=lambda c: int(c["id"][1:]))
d["plan"] = plan; d["claims"] = claims
d["insight"] = {"way": way, "insp": insp, "comp": comp, "wait_lost_30d": wait_lost_day * 30, "rid_month": rid_month, "floor_rate": floor_rate,
                "bottom10": b10[["id", "zone", "bank", "theme", "hw", "theo", "z", "peer_idx", "loc_idx", "tags", "verdict"]].to_dict("records")}
s = json.dumps(d, separators=(",", ":"), default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else (o.tolist() if isinstance(o, np.ndarray) else str(o)))
open(P, "w").write(s.replace("NaN", "null"))
print(json.dumps({"plan_total": plan["total"], "kept": plan["kept"], "way": {k: way[k] for k in ("breakeven_lift", "b40_theo_day", "closure_drop", "others_change")}, "comp_extra": comp["extra_cost_mo"], "insp_value": insp["value_if_fixed"], "wait30": wait_lost_day * 30, "rid_month": rid_month}, default=float, indent=1))
for r_ in rejected: print(r_["why"][:220])
for c in claims: print(c["id"], c["result"])
