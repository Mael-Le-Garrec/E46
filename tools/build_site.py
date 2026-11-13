"""Precompute the data of the static site in docs/ (GitHub Pages): python -m tools.build_site

docs/index.html is hand written; this only (re)writes docs/data/.
"""
import json
import shutil
from pathlib import Path

import numpy as np

from tools.helpers import PARENTS, bins_overview, extract_map, list_bins, list_logs, list_maps, load_log

DEFINITION = "tools/MS42_ECU_Definitions_v0.44.xml"
DATA = Path("docs/data")


def _num(v, decimals):
    v = float(v)
    if not np.isfinite(v):
        return None
    v = round(v, decimals)
    return int(v) if v.is_integer() else v


def _dump(path, obj):
    path.write_text(json.dumps(obj, separators=(",", ":"), allow_nan=False))


def build_maps(bins):
    """Every readable table, each distinct version stored once, plus which version each bin has."""
    tables = {}
    for name in list_maps(DEFINITION, bin_path=bins["stock"]):
        try:
            frames = [extract_map(path, DEFINITION, name) for path in bins.values()]
        except ValueError:  # switches and tables outside the 32KB calibration
            continue
        versions, index = [], []
        for df in frames:
            version = {"x": [_num(v, 4) for v in df.columns], "y": [_num(v, 4) for v in df.index],
                       "z": [[_num(v, 4) for v in row] for row in df.to_numpy(float)]}
            if version not in versions:
                versions.append(version)
            index.append(versions.index(version))
        df = frames[0]
        tables[name] = {"units": df.attrs["units"], "xname": df.columns.name or "", "yname": df.index.name or "",
                        "versions": versions, "bins": index}

    overview = bins_overview(DEFINITION, bins, PARENTS)
    return {
        "bins": list(bins),
        "tables": tables,
        "overview": [{"bin": b, "parent": r["parent"], "vs_stock": int(r["tables vs stock"]),
                      "changed": r["changed vs parent"].split(", ") if r["changed vs parent"] else []}
                     for b, r in overview.iterrows()],
    }


def build_logs(logs):
    """One JSON per log (loaded on demand by the page), returns the index."""
    out = DATA / "logs"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    index = []
    for key, path in logs.items():
        df = load_log(path).select_dtypes("number")
        file = key.replace("/", "__").removesuffix(".csv") + ".json"
        _dump(out / file, {"columns": list(df.columns),
                           "data": {c: [_num(v, 3) for v in df[c].to_numpy(float)] for c in df.columns}})
        index.append({"name": key, "file": file, "rows": len(df), "seconds": round(float(df["Time (s)"].iloc[-1]))})
    return index


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    site = build_maps(list_bins())
    site["logs"] = build_logs(list_logs())
    _dump(DATA / "maps.json", site)
    size = sum(f.stat().st_size for f in DATA.rglob("*.json"))
    print(f"{len(site['tables'])} tables, {len(site['logs'])} logs, {size / 1e6:.1f} MB in {DATA}")
