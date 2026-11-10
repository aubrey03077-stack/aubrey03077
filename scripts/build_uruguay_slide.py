"""Build a single Uruguay 2027 promo-node slide from the regional template (slide 6 layout)."""
import copy, sys
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.dml.color import RGBColor
from pptx.util import Pt, Emu
from pptx.oxml.ns import qn

SRC, OUT = sys.argv[1], sys.argv[2]
ORANGE = RGBColor(0xED, 0x7D, 0x31)

prs = Presentation(SRC)
KEEP = 5  # Peru slide used as the format reference
sldIdLst = prs.slides._sldIdLst
for i, sldId in reversed(list(enumerate(list(sldIdLst)))):
    if i != KEEP:
        prs.part.drop_rel(sldId.rId)
        sldIdLst.remove(sldId)
# save as a normal .pptx (template is macro-enabled but has no macros)
prs.part._content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
s = prs.slides[0]

shapes = {sh.name: sh for sh in s.shapes}
title, table_shape, foot, chart_frame = shapes["标题 1"], shapes["表格 4"], shapes["文本框 3"], shapes["图表 5"]

def set_runs(para, texts):
    """Keep the formatting of the first len(texts) runs, drop the rest."""
    runs = para.runs
    for r, t in zip(runs, texts):
        r.text = t
    for r in runs[len(texts):]:
        r._r.getparent().remove(r._r)

# Title: country (orange) + line break + subtitle
tp = title.text_frame.paragraphs[0]
set_runs(tp, ["乌拉圭", "主要爆发节点", "：三王节/母亲节/父亲节/黑五/圣诞节"])

# Footnote
fp = foot.text_frame.paragraphs[0]
set_runs(fp, ["* 1.母亲节/父亲节/儿童节：5/7/8月第二个星期日  2.Ciberlunes日期为预估  3.系数为预估值（年均=1.0），待用实际SO数据校准"])
fp.runs[0].font.size = Pt(10)
foot.top = Emu(6420000)
foot.left, foot.width = Emu(167574), Emu(11803012)
fp.alignment = 3  # right

# Table
tbl = table_shape.table
col0 = tbl.columns[0].width
rest = (table_shape.width - col0) // 12
for c in range(1, 13):
    tbl.columns[c].width = rest
rows = {
    0: ["Uruguay"],
    1: ["", "三王节\n（1.6）", "情人节\n（2.14）", "开学季\n（3.1）", "", "母亲节\n（5.9）", "Ciberlunes\n（6月上旬*）",
        "父亲节\n（7.11）", "儿童节\n（8.8）", "", "Ciberlunes\n（10月上旬*）", "黑五+CM\n（11.26-29）", "圣诞节\n（12.25）"],
    2: ["", "W1", "W6", "W9", "", "W18", "W23", "W27", "W31", "", "W40", "W47-48", "W51"],
    3: ["", "all channel", "all channel", "all channel", "", "all channel", "电商", "all channel", "all channel", "", "电商", "all channel", "all channel"],
    4: ["", "待填", "", "待填", "", "待填", "待填", "待填", "待填", "", "待填", "待填", "待填"],
    5: ["", "待填", "", "待填", "", "待填", "待填", "待填", "待填", "", "待填", "待填", "待填"],
}
coef = [1.0, 0.8, 0.9, 0.8, 1.1, 1.0, 1.1, 0.9, 0.8, 0.95, 1.25, 1.4]
rows[6] = [""] + [("%.2f" % v).rstrip("0") if v * 10 % 1 else "%.1f" % v for v in coef]

def ref_cell(r):
    for c in range(1, 13):
        if tbl.cell(r, c).text_frame.paragraphs[0].runs:
            return tbl.cell(r, c)
    return tbl.cell(r, 0)

def fill(cell, text, ref):
    txBody = cell._tc.txBody
    ref_p, ref_r = ref
    for p in txBody.findall(qn("a:p")):
        txBody.remove(p)
    for line in text.split("\n"):
        p = copy.deepcopy(ref_p)
        for child in list(p):
            if child.tag != qn("a:pPr"):
                p.remove(child)
        if line:
            r = copy.deepcopy(ref_r)
            r.find(qn("a:t")).text = line
            p.append(r)
        txBody.append(p)

for r, vals in rows.items():
    rc = ref_cell(r) if r else tbl.cell(0, 0)
    rp = copy.deepcopy(rc.text_frame.paragraphs[0]._p)
    ref = (rp, copy.deepcopy(rp.find(qn("a:r"))))
    for c, v in enumerate(vals):
        if r and c == 0:
            continue
        fill(tbl.cell(r, c), v, ref)
# compact text so the table keeps the template's height
for r in range(1, 6):
    for c in range(1, 13):
        for p in tbl.cell(r, c).text_frame.paragraphs:
            for run in p.runs:
                run.font.size = Pt(9)
heights = [Emu(230000), Emu(380000), Emu(240000), Emu(240000), Emu(240000), Emu(240000), Emu(260000)]
for row, hgt in zip(tbl.rows, heights):
    row.height = hgt
table_shape.top = Emu(4180000)

# Chart: replace the linked chart with one embedded line
x, y, w, h = chart_frame.left, Emu(1350000), chart_frame.width, Emu(2750000)
s.shapes._spTree.remove(chart_frame._element)
cd = CategoryChartData()
cd.categories = [str(m) for m in range(1, 13)]
cd.add_series("2027年预估系数", coef)
gf = s.shapes.add_chart(XL_CHART_TYPE.LINE, x, y, w, h, cd)
ch = gf.chart
ch.has_title = True
ch.chart_title.text_frame.text = "乌拉圭 2027 促销系数趋势（预估，年均=1.0）"
tr = ch.chart_title.text_frame.paragraphs[0].runs[0]
tr.font.size, tr.font.bold = Pt(10), True
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(8)
ser = ch.plots[0].series[0]
ser.smooth = True
ser.format.line.color.rgb = ORANGE
ser.format.line.width = Pt(2.5)
ser.marker.style = None
from pptx.enum.chart import XL_MARKER_STYLE
ser.marker.style = XL_MARKER_STYLE.NONE
va = ch.value_axis
va.minimum_scale, va.maximum_scale, va.major_unit = 0, 1.6, 0.4
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = RGBColor(0xD9, 0xD9, 0xD9)
va.tick_labels.font.size = Pt(8)
va.tick_labels.number_format, va.tick_labels.number_format_is_linked = "0.0", False
va.format.line.fill.background()
ca = ch.category_axis
ca.tick_labels.font.size = Pt(8)
ca.format.line.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)
labels = {0: "三王节", 2: "开学季", 4: "母亲节", 5: "Ciberlunes", 6: "父亲节", 9: "Ciberlunes", 10: "黑五", 11: "圣诞节"}
for i, t in labels.items():
    dl = ser.points[i].data_label
    dl.has_text_frame = True
    dl.text_frame.text = t
    dl.position = XL_LABEL_POSITION.ABOVE
    run = dl.text_frame.paragraphs[0].runs[0]
    run.font.size = Pt(10 if t in ("母亲节", "黑五", "圣诞节", "三王节", "父亲节") else 9)
    run.font.bold = t in ("黑五", "圣诞节")
prs.save(OUT)
print("saved", OUT)
