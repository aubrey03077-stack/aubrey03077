"""各渠道品牌占比饼图 (XM IHS)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]

COLORS = {
    "Xiaomi": "#FF6900",    # 橙色
    "Samsung": "#1F4FD8",   # 蓝色
    "Motorola": "#7B2FBE",  # 紫色
    "Honor": "#00A6A6",
    "Apple": "#555555",
    "TCL": "#D62728",
    "Nubia": "#2CA02C",
    "ZTE": "#8C564B",
    "Others": "#BDBDBD",
    "未统计": "#EEEEEE",
}

DATA = {
    "Personal": {"Xiaomi": 6.00, "Samsung": 52.00, "Motorola": 29.00, "Apple": 0.60, "TCL": 3.00, "Others": 9.40},
    "Movistar": {"Xiaomi": 4.60, "Samsung": 52.50, "Motorola": 31.00, "Apple": 0.60, "TCL": 4.20, "Nubia": 5.70, "Others": 0.30, "ZTE": 1.10},
    "Fravega": {"Xiaomi": 11.20, "Samsung": 43.00, "Motorola": 37.00, "Others": 8.80},
    "Oncity": {"Xiaomi": 7.42, "Samsung": 37.05, "Motorola": 45.63, "TCL": 2.78, "Nubia": 6.38, "Others": 0.23, "ZTE": 0.51},
    "TC": {"Xiaomi": 5.50, "未统计": 94.50},
    "Naldo": {"Xiaomi": 11.87, "Samsung": 34.14, "Motorola": 44.97, "TCL": 4.46, "Nubia": 2.94, "Others": 0.20, "ZTE": 1.42},
    "Claro": {"Xiaomi": 6.00, "Samsung": 45.00, "Motorola": 39.00, "Honor": 5.00, "TCL": 4.00, "Others": 1.00},
}


INSIDE_MIN = 5.0  # 小于该值的扇区把数值标在饼图外侧


def pct(v):
    return f"{v:.1f}%" if v >= INSIDE_MIN else ""


fig, axes = plt.subplots(2, 4, figsize=(20, 10.5))
for ax, (channel, shares) in zip(axes.flat, DATA.items()):
    items = [(k, v) for k, v in shares.items() if v > 0]
    labels, values = zip(*items)
    outer = [f"{v:.1f}%" if 2.0 <= v < INSIDE_MIN else "" for v in values]
    ax.pie(
        values,
        labels=outer,
        labeldistance=1.1,
        colors=[COLORS[k] for k in labels],
        autopct=pct,
        startangle=90,
        counterclock=False,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
        textprops=dict(color="white", fontsize=11, fontweight="bold"),
    )
    for t in ax.texts:
        if t.get_text() in outer and t.get_text():
            t.set_color("#333333")
            t.set_fontsize(10)
    title = channel + ("\n(仅有小米数据)" if channel == "TC" else "")
    ax.set_title(title, fontsize=15, fontweight="bold")
    if channel == "TC":
        for t in ax.texts:
            if t.get_text() == "94.5%":
                t.set_color("#888888")

axes.flat[-1].axis("off")
handles = [plt.matplotlib.patches.Patch(color=c, label=k) for k, c in COLORS.items()]
axes.flat[-1].legend(handles=handles, loc="center", fontsize=13, frameon=False, title="品牌", title_fontsize=14)

fig.suptitle("各渠道品牌占比 (XM IHS)", fontsize=20, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(__file__.replace(".py", ".png"), dpi=150)
