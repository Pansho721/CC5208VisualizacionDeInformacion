"""
visualizator.py

Render origin -> destination routes on a static world map (PNG).

Expected CSV columns (extra columns are ignored):
    from_portname, from_lat, from_lon, to_portname, to_lat, to_lon,
    average_transit_days, daily_capacity_at_risk

Usage:
    python visualizator.py routes.csv
    python visualizator.py routes.csv --output map.png
    python visualizator.py routes.csv --color-by average_transit_days --top 50
"""

import argparse
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from global_land_mask import globe

REQUIRED_COLUMNS = [
    "from_portname", "from_lat", "from_lon",
    "to_portname", "to_lat", "to_lon",
]


def load_routes(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"CSV is missing required column(s): {', '.join(missing)}")
    return df.dropna(subset=["from_lat", "from_lon", "to_lat", "to_lon"])


def scale(series: pd.Series, lo: float, hi: float) -> pd.Series:
    """Min-max scale a numeric series into [lo, hi]; constant/NaN -> midpoint."""
    mid = (lo + hi) / 2
    smin, smax = series.min(skipna=True), series.max(skipna=True)
    if pd.isna(smin) or pd.isna(smax) or smax == smin:
        return pd.Series([mid] * len(series), index=series.index)
    return (lo + (series - smin) * (hi - lo) / (smax - smin)).fillna(mid)


def compute_extent(df: pd.DataFrame, pad_frac: float = 0.15):
    """Bounding box (lon_min, lon_max, lat_min, lat_max) around route endpoints."""
    lons = pd.concat([df["from_lon"], df["to_lon"]])
    lats = pd.concat([df["from_lat"], df["to_lat"]])
    lon_min, lon_max = lons.min(), lons.max()
    lat_min, lat_max = lats.min(), lats.max()
    lon_pad = max((lon_max - lon_min) * pad_frac, 2)
    lat_pad = max((lat_max - lat_min) * pad_frac, 2)
    return (max(lon_min - lon_pad, -180), min(lon_max + lon_pad, 180),
            max(lat_min - lat_pad, -90), min(lat_max + lat_pad, 90))


def make_axes(figsize, extent):
    """Plain lat/lon axes with a land/ocean basemap (offline, no network)."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal")

    lons = np.linspace(extent[0], extent[1], min(int((extent[1] - extent[0]) / 0.25), 1440))
    lats = np.linspace(extent[2], extent[3], min(int((extent[3] - extent[2]) / 0.25), 720))
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    land_mask = globe.is_land(lat_grid, lon_grid)

    cmap = mcolors.ListedColormap(["#a9cce3", "#ddd6c1"])  # ocean, land
    ax.pcolormesh(lon_grid, lat_grid, land_mask, cmap=cmap, shading="auto", zorder=0)
    ax.contour(lon_grid, lat_grid, land_mask, levels=[0.5], colors="black", linewidths=0.8, zorder=2)
    ax.grid(True, linewidth=0.3, color="#888888", alpha=0.4, zorder=1)
    return fig, ax


def build_map(df: pd.DataFrame, color_by, top, figsize=(16, 9)):
    if top is not None:
        df = df.sort_values("daily_capacity_at_risk", ascending=False).head(top) \
            if "daily_capacity_at_risk" in df.columns else df.head(top)

    use_color_scale = bool(color_by and color_by in df.columns)
    cmap = plt.get_cmap("YlOrRd")
    norm = color_vals = None
    if use_color_scale:
        color_vals = df[color_by].astype(float)
        cmin, cmax = color_vals.min(skipna=True), color_vals.max(skipna=True)
        norm = mcolors.Normalize(vmin=cmin, vmax=cmax) if cmin != cmax else None

        def color_for(v):
            return "#999999" if pd.isna(v) or norm is None else cmap(norm(v))

    fig, ax = make_axes(figsize, extent=compute_extent(df))

    for idx, row in df.iterrows():
        color = color_for(color_vals.loc[idx]) if use_color_scale else "#3b7dd8"
        ax.plot([row["from_lon"], row["to_lon"]], [row["from_lat"], row["to_lat"]],
                color=color, linewidth=1.5, alpha=0.8, zorder=3, solid_capstyle="round")

    origins = df[["from_portname", "from_lat", "from_lon"]].rename(
        columns={"from_portname": "portname", "from_lat": "lat", "from_lon": "lon"})
    dests = df[["to_portname", "to_lat", "to_lon"]].rename(
        columns={"to_portname": "portname", "to_lat": "lat", "to_lon": "lon"})
    ports = pd.concat([origins, dests], ignore_index=True).drop_duplicates(subset=["portname", "lat", "lon"])
    ax.scatter(ports["lon"], ports["lat"], s=20, color="#1f2937", edgecolor="white", linewidth=0.6, zorder=4)

    if use_color_scale and norm is not None:
        sm = cm.ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.05, shrink=0.5).set_label(color_by)

    ax.set_title("Shipping Routes", fontsize=16, fontweight="bold")
    fig.tight_layout()
    return fig, len(df)


def main():
    parser = argparse.ArgumentParser(description="Render routes from a CSV on a static world map image.")
    parser.add_argument("csv_path", help="Path to the input CSV file.")
    parser.add_argument("--output", "-o", default="routes_map.png", help="Output image path.")
    parser.add_argument("--color-by", default="average_transit_days",
                         help="Numeric column to color routes by. Use '' to disable.")
    parser.add_argument("--top", type=int, default=None, help="Only plot the top N routes by daily_capacity_at_risk.")
    parser.add_argument("--dpi", type=int, default=200, help="Output resolution in DPI.")
    args = parser.parse_args()

    df = load_routes(args.csv_path)
    fig, n_routes = build_map(df, args.color_by or None, args.top)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    print(f"Saved {n_routes} routes to {args.output}")


if __name__ == "__main__":
    main()