"""
plot_relative_abundance.py
---------------------------------
Turns an Excel file of relative-abundance data (e.g. "inputs/Classes Rel. Abun.xlsx")
into a single horizontal stacked bar chart suitable for a research paper
figure.

Expected input format
----------------------
Two columns:
    - a label column (e.g. "OTU ID" / taxon / class name)
    - a numeric column with relative abundance, either as a fraction (0-1)
      or a percentage (0-100). The script auto-detects which one it is.

If your spreadsheet has multiple samples as separate columns (i.e. one row
per taxon, one column per sample), the script also handles that case and
draws one stacked bar per sample.

Usage
-----
    python plot_relative_abundance.py "inputs/Classes Rel. Abun.xlsx" --palette colorblind

    # list available palettes
    python plot_relative_abundance.py --list-palettes

    # change the "collate below X%" threshold (default 1%)
    python plot_relative_abundance.py "inputs/Classes Rel. Abun.xlsx" --threshold 2

    # save as SVG for vector output (better for LaTeX / journal submission)
    python plot_relative_abundance.py "inputs/Classes Rel. Abun.xlsx" --out graphs/figure1.svg

Requirements
------------
    pip install pandas matplotlib openpyxl
"""

import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Color palettes -- all chosen to be print-friendly / reasonably colorblind
# safe, and to work well as a sequence of discrete categories (not a
# continuous colormap look).
# --------------------------------------------------------------------------
PALETTES = {
    # Custom User Palettes
    "teal_sand": [
        "#264653", "#2a9d8f", "#8ab17d", "#e9c46a", "#f4a261", "#ee8959", "#e76f51",
    ],
    "rainbow": [
        "#f94144", "#f3722c", "#f8961e", "#f9844a", "#f9c74f", "#90be6d",
        "#43aa8b", "#4d908e", "#577590", "#277da1",
    ],
    "earthy": [
        "#283618", "#606c38", "#dda15e", "#bc6c25", "#6c584c", "#a98467",
        "#b08968", "#f0ead2", "#ddb892",
    ],
    # Okabe-Ito colorblind-safe palette, a standard choice for journals
    "colorblind": [
        "#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9",
        "#D55E00", "#F0E442", "#999999", "#000000", "#8DA0CB",
    ],
    # Muted, desaturated qualitative palette (matplotlib "tab10" toned down)
    "muted": [
        "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2",
        "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
    ],
    # Grayscale -- for journals that require black & white figures
    "grayscale": [
        "#1a1a1a", "#404040", "#595959", "#737373", "#8c8c8c",
        "#a6a6a6", "#bfbfbf", "#d9d9d9", "#ececec", "#f2f2f2",
    ],
    # ColorBrewer Set2 -- soft, qualitative, common in ecology papers
    "set2": [
        "#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854",
        "#FFD92F", "#E5C494", "#B3B3B3",
    ],
    # ColorBrewer Paired -- good when you have many categories
    "paired": [
        "#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C", "#FB9A99",
        "#E31A1C", "#FDBF6F", "#FF7F00", "#CAB2D6", "#6A3D9A",
    ],
    # Deep, high-contrast qualitative palette (matplotlib "tab10")
    "tab10": [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ],
    # Sequential blue (use when categories have a natural rank/order)
    "blues": plt.get_cmap("Blues_r")(np.linspace(0.15, 0.85, 10)).tolist(),
    # Sequential viridis (perceptually uniform, prints well in color or B/W)
    "viridis": plt.get_cmap("viridis")(np.linspace(0.05, 0.95, 10)).tolist(),
}

OTHER_COLOR = "#B0B0B0"  # neutral gray always reserved for the "Other" slice


def list_palettes():
    print("Available palettes:")
    for name in PALETTES:
        print(f"  - {name}")


def load_data(path, sheet_name=0):
    df = pd.read_excel(path, sheet_name=sheet_name)
    if df.shape[1] < 2:
        raise ValueError("Expected at least 2 columns (labels + values).")
    label_col = df.columns[0]
    value_cols = df.columns[1:]
    df = df.rename(columns={label_col: "label"})
    df["label"] = df["label"].astype(str).str.strip()

    # Auto-detect fraction (0-1) vs percentage (0-100) scale using the
    # first value column, and normalize everything to percentages (0-100).
    first_vals = pd.to_numeric(df[value_cols[0]], errors="coerce")
    if first_vals.sum() <= 1.5:
        for c in value_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce") * 100
    else:
        for c in value_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df, list(value_cols)


