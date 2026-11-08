"""Builds data.json for the dashboard. Every number shown in the dashboard comes from here."""
import duckdb, sys, json, pandas as pd, numpy as np
D = sys.argv[1]; OUT = sys.argv[2]
con = duckdb.connect(); con.execute(f"SET file_search_path='{D}'")
Q = lambda s: con.sql(s).df()
R = lambda x, n=2: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)

# ---------- machine-day base (active rows only; off-floor rows excluded) ----------
md = Q("""
SELECT d.machine_id, d.gaming_date, d.month, d.zone_name, d.bank_id, d.theme, d.config_id, d.volatility_class, d.manufacturer, d.lease_class,
       d.configured_rtp::DOUBLE rtp, d.available_hours, d.occupied_hours, d.coin_in_usd::DOUBLE ci, d.house_win_usd::DOUBLE hw,
       d.theo_usd::DOUBLE theo, d.faults_opened, d.contribution_after_supplied_costs_usd::DOUBLE contrib,
       m.scheduled_seconds/3600.0 sched_h, m.paid_spins sp, m.payout_positive_spins pp,
       m.sum_bet_squared * g.payout_multiplier_variance::DOUBLE / 1e4 luck_var, g.hit_probability::DOUBLE hitp
FROM 'data/1_prepared_views/prepared_daily_view.parquet' d
JOIN 'data/2_machine_decision/machine_day.parquet' m USING (machine_id, gaming_date)
JOIN 'data/2_machine_decision/game_math.parquet' g ON g.config_id = d.config_id
WHERE d.active""")
md["down_h"] = md.sched_h - md.available_hours
rate = md.groupby(["machine_id", "month"]).apply(lambda x: x.theo.sum() / x.available_hours.sum() if x.available_hours.sum() > 0 else 0).rename("r")
md = md.join(rate, on=["machine_id", "month"])
md["lost_theo"] = md.down_h * md.r
# daily play rate (theo per available hour) for the peer-index uncertainty band
md["dr"] = np.where(md.available_hours > 0, md.theo / md.available_hours.where(md.available_hours > 0, 1), np.nan)
md["dr2"] = md.dr ** 2; md["drn"] = md.dr.notna().astype(int)

months = sorted(md.month.unique())
zones = sorted(md.zone_name.unique()); banks = sorted(md.bank_id.unique()); themes = sorted(md.theme.unique())
mids = sorted(md.machine_id.unique())
mm = md.groupby(["machine_id", "month", "zone_name", "bank_id", "theme"]).agg(
    days=("gaming_date", "count"), ci=("ci", "sum"), hw=("hw", "sum"), theo=("theo", "sum"), lv=("luck_var", "sum"),
    ah=("available_hours", "sum"), sh=("sched_h", "sum"), oh=("occupied_hours", "sum"), f=("faults_opened", "sum"),
    dh=("down_h", "sum"), lt=("lost_theo", "sum"), co=("contrib", "sum"), sp=("sp", "sum"), pp=("pp", "sum"),
    rs=("dr", "sum"), rss=("dr2", "sum"), rn=("drn", "sum")).reset_index()
mm_rows = [[mids.index(r.machine_id), months.index(r.month), zones.index(r.zone_name), banks.index(r.bank_id), themes.index(r.theme), int(r.days),
            R(r.ci, 0), R(r.hw, 0), R(r.theo, 0), R(r.lv, 0), R(r.ah, 1), R(r.sh, 1), R(r.oh, 1), int(r.f), R(r.dh, 2), R(r.lt, 0), R(r.co, 0), int(r.sp), int(r.pp), R(r.rs, 3), R(r.rss, 2), int(r.rn)]
           for r in mm.itertuples()]
mach = md.sort_values("gaming_date").groupby("machine_id").agg(vol=("volatility_class", "last"), mfr=("manufacturer", "first"), lease=("lease_class", "first"),
                                                                   rtp=("rtp", "last"), hitp=("hitp", "last"), theme=("theme", "last"))
