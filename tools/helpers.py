from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET
import struct

import numpy as np
import pandas as pd


def _read_c_string(blob, offset, length=32):
    chunk = blob[offset:offset + length]
    return chunk.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def _int_from_text(value):
    if value is None:
        return None
    return int(value, 0)


def _struct_code(storagetype):
    storagetype = (storagetype or "uint8").lower()
    if storagetype == "uint8":
        return "B"
    if storagetype == "int8":
        return "b"
    if storagetype == "uint16":
        return "H"
    if storagetype == "int16":
        return "h"
    if storagetype == "uint32":
        return "I"
    if storagetype == "int32":
        return "i"
    raise ValueError(f"Unsupported storagetype: {storagetype}")


def _evaluate(expression, x):
    if not expression:
        return x
    return eval(expression, {"__builtins__": {}}, {"x": x, "np": np})


def _child_table(table_node, table_type):
    for child in table_node.findall("table"):
        if child.get("type") == table_type:
            return child
    return None


@lru_cache
def load_definition(definition_path):
    return ET.parse(Path(definition_path)).getroot()


def _base_rom(root):
    for rom in root.findall("rom"):
        if rom.get("base") is None:
            return rom
    raise ValueError("Could not find the base ROM definition")


def select_rom(root, bin_path=None, rom_xmlid=None):
    if rom_xmlid:
        for rom in root.findall("rom"):
            if rom.findtext("romid/xmlid") == rom_xmlid:
                return rom

    if bin_path is not None:
        blob = Path(bin_path).read_bytes()
        for rom in root.findall("rom"):
            if rom.get("base") is None:
                continue
            xmlid = rom.findtext("romid/xmlid")
            internalidaddress = _int_from_text(rom.findtext("romid/internalidaddress"))
            if xmlid is None or internalidaddress is None:
                continue
            marker = _read_c_string(blob, internalidaddress, max(16, len(xmlid) + 4))
            if xmlid in marker:
                return rom

    raise ValueError("Could not match the BIN to a ROM definition; pass rom_xmlid explicitly")


def _table_lookup(container):
    lookup = {}
    for table in container.findall("table"):
        name = table.get("name")
        if name:
            lookup[name] = table
    return lookup


def resolve_table(root, rom, table_name):
    base = _base_rom(root)
    base_table = _table_lookup(base).get(table_name)
    rom_table = _table_lookup(rom).get(table_name)

    if base_table is None and rom_table is None:
        raise KeyError(f"Table not found: {table_name}")

    source = base_table if base_table is not None else rom_table
    merged = ET.fromstring(ET.tostring(source, encoding="unicode"))

    if rom_table is not None:
        merged.attrib.update(rom_table.attrib)
        for child in rom_table.findall("table"):
            child_type = child.get("type")
            merged_child = _child_table(merged, child_type)
            if merged_child is not None:
                merged_child.attrib.update(child.attrib)
                for grandchild in child:
                    merged_child.append(grandchild)

    return merged


def list_maps(definition_path, bin_path=None, rom_xmlid=None):
    root = load_definition(definition_path)
    rom = select_rom(root, bin_path=bin_path, rom_xmlid=rom_xmlid)
    base = _base_rom(root)

    names = set()
    for table in base.findall("table"):
        name = table.get("name")
        if name:
            names.add(name)
    for table in rom.findall("table"):
        name = table.get("name")
        if name:
            names.add(name)

    return sorted(names)


def _read_axis_values(axis_node, default_count, blob, parent_table):
    if axis_node is None:
        return None

    addr = _int_from_text(axis_node.get("storageaddress") or axis_node.findtext("storageaddress"))
    count = int(axis_node.get("size") or axis_node.get("count") or default_count)
    if addr is None:
        return np.arange(count, dtype=float)

    storagetype = axis_node.get("storagetype") or parent_table.get("storagetype", "uint8")
    endian = "<" if (axis_node.get("endian") or parent_table.get("endian", "little")) == "little" else ">"
    code = _struct_code(storagetype)

    unpacked = struct.unpack_from(f"{endian}{count}{code}", blob, addr)
    arr = np.array(unpacked, dtype=float)

    scaling = axis_node.find("scaling")
    if scaling is not None and scaling.get("expression"):
        arr = _evaluate(scaling.get("expression"), arr)
    return arr