def collate_small_categories(df, value_cols, threshold_pct):
    """
    Collapse any category whose value is below `threshold_pct` (in ANY
    sample, for multi-sample data) into a single 'Other (<X%)' row, so the
    chart doesn't end in a long tail of tiny slices. Any existing
    'Other'/'Others' style row found in the input is folded in too.
    """
    df = df.copy()

    is_existing_other = df["label"].str.lower().str.match(r"^other[s]?\b")
    max_val = df[value_cols].max(axis=1)
    is_small = max_val < threshold_pct

    to_collate = is_existing_other | is_small
    kept = df.loc[~to_collate].copy()
    collated = df.loc[to_collate]

    if not collated.empty:
        other_row = {"label": f"Other (<{threshold_pct:g}%)"}
        for c in value_cols:
            other_row[c] = collated[c].sum()
        kept = pd.concat([kept, pd.DataFrame([other_row])], ignore_index=True)

    # Sort descending by the first sample's value (strictly by size, biggest on left/first)
    sort_col = value_cols[0]
    kept = kept.sort_values(by=sort_col, ascending=False)

    return kept.reset_index(drop=True)


def get_colors(labels, palette_name):
    palette = PALETTES.get(palette_name)
    if palette is None:
        raise ValueError(
            f"Unknown palette '{palette_name}'. "
            f"Choose from: {', '.join(PALETTES)}"
        )

    colors = []
    n_other_seen = 0
    n_regular = 0
    for label in labels:
        if label.startswith("Other"):
            colors.append(OTHER_COLOR)
            n_other_seen += 1
        else:
            colors.append(palette[n_regular % len(palette)])
            n_regular += 1
    return colors


def plot_stacked_bar(
    df,
    value_cols,
    palette_name="colorblind",
    out_path="graphs/relative_abundance.png",
    figsize=None,
    dpi=300,
    bar_height=0.6,
    title=None,
):
    labels = df["label"].tolist()
    colors = get_colors(labels, palette_name)

    n_samples = len(value_cols)
    sample_names = [str(c) for c in value_cols]

    n_cats = len(labels)
    if n_cats <= 8:
        ncol = 3
    elif n_cats <= 12:
        ncol = 4
    elif n_cats <= 18:
        ncol = 5
    else:
        ncol = 6
    n_rows = int(np.ceil(n_cats / ncol))

    if figsize is None:
        # Uniform size for all graphs to make the horizontal bar dimensions uniform (height = 2.0)
        figsize = (9.5, 2.0)

    fig, ax = plt.subplots(figsize=figsize)

    y_pos = np.arange(n_samples)
    left = np.zeros(n_samples)

    for i, (label, color) in enumerate(zip(labels, colors)):
        vals = df.loc[i, value_cols].to_numpy(dtype=float)
        ax.barh(
            y_pos,
            vals,
            left=left,
            height=bar_height,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            label=label,
        )
        left += vals

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sample_names)
    ax.set_xlabel("Relative abundance (%)")
    ax.set_xlim(0, 100)
    ax.invert_yaxis()  # first sample on top

    # Clean, publication-style axes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, linewidth=0.4, alpha=0.4)

    if title:
        ax.set_title(title, fontsize=12, fontweight="bold", pad=12)

    # Use fixed margins to ensure the overall horizontal bar dimensions are identical across all graphs.
    # (Do not use tight_layout since it makes margins dynamic based on label length).
    fig.subplots_adjust(left=0.18, right=0.95, bottom=0.55, top=0.90)
    legend_y = -0.65
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, legend_y),
        ncol=ncol,
        frameon=False,
        fontsize=6.5,
        handlelength=0.8,
        handleheight=0.8,
        columnspacing=0.8,
        labelspacing=0.15,
    )

    # Ensure output directory exists
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"Saved figure to: {out_path}")
    return fig, ax


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("excel_path", nargs="?", help="Path to the .xlsx file")
    parser.add_argument("--sheet", default=0, help="Sheet name or index (default: first sheet)")
    parser.add_argument(
        "--palette",
        default="teal_sand",
        choices=list(PALETTES.keys()),
        help="Color palette to use (default: teal_sand)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Collate categories below this percent into 'Other' (default: 1.0)",
    )
    parser.add_argument("--out", default="graphs/relative_abundance.png", help="Output image path (.png/.svg)")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution (default: 300)")
    parser.add_argument("--title", default=None, help="Optional chart title")
    parser.add_argument("--list-palettes", action="store_true", help="List available palettes and exit")

    args = parser.parse_args()

    if args.list_palettes:
        list_palettes()
        sys.exit(0)

    if not args.excel_path:
        parser.error("excel_path is required unless using --list-palettes")

    if args.out and args.out.lower().endswith(".pdf"):
        parser.error("PDF generation has been removed. Please save as .png or .svg.")

    df, value_cols = load_data(args.excel_path, sheet_name=args.sheet)
    df = collate_small_categories(df, value_cols, args.threshold)
    plot_stacked_bar(
        df,
        value_cols,
        palette_name=args.palette,
        out_path=args.out,
        dpi=args.dpi,
        title=args.title,
    )


if __name__ == "__main__":
    main()
