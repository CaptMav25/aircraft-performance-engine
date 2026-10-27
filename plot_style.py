"""
Module:   plot_style
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Shared chart style: bundled Roboto font, Title Case labels, abbreviations
    written as Full Name (ABBR), solid axis lines, and the right-hand sidebar
    of Conditions and Results tables used by every chart.
"""

import glob
import os

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, AutoMinorLocator

from units import ft_to_m, m_to_ft

# Blue and orange stay distinguishable for the common types of colour blindness.
BLUE = "#2a78d6"          # takeoff / accelerate-go
ORANGE = "#eb6834"        # landing / accelerate-stop
INK = "#1b1b1a"           # titles, key text
INK_2 = "#4a4945"         # axis labels, table labels
INK_3 = "#8a8983"         # reference lines, notes
GRID = "#e2e1dc"
GRID_MINOR = "#f0efeb"
PANEL = "#fbfbf9"         # plot area background
HEADER_FILL = "#2b2b29"   # table header bar
ROW_FILL = "#f4f3ef"      # alternate table rows
LIMIT_RED = "#c43b3b"     # runway / regulatory limits

AXIS = "#1b1b1a"          # solid axis lines and tick marks

# Roboto ships with the project (fonts/ folder, Apache 2.0 licence), so every computer
# draws the charts identically. The others are fallbacks if the folder is missing.
FONT_FAMILY = ["Roboto", "Helvetica Neue", "Arial", "DejaVu Sans"]
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Words kept exactly as written by title_case(): units and symbols
_KEEP_AS_IS = {"ft", "m", "kt", "lb", "kg", "s", "°c", "%", "m/s", "×", "=", "/", "–", "-", "·"}


def _register_project_fonts():
    """Load the bundled Roboto files so matplotlib can use them."""
    for path in glob.glob(os.path.join(FONT_DIR, "*.ttf")):
        try:
            font_manager.fontManager.addfont(path)
        except (OSError, RuntimeError):
            pass


def title_case(text):
    """
    Capitalize the first letter of every word, including after hyphens:
    "engine-failure speed" -> "Engine-Failure Speed".
    Words that already contain capitals or digits (BFL, V1, KTAS) and units
    (ft, kt, °C) are left exactly as written.
    """
    def fix(word):
        core = word.strip("()[],:;")
        if not core or core.lower() in _KEEP_AS_IS:
            return word
        if any(c.isupper() for c in core) or any(c.isdigit() for c in core):
            return word
        return "-".join(part[:1].upper() + part[1:] for part in word.split("-"))
    return " ".join(fix(word) for word in text.split(" "))


def use_style():
    """Apply the project's matplotlib defaults. Call once before drawing."""
    _register_project_fonts()
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT_FAMILY,
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "axes.edgecolor": AXIS,
        "axes.facecolor": PANEL,
        "axes.linewidth": 1.1,
        "axes.unicode_minus": True,
        "xtick.color": AXIS,
        "ytick.color": AXIS,
        "xtick.labelcolor": INK,
        "ytick.labelcolor": INK,
        "xtick.major.size": 5,
        "ytick.major.size": 5,
        "xtick.major.width": 1.1,
        "ytick.major.width": 1.1,
        "axes.labelcolor": INK,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "legend.frameon": False,
        "legend.fontsize": 9,
    })