machines = [[m, mach.loc[m, "mfr"], mach.loc[m, "vol"], mach.loc[m, "lease"], R(mach.loc[m, "rtp"], 4), R(mach.loc[m, "hitp"], 6)] for m in mids]
period_days = {mo: int(md[md.month == mo].gaming_date.nunique()) for mo in months}

# ---------- property day ----------
pdy = Q("""SELECT p.*, c.scheduled_seconds FROM 'data/1_prepared_views/property_day.parquet' p JOIN 'data/2_machine_decision/calendar_day.parquet' c USING(gaming_date) ORDER BY gaming_date""")
lost_day = md.groupby("gaming_date").lost_theo.sum()
pdy = pdy.join(lost_day, on="gaming_date")
zone_day = md.groupby(["gaming_date", "zone_name"]).agg(theo=("theo", "sum"), ah=("available_hours", "sum"), oh=("occupied_hours", "sum")).reset_index()
zd = {z: {"theo": [], "ah": [], "oh": []} for z in zones}
for d in pdy.gaming_date:
    s = zone_day[zone_day.gaming_date == d].set_index("zone_name")
    for z in zones:
        for k in ("theo", "ah", "oh"):
            zd[z][k].append(R(s.loc[z, k], 0 if k == "theo" else 1) if z in s.index else 0)
days = [{"d": r.gaming_date.strftime("%Y-%m-%d"), "wd": r.local_weekday, "ci": R(r.coin_in_usd, 0), "hw": R(r.house_win_usd, 0), "theo": R(r.theo_usd, 0),
         "ah": R(r.available_machine_hours, 0), "oh": R(r.occupied_machine_hours, 0), "ent": None if pd.isna(r.total_zone_entries_observed) else int(r.total_zone_entries_observed),
         "cov": R(r.counter_coverage_share, 3), "pos": R(r.pos_cash_usd, 0), "cogs": R(r.pos_cogs_usd, 0), "comp": R(r.comp_cost_usd, 0), "f": int(r.faults_opened), "lt": R(r.lost_theo, 0),
         "ev": r.events_active if isinstance(r.events_active, str) else "", "card": R(r.carded_coin_in_share, 3), "contrib": R(r.contribution_after_supplied_costs_usd, 0),
         "inc": int(r.incidents_reported)} for r in pdy.itertuples()]

# zone traffic (coverage-adjusted entries per day, offline hours excluded)
zt = Q("""SELECT zone_id, CAST(hour_start_local - INTERVAL 6 HOUR AS DATE) gd, sum(entries_count) e, sum(coverage_minutes) cm
 FROM 'data/4_context/zone_traffic_hourly.parquet' WHERE counter_status <> 'offline' GROUP BY 1,2""")
zt["gd"] = pd.to_datetime(zt.gd); zt = zt[(zt.gd >= "2025-01-01") & (zt.gd <= "2025-06-30")]
zt["adj"] = zt.e / zt.cm * 1440
zmap = dict(Q("SELECT zone_id, name FROM 'data/2_machine_decision/floor_locations.parquet' WHERE node_type='zone'").values)
traffic = {zmap[z]: {d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d): R(v, 0) for d, v in zip(g.gd, g.adj)} for z, g in zt.groupby("zone_id")}

# ---------- downtime / operations ----------
ops = Q("""SELECT o.machine_id, o.event_type, o.opened_at_local, hour(o.opened_at_local) h, epoch(work_started_at_utc-opened_at_utc)/3600 wait_h,
 epoch(available_at_utc-opened_at_utc)/3600 dur_h, direct_cost_cents/100.0 cost, m.manufacturer
 FROM 'data/2_machine_decision/operations.parquet' o JOIN 'data/2_machine_decision/machines.parquet' m USING(machine_id) WHERE event_type='fault_repair'""")
