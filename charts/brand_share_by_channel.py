"""每个品牌一张饼图：该品牌在各渠道的占比 (XM IHS)。

扇区标签 = 渠道名 + 该品牌在该渠道的份额；扇区大小按各渠道份额的相对大小。
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

from channel_brand_share import DATA

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]

BRAND_COLORS = {
    "Xiaomi": "#FF6900",    # 橙色
    "Samsung": "#1F4FD8",   # 蓝色
    "Motorola": "#7B2FBE",  # 紫色
    "Honor": "#00A6A6",
    "Apple": "#555555",
    "TCL": "#D62728",
    "Nubia": "#2CA02C",
    "Others": "#8A8A8A",
    "ZTE": "#8C564B",
}


def shades(hex_color, n):
    """同一品牌色由深到浅的 n 个色阶。"""
    r, g, b = to_rgb(hex_color)
    out = []
    for i in range(n):
        t = 0.55 * i / max(n - 1, 1)  # 最多向白色混合 55%
        out.append((r + (1 - r) * t, g + (1 - g) * t, b + (1 - b) * t))
    return out


def place_labels(ax, wedges, labels, min_gap=0.2):
    """外侧标签 + 引线；同一侧的标签上下错开避免重叠。"""
    if len(wedges) == 1:  # 只有一个渠道：标签直接写在饼图中心
        ax.text(0, 0, labels[0], ha="center", va="center", fontsize=18,
                color="white", fontweight="bold")
        return
    pts = []
    for w, lab in zip(wedges, labels):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        x, y = np.cos(ang), np.sin(ang)
        pts.append([x, y, 1.25 * y, lab])
    for side in (1, -1):
        group = sorted([p for p in pts if np.sign(p[0] or 1) == side], key=lambda p: p[2])
        for i in range(1, len(group)):
            if group[i][2] - group[i - 1][2] < min_gap:
                group[i][2] = group[i - 1][2] + min_gap
        top = 1.3  # 不超过此高度，超出时整体自上而下回推
        for i in range(len(group) - 1, -1, -1):
            limit = top if i == len(group) - 1 else group[i + 1][2] - min_gap
            group[i][2] = min(group[i][2], limit)
    for x, y, ly, lab in pts:
        side = 1 if x >= 0 else -1
        lx = side * 1.3
        ax.annotate(
            lab, xy=(x, y), xytext=(lx, ly),
            ha="left" if side > 0 else "right", va="center",
            fontsize=13, color="#222222",
            arrowprops=dict(arrowstyle="-", color="#999999", lw=1,
                            connectionstyle="angle,angleA=0,angleB=90" if abs(ly - 1.25 * y) > 1e-6 else "arc3"),
        )


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand_pies")
os.makedirs(OUT_DIR, exist_ok=True)

for idx, (brand, color) in enumerate(BRAND_COLORS.items(), 1):
    items = [(ch, s[brand]) for ch, s in DATA.items() if s.get(brand, 0) > 0]
    items.sort(key=lambda x: -x[1])
    channels, values = zip(*items)
    labels = [f"{ch}\n{v:.2f}%".replace(".00%", "%") for ch, v in items]

    fig, ax = plt.subplots(figsize=(9, 8))
    wedges, _ = ax.pie(
        values,
        colors=shades(color, len(values)),
        startangle=90,
        counterclock=False,
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )
    place_labels(ax, wedges, labels)
    ax.set_title(f"{brand} 各渠道占比", fontsize=20, fontweight="bold", color=color, pad=30)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, f"{idx}_{brand}.png"), dpi=150)
    plt.close(fig)