def style_axes(ax, title=None, xlabel=None, ylabel=None):
    """Solid dark axis lines with ticks, light grid, thousands separators, Title Case labels."""
    ax.grid(True, which="major", color=GRID, lw=0.8)
    ax.grid(True, which="minor", color=GRID_MINOR, lw=0.6)
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1.1)
    ax.tick_params(which="major", length=5, width=1.1, color=AXIS, labelcolor=INK)
    ax.tick_params(which="minor", length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    if title:
        ax.set_title(title_case(title), loc="left", fontweight="bold", color=INK, pad=8)
    if xlabel:
        ax.set_xlabel(title_case(xlabel))
    if ylabel:
        ax.set_ylabel(title_case(ylabel))


def add_metres_axis(ax, label="Distance (m)"):
    """Second y-axis on the right showing the same distances in metres."""
    ax_m = ax.secondary_yaxis("right", functions=(ft_to_m, m_to_ft))
    ax_m.set_ylabel(title_case(label), color=INK_2, fontsize=8, rotation=270, labelpad=12)
    ax_m.tick_params(colors=INK_2, labelsize=7, length=4, width=1.0)
    ax_m.spines["right"].set_color(INK_2)
    ax_m.spines["right"].set_linewidth(1.0)
    ax_m.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    return ax_m


def figure_title(fig, title, x=0.04, y=0.965):
    """
    One bold Title Case title, top left. No subtitle: conditions go in the sidebar.
    Returns the Text so align_layout() can line it up with the charts.
    """
    return fig.text(x, y, title_case(title), fontsize=15, fontweight="bold", color=INK,
                    va="bottom")


def table_height(ax, rows, col_headers=None, row_height_in=0.26):
    """Height of a table in axes-fraction units (header bar + column titles + rows)."""
    ax_h_in = ax.get_position().height * ax.figure.get_figheight()
    n_rows = 1 + (1 if col_headers else 0) + len(rows)
    return n_rows * row_height_in / ax_h_in


def stack_tables(ax, tables, row_height_in=0.26, max_row_height_in=0.34, gap_in=0.30):
    """
    Draw several tables in a sidebar so the first starts exactly at the top edge
    and the last ends exactly at the bottom edge (lined up with the charts).
    Rows grow (up to max_row_height_in) to fill the space; any height left over
    becomes equal gaps between tables. Rows shrink if the tables would not fit.
    tables : list of dicts of draw_table() arguments (heading, rows, ...)
    """
    ax_h_in = ax.get_position().height * ax.figure.get_figheight()
    n_rows = sum(1 + (1 if t.get("col_headers") else 0) + len(t["rows"]) for t in tables)
    n_gaps = max(len(tables) - 1, 0)
    fill_row_in = (ax_h_in - n_gaps * gap_in) / n_rows        # row height that fills exactly
    row_height_in = min(max(fill_row_in, 0.18), max_row_height_in)

    heights = [table_height(ax, t["rows"], t.get("col_headers"), row_height_in) for t in tables]
    gap = (1 - sum(heights)) / n_gaps if n_gaps else 0
    top = 1.0
    for table, height in zip(tables, heights):
        draw_table(ax, top, row_height_in=row_height_in, **table)
        top -= height + gap


def align_layout(fig, plot_axes, side_ax, title_text=None, foot_text=None, gap_in=0.22):
    """
    Line everything up after drawing:
      - title and footnote start at the left edge of the charts (y-axis labels included)
      - the sidebar's top and bottom match the top and bottom of the plot areas
      - the sidebar's right edge mirrors the left margin
      - the title sits just above the charts, the footnote just below
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()

    def fig_box(artist):
        return inv.transform(artist.get_window_extent(renderer)
                             if not hasattr(artist, "get_tightbbox")
                             else artist.get_tightbbox(renderer))

    tight = [fig_box(ax) for ax in plot_axes]                 # incl. labels and titles
    left = min(box[0][0] for box in tight)
    top_tight = max(box[1][1] for box in tight)
    bottom_tight = min(box[0][1] for box in tight)
    plot_top = max(ax.get_position().y1 for ax in plot_axes)
    plot_bottom = min(ax.get_position().y0 for ax in plot_axes)

    side = side_ax.get_position()
    side_ax.set_position([side.x0, plot_bottom, (1 - left) - side.x0, plot_top - plot_bottom])

    gap = gap_in / fig.get_figheight()
    if title_text is not None:
        title_text.set_position((left, top_tight + gap))
    if foot_text is not None:
        foot_text.set_position((left, bottom_tight - gap))
        foot_text.set_va("top")


def draw_table(ax, top, heading, rows, col_headers=None, col_widths=None,
               row_height_in=0.26, swatches=None):
    """
    Draw one bordered table in a sidebar axes (axis turned off), starting at
    `top` (axes fraction). Returns the y position below the table.

    heading     : text in the dark header bar, e.g. "Conditions"
    rows        : list of tuples; the first item is the row label, the rest are values
    col_headers : optional column titles under the header bar
    col_widths  : fractions of the table width per column (default: label 58%)
    swatches    : optional list of colours, one per row, drawn as a line beside the label
    """
    ax.set_axis_off()
    n_cols = len(rows[0]) if rows else 2
    if col_widths is None:
        col_widths = [0.58] + [0.42 / (n_cols - 1)] * (n_cols - 1)
    ax_h_in = ax.get_position().height * ax.figure.get_figheight()
    row_h = row_height_in / ax_h_in
    x_edges = [0.0]
    for w in col_widths:
        x_edges.append(x_edges[-1] + w)

    y = top
    # Header bar
    ax.add_patch(Rectangle((0, y - row_h), 1, row_h, transform=ax.transAxes,
                           fc=HEADER_FILL, ec=HEADER_FILL, lw=0.8, clip_on=False))
    ax.text(0.03, y - row_h / 2, title_case(heading).upper(), transform=ax.transAxes,
            va="center", fontsize=8, fontweight="bold", color="white")
    y -= row_h

    # Optional column titles
    if col_headers:
        for i, text in enumerate(col_headers):
            ha, x = ("left", x_edges[i] + 0.03) if i == 0 else ("right", x_edges[i + 1] - 0.03)
            ax.text(x, y - row_h / 2, title_case(text), transform=ax.transAxes, va="center",
                    ha=ha, fontsize=7.5, fontweight="bold", color=INK_2)
        ax.plot([0, 1], [y - row_h, y - row_h], transform=ax.transAxes, color=INK_3, lw=0.8,
                clip_on=False)
        y -= row_h

    # Body rows
    for r, row in enumerate(rows):
        label, *values = row
        if r % 2 == 1:
            ax.add_patch(Rectangle((0, y - row_h), 1, row_h, transform=ax.transAxes,
                                   fc=ROW_FILL, ec="none", clip_on=False))
        x_label = 0.03
        if swatches and swatches[r]:
            ax.plot([0.03, 0.09], [y - row_h / 2] * 2, transform=ax.transAxes,
                    color=swatches[r], lw=2.5, solid_capstyle="butt", clip_on=False)
            x_label = 0.12
        ax.text(x_label, y - row_h / 2, title_case(label), transform=ax.transAxes,
                va="center", fontsize=8.2, color=INK_2)
        for i, value in enumerate(values, start=1):
            ax.text(x_edges[i + 1] - 0.03, y - row_h / 2, value, transform=ax.transAxes,
                    va="center", ha="right", fontsize=8.2, fontweight="bold", color=INK)
        y -= row_h

    # Outer border
    table_h = top - y
    ax.add_patch(Rectangle((0, y), 1, table_h, transform=ax.transAxes, fc="none",
                           ec=INK_3, lw=0.8, clip_on=False))
    return y - 0.045          # gap before the next table


def footnote(fig, text, x=0.04, y=0.018):
    """Small note along the bottom edge (sentence case). Returns the Text."""
    return fig.text(x, y, text, fontsize=7.5, color=INK_3)