ops["gd"] = (ops.opened_at_local - pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")
faults = [[r.gd, r.h, R(r.wait_h, 2), R(r.dur_h, 2), R(r.cost, 0), r.manufacturer, r.machine_id] for r in ops.itertuples()]
roster = Q("""SELECT strftime(gaming_date,'%Y-%m-%d') d, shift, sum(planned_headcount) p, sum(actual_headcount) a FROM 'data/5_optional/shift_roster.parquet' WHERE role='slot_tech' GROUP BY 1,2 ORDER BY 1,2""")
roster_rows = roster.values.tolist()

# ---------- players ----------
pp_ = Q("""SELECT period_month mo, home_region rg, coalesce(age_band,'Unknown') ag, opening_tier tr, count(*) n,
 sum(tracked_coin_in_usd)::DOUBLE ci, sum(tracked_payout_usd)::DOUBLE po, sum(tracked_net_usd)::DOUBLE net, sum(theo_usd)::DOUBLE theo,
 sum(comp_cost_usd)::DOUBLE comp, sum(comp_face_value_usd)::DOUBLE face, sum(comps_redeemed) nc, sum(points_earned) pe, sum(points_redeemed) pr,
 sum(CASE WHEN tracked_net_usd>0 THEN 1 ELSE 0 END) ahead, sum(CASE WHEN tracked_coin_in_usd>0 THEN 1 ELSE 0 END) gam,
 sum(linked_pos_cash_usd)::DOUBLE pos, sum(tracked_contribution_usd)::DOUBLE contrib
 FROM 'data/1_prepared_views/player_period.parquet' GROUP BY 1,2,3,4""")
regions = sorted(pp_.rg.unique()); ages = sorted(pp_.ag.unique()); tiers = ["Base", "Gold", "Platinum"]
pgrp = [[months.index(r.mo), regions.index(r.rg), ages.index(r.ag), tiers.index(r.tr), int(r.n), R(r.ci, 0), R(r.po, 0), R(r.net, 0), R(r.theo, 0), R(r.comp, 0),
         R(r.face, 0), int(r.nc), int(r.pe), int(r.pr), int(r.ahead), int(r.gam), R(r.pos, 0), R(r.contrib, 0)] for r in pp_.itertuples()]
# concentration over the full window (player level), per segment
pl = Q("""SELECT player_id, any_value(home_region) rg, coalesce(any_value(age_band),'Unknown') ag, any_value(opening_tier) tr,
 sum(tracked_coin_in_usd)::DOUBLE ci, sum(tracked_net_usd)::DOUBLE net, sum(theo_usd)::DOUBLE theo FROM 'data/1_prepared_views/player_period.parquet' GROUP BY 1""")
pl = pl[pl.ci > 0]
def conc(x):
    loss = (-x.net).clip(lower=0).sort_values(ascending=False).values
    th = x.theo.sort_values(ascending=False).values
    n = len(x); tl = loss.sum(); tt = th.sum()
    pts = [0.0] + [R(loss[: max(1, int(round(n * q / 100)))].sum() / tl, 4) for q in range(1, 101)]
    top = {k: R(loss[: max(1, int(n * k / 100))].sum() / tl, 4) for k in (1, 5, 10, 20)}
    topth = {k: R(th[: max(1, int(n * k / 100))].sum() / tt, 4) for k in (1, 5, 10, 20)}
    return {"n": int(n), "ahead": R((x.net > 0).mean(), 4), "median_net": R(x.net.median(), 0), "p5_net": R(x.net.quantile(.05), 0), "p95_net": R(x.net.quantile(.95), 0),
            "net": R(x.net.sum(), 0), "theo": R(x.theo.sum(), 0), "top_loss": top, "top_theo": topth, "lorenz": pts,
            "hist": np.histogram(x.net.clip(-3000, 3000), bins=np.arange(-3000, 3001, 250))[0].tolist()}
concentration = {"All tracked players": conc(pl)}
for col, name in (("rg", "Region"), ("ag", "Age"), ("tr", "Tier")):
    for v, g in pl.groupby(col):
        concentration[f"{name}: {v}"] = conc(g)

# ---------- comps ----------
led = Q("""SELECT strftime(event_at_utc - INTERVAL 14 HOUR,'%Y-%m-%d') d, count(*) n, -sum(points_delta) pts, sum(face_value_cents)/100.0 face, sum(economic_cost_cents)/100.0 cost
 FROM 'data/3_guests/loyalty_ledger.parquet' WHERE event_type='redeem' GROUP BY 1 ORDER BY 1""")
led = led[(led.d >= "2025-01-01") & (led.d <= "2025-06-30")]
comp_daily = [[r.d, int(r.n), int(r.pts), R(r.face, 0), R(r.cost, 0)] for r in led.itertuples()]
benefits = Q("""SELECT benefit_id, CASE WHEN event_at_utc < '2025-05-01 14:00' THEN 'before' ELSE 'after' END per, count(*) n, avg(-points_delta) pts, avg(face_value_cents)/100 face
 FROM 'data/3_guests/loyalty_ledger.parquet' WHERE event_type='redeem' GROUP BY 1,2""")
ben = {}
for r in benefits.itertuples():
    ben.setdefault(r.benefit_id, {})[r.per] = {"n": int(r.n), "pts": R(r.pts, 0), "face": R(r.face, 2)}

# ---------- context ----------
lv = Q("SELECT month, visitor_volume, visitor_yoy_ratio::DOUBLE yoy, convention_attendance, hotel_occupancy_ratio::DOUBLE occ FROM 'data/4_context/real_sources/city_visitation_monthly.parquet' ORDER BY 1")
mo_bench = Q("SELECT month, sum(handle_usd)::DOUBLE handle, sum(agr_usd)::DOUBLE agr FROM 'data/4_context/real_sources/benchmark_state_monthly.parquet' GROUP BY 1 ORDER BY 1")
events = Q("SELECT name, event_type, strftime(start_date,'%Y-%m-%d') s, strftime(end_date,'%Y-%m-%d') e, strftime(announced_date,'%Y-%m-%d') a, local_scope FROM 'data/4_context/events.parquet' ORDER BY start_date").to_dict("records")
walk = Q("SELECT walkway_id, zone_a, zone_b, strftime(closed_from_utc,'%Y-%m-%d') f, strftime(closed_to_utc,'%Y-%m-%d') t, closure_reason FROM 'data/2_machine_decision/floor_walkways.parquet' WHERE closed_from_utc IS NOT NULL").to_dict("records")
actions = Q("SELECT action_type_id id, name, unit, unit_cost_cents/100.0 unit_cost, recurring_cost_cents_per_day/100.0 daily, lead_days lead, downtime_minutes dt, quantity_limit lim, incompatibility_group grp, notes FROM 'data/2_machine_decision/action_catalog.parquet'").to_dict("records")
ops_other = Q("SELECT machine_id, location_id, event_type, strftime(opened_at_local,'%Y-%m-%d') d FROM 'data/2_machine_decision/operations.parquet' WHERE event_type IN ('move','install','retire') ORDER BY opened_at_utc").to_dict("records")
floor = Q("SELECT location_id, node_type, zone_id, bank_id, name, x_m, y_m, capacity FROM 'data/2_machine_decision/floor_locations.parquet' WHERE node_type IN ('zone','bank','entrance','outlet')").to_dict("records")
model = json.load(open("build/model.json"))
wx = Q("SELECT strftime(source_date,'%Y-%m-%d') d, tmax_c::DOUBLE t, prcp_mm::DOUBLE p FROM 'data/4_context/real_sources/weather_daily.parquet' ORDER BY 1")
weather = [[r.d, R(r.t, 1), R(r.p, 1)] for r in wx.itertuples()]

data = {"months": months, "period_days": period_days, "zones": zones, "banks": banks, "themes": themes, "machines": machines, "mm": mm_rows,
        "days": days, "zone_day": zd, "traffic": traffic, "faults": faults, "roster": roster_rows,
        "regions": regions, "ages": ages, "tiers": tiers, "pgrp": pgrp, "concentration": concentration,
        "comp_daily": comp_daily, "benefits": ben, "lvcva": lv.to_dict("records"), "missouri": mo_bench.to_dict("records"),
        "events": events, "walkways": walk, "actions": actions, "ops_other": ops_other, "floor": floor, "model": model, "weather": weather}
s = json.dumps(data, separators=(",", ":"), default=lambda o: None if o is None or (isinstance(o, float) and np.isnan(o)) else (float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
s = s.replace("NaN", "null")
open(OUT, "w").write(s)
print("bytes", len(s), "mm rows", len(mm_rows), "faults", len(faults))
