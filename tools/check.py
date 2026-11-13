"""Self-check of the helpers against known results: python -m tools.check"""
import json

import pandas as pd
import plotly.io as pio

from tools import (PARENTS, bins_overview, changed_tables, extract_map, fuel_trim_table, list_bins, list_logs,
                   load_log, log_browser, map_browser, to_romraider)

pio.renderers.default = "json"  # no browser
D = "tools/MS42_ECU_Definitions_v0.44.xml"
bins, logs = list_bins(), list_logs()
assert list(bins)[0] == "stock" and "E85_V0.9" in bins, bins
assert list(bins).index("E85_V0.10") == list(bins).index("E85_V0.9") + 1  # natural sort

# changed tables match the byte diffs done by hand
assert changed_tables(D, bins["E85_V0.8"], bins["E85_V0.9"]) == ["Afterstart Enrichment"]
v7 = changed_tables(D, bins["stock"], bins["E85_V0.7"])
assert len(v7) == 18 and "Full Load Enrichment" in v7, v7
assert "Full Load Enrichment" not in changed_tables(D, bins["stock"], bins["E85_V0.8"])
ov = bins_overview(D, bins, PARENTS)
assert ov.loc["E85_V0.5", "parent"] == "E85_V0.3" and ov.loc["test_1", "parent"] == "stock", ov["parent"]
assert ov.loc["E85_V0.9", "changed vs parent"] == "Afterstart Enrichment"
assert ov.loc["E85_V0.8", "parent"] == "E85_V0.7"

# logs: every file loads, derived channels exist where possible
for name, path in logs.items():
    df = load_log(path)
    assert "Time (s)" in df and "Injector Duty (%)" in df, name
assert "Fuel Correction - Bank 1 (%)" in load_log(logs["2022-05-26/romraiderlog_20220526_102629.csv"])

# trim correction: only reliable cells change, by exactly their correction
fmap = extract_map(bins["E85_V0.9"], D, "Fuel Injection part load bank 1 warm engine")
recent = pd.concat(load_log(p) for k, p in logs.items() if k.startswith("2022-05-2"))
mean, count, corrected = fuel_trim_table(recent, fmap)
changed = (corrected != fmap.round(3)).to_numpy()
assert changed.any() and (count.to_numpy()[changed] >= 20).all()
assert abs(((corrected / fmap - 1) * 100 - mean).to_numpy()[changed]).max() < 0.2

# RomRaider paste format: header row of loads, then rpm + values
text = to_romraider(fmap).splitlines()
assert text[0] == "[Table3D]" and len(text) == len(fmap) + 2 and text[2].startswith("400.0\t")

# widgets: drive every control through its callbacks
mb = map_browser(D, bins, a="E85_V0.9", b="stock", table="Fuel Injection part load bank 1 warm engine")
(w_a, w_b), (w_t, w_only) = mb.children[0].children, mb.children[1].children
w_only.value = True
assert "Afterstart Enrichment" in w_t.options and len(w_t.options) == 12, w_t.options
w_b.value = "E85_V0.8"
assert list(w_t.options) == ["Afterstart Enrichment"]
out = mb.children[2]
assert len(out.outputs) == 6, len(out.outputs)  # title, (name + table) x2, plot
assert all(o["data"] for o in out.outputs) and json.dumps(out.outputs)  # nothing empty, all serialisable
w_b.value = "(none)"; w_only.value = False
assert len(out.outputs) == 4, len(out.outputs)
for t in ["Full Load Enrichment", "Fuel Injection Before Cranking", "Engine Speed Limiter (VSS Error)", "Ignition Part load RON 98"]:
    w_t.value = t

lb = log_browser(logs)
w_log, (w_ch, xyc) = lb.children[0], lb.children[1].children
for name in logs:
    w_log.value = name
w_ch.value = ("Injector Duty (%)",); xyc.children[2].value = "Coolant Temperature (°C)"
assert [len(o.outputs) for o in lb.children[2:]] == [1, 1] and all(o.outputs[0]["data"] for o in lb.children[2:])
print("all checks passed")