def _axis_label_text(axis_node, axis_type="Axis"):
    if axis_node is None:
        return None
    for key in ("label", "name", "title"):
        value = axis_node.get(key)
        if value:
            return value.strip()
    for tag in ("label", "name", "title", "description", "unit"):
        text = axis_node.findtext(tag)
        if text:
            return text.strip()
    return f"{axis_type} Axis"


def get_axis_labels(definition_path, table_name, rom_xmlid=None, bin_path=None):
    root = load_definition(definition_path)
    rom = select_rom(root, bin_path=bin_path, rom_xmlid=rom_xmlid)
    table = resolve_table(root, rom, table_name)

    x_node = _child_table(table, "X Axis")
    y_node = _child_table(table, "Y Axis")
    return _axis_label_text(x_node, "X"), _axis_label_text(y_node, "Y")


def _apply_axis_names(frame, table, table_name):
    x_node = _child_table(table, "X Axis")
    y_node = _child_table(table, "Y Axis")
    x_label = _axis_label_text(x_node, "X")
    y_label = _axis_label_text(y_node, "Y")

    frame.index.name = y_label or table_name
    frame.columns.name = x_label
    return frame


def extract_map(
    bin_path,
    definition_path,
    table_name,
    rom_xmlid=None,
    scaled=True,
    round_axes=True,
    axis_decimals=3,
    round_cells=True,
    cell_decimals=3,
):
    root = load_definition(definition_path)
    rom = select_rom(root, bin_path=bin_path, rom_xmlid=rom_xmlid)
    table = resolve_table(root, rom, table_name)

    storagetype = table.get("storagetype", "uint8")
    endian = "<" if table.get("endian", "little") == "little" else ">"
    code = _struct_code(storagetype)

    rows = int(table.get("sizey", "1"))
    cols = int(table.get("sizex", "1"))
    count = rows * cols
    address = _int_from_text(table.get("storageaddress"))
    if address is None:
        raise ValueError(f"Table has no storageaddress: {table_name}")

    blob = Path(bin_path).read_bytes()
    unpacked = struct.unpack_from(f"{endian}{count}{code}", blob, address)
    values = np.array(unpacked, dtype=float).reshape(rows, cols)
    frame = pd.DataFrame(values)

    if scaled:
        y_axis_node = _child_table(table, "Y Axis")
        x_axis_node = _child_table(table, "X Axis")

        y_vals = _read_axis_values(y_axis_node, rows, blob, table)
        x_vals = _read_axis_values(x_axis_node, cols, blob, table)

        frame.index = y_vals if y_vals is not None else np.arange(rows)
        frame.columns = x_vals if x_vals is not None else np.arange(cols)

        if y_axis_node is not None and y_axis_node.find("scaling") is not None and y_vals is None:
            frame.index = _evaluate(y_axis_node.find("scaling").get("expression"), frame.index.values)
        if x_axis_node is not None and x_axis_node.find("scaling") is not None and x_vals is None:
            frame.columns = _evaluate(x_axis_node.find("scaling").get("expression"), frame.columns.values)

        if round_axes:
            try:
                frame.index = np.round(frame.index.astype(float), axis_decimals)
            except Exception:
                pass
            try:
                frame.columns = np.round(frame.columns.astype(float), axis_decimals)
            except Exception:
                pass

        table_scaling = table.find("scaling")
        if table_scaling is not None and table_scaling.get("expression"):
            frame = pd.DataFrame(
                _evaluate(table_scaling.get("expression"), frame.to_numpy(dtype=float)),
                index=frame.index,
                columns=frame.columns,
            )

        if round_cells:
            try:
                frame = frame.round(cell_decimals)
            except Exception:
                pass

    frame = _apply_axis_names(frame, table, table_name)
    scaling = table.find("scaling")
    frame.attrs["units"] = scaling.get("units", "") if scaling is not None else ""
    return frame


