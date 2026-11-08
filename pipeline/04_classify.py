"""Reference implementation of the dashboard's machine diagnosis (mirrored in JS). Full window."""
import json, sys, numpy as np, pandas as pd
d = json.load(open(sys.argv[1]))
cols = ["mi","mo","zi","bi","ti","days","ci","hw","theo","lv","ah","sh","oh","f","dh","lt","co","sp","pp","rs","rss","rn"]
mm = pd.DataFrame(d["mm"], columns=cols)
sel = set(range(len(d["months"])))
mm = mm[mm.mo.isin(sel)]
pdays = sum(d["period_days"][d["months"][i]] for i in sel)
M = pd.DataFrame(d["machines"], columns=["id","mfr","vol","lease","rtp","hitp"])
# peer rates by theme x zone (rows), theme floor rates
tz = mm.groupby(["ti","zi"])[["theo","ah"]].sum()
tf = mm.groupby("ti")[["theo","ah"]].sum(); tf["r"] = tf.theo/tf.ah
rows = mm.groupby(["mi","ti","zi"])[["theo","ah"]].sum().reset_index()
rows = rows.join(tz, on=["ti","zi"], rsuffix="_g")
rows["peer_t"] = rows.theo_g-rows.theo; rows["peer_a"] = rows.ah_g-rows.ah
pe = rows.groupby("mi")[["theo","ah","peer_t","peer_a"]].sum()
# expected theo at peer rate for the machine's own hours
rows["exp_peer"] = np.where(rows.peer_a>0, rows.peer_t/rows.peer_a*rows.ah, np.nan)
rows["exp_floor"] = rows.ti.map(tf.r)*rows.ah
ex = rows.groupby("mi")[["exp_peer","exp_floor"]].sum(min_count=1)
g = mm.groupby("mi").agg(days=("days","sum"), ci=("ci","sum"), hw=("hw","sum"), theo=("theo","sum"), lv=("lv","sum"), ah=("ah","sum"), sh=("sh","sum"),
                         f=("f","sum"), lt=("lt","sum"), co=("co","sum"), sp=("sp","sum"), pp=("pp","sum"))
dom = mm.sort_values("days").groupby("mi").last()[["zi","bi","ti"]]
g = g.join(dom).join(ex).join(M, how="left")
g["zone"] = g.zi.map(lambda i: d["zones"][i]); g["bank"] = g.bi.map(lambda i: d["banks"][i]); g["theme"] = g.ti.map(lambda i: d["themes"][i]); g["id"] = g.index.map(lambda i: d["machines"][i][0])
g["luck"] = g.hw-g.theo; g["z"] = g.luck/np.sqrt(g.lv)
p = g.hitp; g["hit_z"] = (g.pp-g.sp*p)/np.sqrt(g.sp*p*(1-p))
g["avail"] = g.ah/g.sh; g["peer_idx"] = g.theo/g.exp_peer; g["loc_idx"] = g.exp_peer/g.exp_floor; g["theo_hold"] = g.theo/g.ci
def tags(r):
    t = []
    if r.days < 0.75*pdays: t.append("Short exposure")
    if r.hit_z > 5 or r.hit_z < -5 or r.z < -3: t.append("Payout anomaly")
    if r.z <= -1.5 and not (r.hit_z > 5 or r.z < -3): t.append("Bad luck")
    if r.loc_idx < 0.85: t.append("Weak location")
    if r.theo_hold < 0.06: t.append("Low-hold game")
    if r.avail < 0.97: t.append("Downtime")
    if r.peer_idx < 0.90 and r.days >= 60: t.append("Weak vs peers")
    return t
g["tags"] = g.apply(tags, axis=1)
g["verdict"] = g.tags.map(lambda t: "Inspect" if "Payout anomaly" in t else ("Replace candidate" if "Weak vs peers" in t else ("Keep — cause is outside the machine" if t else "Keep — normal")))
b10 = g.sort_values("hw").head(10)
print(b10[["id","zone","bank","theme","days","hw","theo","luck","z","hit_z","avail","peer_idx","loc_idx","theo_hold","tags","verdict"]].round(3).to_string())
print(g.verdict.value_counts())
w = g[g.verdict=="Replace candidate"].sort_values("peer_idx")
print(w[["id","zone","theme","days","hw","peer_idx","loc_idx","exp_peer","theo","tags"]].round(3).to_string())
print("gap to peers ($ theo)", (w.exp_peer-w.theo).sum())
print("bottom-10 rank of weak machines:", [int((g.hw< r.hw).sum())+1 for r in w.itertuples()])
print("floor median hw", g.hw.median(), "luck sum bottom10", b10.luck.sum(), "theo bottom10", b10.theo.sum())
g.to_pickle("build/class.pkl")
