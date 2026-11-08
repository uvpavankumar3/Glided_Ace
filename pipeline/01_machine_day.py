import duckdb, sys, pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
D = sys.argv[1]
con = duckdb.connect(); con.execute(f"SET file_search_path='{D}'")
df = con.sql("""
SELECT d.*, m.sum_bet_squared, m.scheduled_seconds sched_s, m.available_seconds, m.payout_positive_spins,
       g.payout_multiplier_variance pvar
FROM 'data/1_prepared_views/prepared_daily_view.parquet' d
JOIN 'data/2_machine_decision/machine_day.parquet' m USING (machine_id, gaming_date)
LEFT JOIN 'data/2_machine_decision/game_math.parquet' g ON g.config_id = d.config_id
WHERE d.active""").df()
for c in ["coin_in_usd","payout_usd","house_win_usd","theo_usd","luck_residual_usd","lease_cost_usd","service_cost_usd","power_cost_usd","repair_cost_usd","contribution_after_supplied_costs_usd"]:
    df[c] = df[c].astype(float)
df["luck_var"] = df.sum_bet_squared.astype(float) * df.pvar.astype(float) / 1e4  # dollars^2
print(df.shape, df.gaming_date.min(), df.gaming_date.max())
print(df.isna().sum()[df.isna().sum()>0])
g = df.groupby("machine_id").agg(
    zone=("zone_name", lambda s: s.mode().iat[0]), bank=("bank_id", lambda s: s.mode().iat[0]),
    n_locs=("location_id","nunique"), n_cfg=("config_id","nunique"),
    theme=("theme","last"), vol=("volatility_class","last"), mfr=("manufacturer","first"), lease=("lease_class","first"),
    days=("gaming_date","count"), coin_in=("coin_in_usd","sum"), hw=("house_win_usd","sum"), theo=("theo_usd","sum"),
    luck_var=("luck_var","sum"), avail_h=("available_hours","sum"), sched_s=("sched_s","sum"), occ_h=("occupied_hours","sum"),
    faults=("faults_opened","sum"), contrib=("contribution_after_supplied_costs_usd","sum"))
g["luck"] = g.hw - g.theo
g["luck_sd"] = np.sqrt(g.luck_var)
g["z"] = g.luck / g.luck_sd
g["avail"] = g.avail_h / (g.sched_s/3600)
g["theo_per_avail_h"] = g.theo / g.avail_h
g["occ"] = g.occ_h / g.avail_h
g["hold"] = g.hw / g.coin_in
g["theo_per_day"] = g.theo / g.days
g = g.sort_values("hw")
cols = ["zone","bank","n_locs","theme","vol","mfr","days","coin_in","hw","theo","luck","luck_sd","z","avail","occ","theo_per_avail_h","faults","contrib"]
print(g[cols].head(15).round(2).to_string())
print("\nfloor medians"); print(g[["days","avail","occ","theo_per_avail_h","theo_per_day","z"]].median())
print("\nz distribution"); print(g.z.describe()); print((g.z.abs()>3).sum(), "machines |z|>3")
print(g.sort_values("z")[cols].head(12).round(2).to_string())
print(g.sort_values("z")[cols].tail(5).round(2).to_string())
g.to_parquet("build/machine_summary.parquet")
df.to_parquet("build/md.parquet")