# ---------------------------------------------------------------------- bins


def list_bins(repo="."):
    """32KB calibration bins in the repo, keyed by short name ('stock', 'E85_V0.9', ...)."""
    bins = {}
    for path in sorted(Path(repo).glob("**/*.bin")):
        if ".git" in path.parts or path.stat().st_size != 32768:
            continue
        name = path.stem.replace("MS42_0110C6_32KB_", "").replace("hatrix_", "") or "stock"
        bins[name] = path
    return dict(sorted(bins.items(), key=lambda kv: kv[0] != "stock"))


@lru_cache
def _table_ranges(definition_path, rom_index):
    """Byte spans (table data + axes) of every table, to map changed bytes to tables.
    By rom index: each xmlid exists twice (512KB and 32KB layouts)."""
    root = load_definition(definition_path)
    rom = root.findall("rom")[rom_index]
    names = {t.get("name") for r in (_base_rom(root), rom) for t in r.findall("table")} - {None}
    ranges = {}
    for name in names:
        table = resolve_table(root, rom, name)
        address = _int_from_text(table.get("storageaddress"))
        if address is None:
            continue
        width = struct.calcsize(_struct_code(table.get("storagetype")))
        spans = [(address, address + width * int(table.get("sizex") or 1) * int(table.get("sizey") or 1))]
        for axis_type, size_key in (("X Axis", "sizex"), ("Y Axis", "sizey")):
            axis = _child_table(table, axis_type)
            axis_address = _int_from_text(axis.get("storageaddress")) if axis is not None else None
            if axis_address is not None:
                count = int(axis.get("size") or axis.get("count") or table.get(size_key) or 1)
                axis_width = struct.calcsize(_struct_code(axis.get("storagetype") or table.get("storagetype")))
                spans.append((axis_address, axis_address + axis_width * count))
        ranges[name] = spans
    return ranges


def changed_tables(definition_path, bin_a, bin_b):
    """Names of the tables whose bytes (data or axes) differ between two bins."""
    a = np.frombuffer(Path(bin_a).read_bytes(), np.uint8)
    b = np.frombuffer(Path(bin_b).read_bytes(), np.uint8)
    diff = np.flatnonzero(a != b)
    if not diff.size:
        return []
    root = load_definition(definition_path)
    ranges = _table_ranges(definition_path, root.findall("rom").index(select_rom(root, bin_path=bin_a)))
    return sorted(n for n, spans in ranges.items() if any(((diff >= s) & (diff < e)).any() for s, e in spans))


PARENTS = {"E85_V0.5": "E85_V0.3",  # V0.4 was a dead end
           "test_1": "stock"}     # any other bin's parent is the previous bin


def bins_overview(definition_path, bins, parents=None, reference="stock"):
    """Each bin's parent (the previous bin, unless set in `parents`), the tables changed vs
    that parent, and the count of tables changed vs stock."""
    parents, rows, previous = parents or {}, [], None
    for name in bins:
        parent, previous = parents.get(name, previous), name
        changed = changed_tables(definition_path, bins[parent], bins[name]) if parent else []
        rows.append({"bin": name, "parent": parent or "",
                     f"tables vs {reference}": len(changed_tables(definition_path, bins[reference], bins[name])),
                     "changed vs parent": ", ".join(changed)})
    return pd.DataFrame(rows).set_index("bin")


# ---------------------------------------------------------------------- maps


