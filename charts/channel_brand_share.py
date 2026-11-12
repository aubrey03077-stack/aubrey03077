"""各渠道品牌占比饼图 (XM IHS)：每个渠道单独输出一张图，扇区上标注品牌名和占比。"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]

OUT_DIR = Path(__file__).parent / "output"

COLORS = {
    "Xiaomi": "#FF6900",    # 橙色
    "Samsung": "#1F4FD8",   # 蓝色
    "Motorola": "#7B2FBE",  # 紫色
    "Honor": "#00A6A6",
    "Apple": "#555555",
    "TCL": "#D62728",
    "Nubia": "#2CA02C",
    "ZTE": "#8C564B",
    "Others": "#9E9E9E",
    "未统计": "#E6E6E6",
}

# 渠道 -> {品牌: 占比%}，来自 XM IHS 表；空白/0 的品牌不画
DATA = {
    "Personal": {"Xiaomi": 6.00, "Samsung": 52.00, "Motorola": 29.00, "Apple": 0.60, "TCL": 3.00, "Others": 9.40},
    "Movistar": {"Xiaomi": 4.60, "Samsung": 52.50, "Motorola": 31.00, "Apple": 0.60, "TCL": 4.20, "Nubia": 5.70, "Others": 0.30, "ZTE": 1.10},
    "Fravega": {"Xiaomi": 11.20, "Samsung": 43.00, "Motorola": 37.00, "Others": 8.80},
    "Oncity": {"Xiaomi": 7.42, "Samsung": 37.05, "Motorola": 45.63, "TCL": 2.78, "Nubia": 6.38, "Others": 0.23, "ZTE": 0.51},
    "TC": {"Xiaomi": 5.50, "未统计": 94.50},
    "Naldo": {"Xiaomi": 11.87, "Samsung": 34.14, "Motorola": 44.97, "TCL": 4.46, "Nubia": 2.94, "Others": 0.20, "ZTE": 1.42},
    "Claro": {"Xiaomi": 6.00, "Samsung": 45.00, "Motorola": 39.00, "Honor": 5.00, "TCL": 4.00, "Others": 1.00},
}

INSIDE_MIN = 10.0   # 占比 >= 该值的扇区，标签写在扇区内部
MIN_GAP = 0.17      # 外部标签之间的最小垂直间距


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") + "%"


def spread(ys, lo=-1.35, hi=1.35):
    """把同一侧的外部标签在垂直方向错开，避免重叠。ys 已按从上到下排序。"""
    out = list(ys)
    for i in range(1, len(out)):
        out[i] = min(out[i], out[i - 1] - MIN_GAP)
    if out and out[-1] < lo:
        out[-1] = lo
        for i in range(len(out) - 2, -1, -1):
            out[i] = max(out[i], out[i + 1] + MIN_GAP)
    return [min(y, hi) for y in out]


def draw(channel, shares):
    items = sorted(((k, v) for k, v in shares.items() if v > 0), key=lambda kv: -kv[1])
    # 小米固定排在 12 点钟开始
    items.sort(key=lambda kv: kv[0] != "Xiaomi")
    labels, values = zip(*items)

    fig, ax = plt.subplots(figsize=(9, 7.5))
    wedges, _ = ax.pie(
        values,
        colors=[COLORS[k] for k in labels],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )

    outer = {"L": [], "R": []}
    for w, name, v in zip(wedges, labels, values):
        ang = math.radians((w.theta1 + w.theta2) / 2)
        x, y = math.cos(ang), math.sin(ang)
        text = f"{name}\n{fmt(v)}"
        if v >= INSIDE_MIN:
            color = "#555555" if name == "未统计" else "white"
            ax.text(0.62 * x, 0.62 * y, text, ha="center", va="center",
                    fontsize=14, fontweight="bold", color=color)
        else:
            outer["R" if x >= 0 else "L"].append((y, x, text))

    for side, pts in outer.items():
        pts.sort(key=lambda p: -p[0])
        ys = spread([1.18 * p[0] for p in pts])
        for (y, x, text), ty in zip(pts, ys):
            tx = 1.3 if side == "R" else -1.3
            ax.annotate(
                text.replace("\n", " "),
                xy=(x, y), xytext=(tx, ty),
                ha="left" if side == "R" else "right", va="center",
                fontsize=12, fontweight="bold", color="#222222",
                arrowprops=dict(arrowstyle="-", color="#888888", lw=1),
            )

    title = f"{channel} 渠道品牌占比"
    if channel == "TC":
        title += "\n(表中仅有小米数据，其余为未统计)"
    ax.set_title(title, fontsize=18, fontweight="bold", pad=20)
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect("equal")
    fig.tight_layout()
    path = OUT_DIR / f"{channel}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    for ch, sh in DATA.items():
        print(draw(ch, sh))