def plot_map(a, b=None, names=("A", "B"), title=""):
    """3D surface of `a` (with `b` overlaid in red) and a heatmap of b vs a in %.
    Line plot for 1D tables, None for single values."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    units = a.attrs.get("units", "")
    if a.size == 1:
        return None

    if 1 in a.shape:
        fig = go.Figure()
        for df, name in ((a, names[0]), (b, names[1])):
            if df is not None:
                s = df.squeeze()
                fig.add_trace(go.Scatter(x=s.index, y=s.values, name=name, mode="lines+markers"))
        fig.update_layout(title=title, xaxis_title=s.index.name, yaxis_title=units, height=450)
        return fig

    x, y = a.columns.to_numpy(float), a.index.to_numpy(float)
    cols = 1 if b is None else 2
    fig = make_subplots(
        rows=1, cols=cols,
        specs=[[{"type": "surface"}] + [{"type": "heatmap"}] * (cols - 1)],
        subplot_titles=[title, f"{names[1]} vs {names[0]} (%)"][:cols],
        column_widths=[0.55, 0.45] if cols == 2 else None,
    )
    fig.add_trace(go.Surface(x=x, y=y, z=a.to_numpy(float), name=names[0], colorscale="Viridis", showscale=False), 1, 1)
    if b is not None:
        fig.add_trace(go.Surface(x=x, y=y, z=b.to_numpy(float), name=names[1], colorscale="Reds",
                                 opacity=0.6, showscale=False), 1, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            pct = (b.to_numpy(float) / a.to_numpy(float) - 1) * 100
        pct[~np.isfinite(pct)] = np.nan
        fig.add_trace(go.Heatmap(x=[f"{v:g}" for v in x], y=[f"{v:g}" for v in y], z=pct,
                                 colorscale="RdBu_r", zmid=0, text=np.round(pct, 1), texttemplate="%{text}",
                                 colorbar=dict(title="%")), 1, 2)
        fig.update_xaxes(title_text=a.columns.name, row=1, col=2)
        fig.update_yaxes(title_text=a.index.name, autorange="reversed", row=1, col=2)  # same order as RomRaider
    fig.update_scenes(xaxis_title=a.columns.name or "X", yaxis_title=a.index.name or "Y", zaxis_title=units)
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0))
    return fig


def _show(out, *objects):
    """Replace an ipywidgets Output's content. Sets `outputs` from the kernel instead of
    capturing with `with out:`, which VS Code renders several times per display call."""
    out.outputs = ()
    for obj in objects:
        if hasattr(obj, "to_plotly_json"):  # its _ipython_display_ bypasses formatting: pass the bundle
            out.outputs += ({"output_type": "display_data", "data": obj._repr_mimebundle_({}, {}), "metadata": {}},)
        else:
            out.append_display_data(obj)


def map_browser(definition_path, bins, a="stock", b=None, table=None):
    """Widget: values and 3D plot of a table in bin A, optionally compared to bin B."""
    import ipywidgets as w
    from IPython.display import Markdown

    definition_path = str(definition_path)
    names = list(bins)
    all_tables = list_maps(definition_path, bin_path=bins[names[0]])
    none = "(none)"
    w_a = w.Dropdown(options=names, value=a, description="Bin A")
    w_b = w.Dropdown(options=[none] + names, value=b or none, description="Bin B")
    w_only = w.Checkbox(value=False, description="Only tables changed (A vs B, or A vs stock)", indent=False)
    w_t = w.Dropdown(options=all_tables, value=table if table in all_tables else all_tables[0],
                     description="Table", layout=w.Layout(width="550px"))
    out = w.Output()

    def render(*_):
        if w_t.value is None:
            _show(out, Markdown("No table differs."))
            return
        try:
            da = extract_map(bins[w_a.value], definition_path, w_t.value)
            db = None if w_b.value == none else extract_map(bins[w_b.value], definition_path, w_t.value)
        except ValueError as e:  # switches and tables outside the 32KB calibration
            _show(out, Markdown(f"Can't read *{w_t.value}* from these bins: {e}"))
            return
        objects = [Markdown(f"### {w_t.value} [{da.attrs['units']}]")]
        for name, df in [(w_a.value, da)] + ([(w_b.value, db)] if db is not None else []):
            objects += [Markdown(f"**{name}**"),
                        df.style.background_gradient(cmap="viridis", axis=None).format(precision=3)]
        fig = plot_map(da, db, names=(w_a.value, w_b.value), title=w_t.value)
        _show(out, *objects, *([fig] if fig is not None else []))

    def refresh(*_):
        if w_only.value:
            reference = bins[w_b.value] if w_b.value != none else bins.get("stock", bins[names[0]])
            options = changed_tables(definition_path, reference, bins[w_a.value])
        else:
            options = all_tables
        current = w_t.value
        w_t.unobserve(render, "value")
        w_t.options = options
        w_t.value = current if current in options else (options[0] if options else None)
        w_t.observe(render, "value")
        render()

    for widget in (w_a, w_b, w_only):
        widget.observe(refresh, "value")
    w_t.observe(render, "value")
    refresh()
    return w.VBox([w.HBox([w_a, w_b]), w.HBox([w_t, w_only]), out])


# ---------------------------------------------------------------------- logs


def list_logs(log_dir="logs/RomRaiders_Logs"):
    log_dir = Path(log_dir)
    return {str(p.relative_to(log_dir)): p for p in sorted(log_dir.glob("**/*.csv"))}


def _col(df, prefix):
    return next((df[c] for c in df.columns if c.startswith(prefix)), None)


def load_log(path):
    """RomRaider CSV with clean column names, time in s, injector duty and total fuel correction."""
    df = pd.read_csv(path, encoding="iso-8859-1")
    df.columns = [c.lstrip("* ").strip() for c in df.columns]
    df.insert(0, "Time (s)", df.pop("Time (msec)") / 1000)
    rpm, ipw = "Engine Speed (RPM)", "Fuel Injector Pulse Width (ms)"
    if {rpm, ipw} <= set(df.columns):
        df["Injector Duty (%)"] = df[ipw] * df[rpm] / 1200
    for bank in (1, 2):
        stft = f"Lambda Integrator - Bank {bank} (%)"
        ltft = f"Lambda Multiplicative Adaptation - Bank {bank} (%)"
        if {stft, ltft} <= set(df.columns):
            df[f"Fuel Correction - Bank {bank} (%)"] = ((1 + df[stft] / 100) * (1 + df[ltft] / 100) - 1) * 100
    return df


def log_browser(logs, log=None):
    """Widget: channels vs time (shared zoom) and an X/Y scatter coloured by a third channel."""
    import ipywidgets as w
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    default_channels = ["Engine Speed (RPM)", "Engine Load (mg/stroke)", "Fuel Injector Pulse Width (ms)",
                        "Fuel Correction - Bank 1 (%)", "Coolant Temperature (°C)"]
    default_xyc = ["Engine Load (mg/stroke)", "Fuel Injector Pulse Width (ms)", "Engine Speed (RPM)"]
    w_log = w.Dropdown(options=list(logs), value=log or list(logs)[-1], description="Log",
                       layout=w.Layout(width="550px"))
    w_ch = w.SelectMultiple(description="Vs time", rows=12, layout=w.Layout(width="450px"))
    w_x, w_y, w_c = (w.Dropdown(description=d, layout=w.Layout(width="400px")) for d in ("X", "Y", "Color"))
    out_t, out_s = w.Output(), w.Output()
    state = {"busy": True}

    def plot_time(*_):
        if state["busy"]:
            return
        df, channels = state["df"], list(w_ch.value)
        if not channels:
            _show(out_t)
            return
        fig = make_subplots(rows=len(channels), cols=1, shared_xaxes=True, vertical_spacing=0.02)
        for i, c in enumerate(channels, 1):
            fig.add_trace(go.Scattergl(x=df["Time (s)"], y=df[c], name=c, mode="lines"), i, 1)
            fig.update_yaxes(title_text=c.replace(" (", "<br>("), row=i, col=1)
        fig.update_xaxes(title_text="Time (s)", row=len(channels), col=1)
        fig.update_layout(height=160 * len(channels) + 80, showlegend=False, margin=dict(t=20, b=40))
        _show(out_t, fig)

    def plot_scatter(*_):
        if state["busy"]:
            return
        df = state["df"]
        fig = go.Figure(go.Scattergl(
            x=df[w_x.value], y=df[w_y.value], mode="markers", customdata=df["Time (s)"],
            marker=dict(color=df[w_c.value], colorscale="Viridis", size=5, showscale=True,
                        colorbar=dict(title=w_c.value.replace(" (", "<br>("))),
            hovertemplate="t = %{customdata} s<br>x = %{x}<br>y = %{y}<extra></extra>"))
        fig.update_layout(xaxis_title=w_x.value, yaxis_title=w_y.value, height=550, margin=dict(t=20))
        _show(out_s, fig)

    def load(*_):
        state["busy"] = True
        df = state["df"] = load_log(logs[w_log.value])
        columns = [c for c in df.columns if c != "Time (s)"]
        w_ch.options = columns
        w_ch.value = tuple(c for c in default_channels if c in columns)
        for widget, want in zip((w_x, w_y, w_c), default_xyc):
            keep = widget.value
            widget.options = columns
            widget.value = keep if keep in columns else (want if want in columns else columns[0])
        state["busy"] = False
        plot_time()
        plot_scatter()

    w_log.observe(load, "value")
    w_ch.observe(plot_time, "value")
    for widget in (w_x, w_y, w_c):
        widget.observe(plot_scatter, "value")
    load()
    return w.VBox([w_log, w.HBox([w_ch, w.VBox([w_x, w_y, w_c])]), out_t, out_s])


# ---------------------------------------------------------------------- tuning


def fuel_trim_table(log_df, fuel_map, bank=1, min_samples=20, min_change=2.0, min_coolant=80):
    """Mean fuel correction (STFT x LTFT, %) per map cell from warm closed-loop points,
    sample count per cell, and the map multiplied by the correction where it is reliable.

    ponytail: nearest-cell binning without interpolation weights; fine for corrections of a few %.
    """
    rpm, load = log_df["Engine Speed (RPM)"], log_df["Engine Load (mg/stroke)"]
    ok = _col(log_df, "Coolant Temperature") > min_coolant
    pedal = _col(log_df, "Throttle Position pedal")
    if pedal is not None:  # drop full load (open loop) and overrun fuel cut
        ok &= (pedal < 60) & ~((pedal < 0.5) & (rpm > 1000))
    d = log_df[ok]

    rows = np.abs(d["Engine Speed (RPM)"].to_numpy()[:, None] - fuel_map.index.to_numpy(float)).argmin(1)
    cols = np.abs(d["Engine Load (mg/stroke)"].to_numpy()[:, None] - fuel_map.columns.to_numpy(float)).argmin(1)
    grouped = d.groupby([rows, cols])[f"Fuel Correction - Bank {bank} (%)"].agg(["mean", "size"])

    mean = np.full(fuel_map.shape, np.nan)
    count = np.zeros(fuel_map.shape, int)
    for (r, c), m, n in zip(grouped.index, grouped["mean"], grouped["size"]):
        mean[r, c], count[r, c] = m, n
    mean = pd.DataFrame(mean, index=fuel_map.index, columns=fuel_map.columns).round(1)
    count = pd.DataFrame(count, index=fuel_map.index, columns=fuel_map.columns)

    apply = (count >= min_samples) & (mean.abs() >= min_change)
    corrected = fuel_map.where(~apply, fuel_map * (1 + mean / 100)).round(3)
    return mean, count, corrected


def to_romraider(df):
    """Tab-separated text that pastes into a RomRaider 3D table."""
    out = df.copy()
    out.index.name = out.columns.name = None
    return "[Table3D]\n" + out.to_csv(sep="\t")[1:]
