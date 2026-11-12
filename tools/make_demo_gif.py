"""Regenerate assets/demo.gif (v1.3 flow: install → search → pre-check → pick files → save → verify).

Requires Pillow and a CJK font. Usage:
    pip install pillow
    CJK_FONT=/path/NotoSansSC-Regular.otf CJK_FONT_BOLD=/path/NotoSansSC-Bold.otf python3 tools/make_demo_gif.py
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 960, 640
S = 2  # supersample
TALL = 1800  # logical height of the scrolling canvas
TOP, BOTTOM = 80, H - 34  # visible content area inside the window
F = os.environ.get("CJK_FONT", os.path.expanduser("~/.fonts/NotoSansSC.otf"))
FB = os.environ.get("CJK_FONT_BOLD", os.path.expanduser("~/.fonts/NotoSansSC-Bold.otf"))


def font(p, size):
    return ImageFont.truetype(p, size * S)


f14, f15, f16 = font(F, 14), font(F, 15), font(F, 16)
fb16 = font(FB, 16)
mono = font(F, 14)

BG = (244, 246, 252); WIN = (255, 255, 255); BAR = (238, 240, 247)
INK = (30, 41, 59); MUTE = (100, 116, 139); LINE = (226, 232, 240)
P1 = (109, 91, 255); OK = (16, 185, 129); WARN = (245, 158, 11)
USERBG = (99, 102, 241); LINK = (59, 130, 246)

logo = Image.open(os.path.join(ROOT, "assets", "logo-256.png")).convert("RGBA").resize(
    (26 * S, 26 * S), Image.LANCZOS)


def s(v):
    return int(v * S)


def rrect(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle([s(box[0]), s(box[1]), s(box[2]), s(box[3])], radius=s(r),
                        fill=fill, outline=outline, width=s(w))


def text(d, xy, t, f, fill):
    d.text((s(xy[0]), s(xy[1])), t, font=f, fill=fill)


def tw(t, f):
    return f.getlength(t) / S


def spinner(d, cx, cy, k):
    for i in range(8):
        a = (i / 8) * 2 * math.pi + k * 0.8
        c = int(200 - 140 * ((i + k) % 8) / 8)
        x, y = cx + 7 * math.cos(a), cy + 7 * math.sin(a)
        d.ellipse([s(x - 1.8), s(y - 1.8), s(x + 1.8), s(y + 1.8)], fill=(c, c, 255))


def tick(d, cx, cy, col=OK):
    d.ellipse([s(cx - 9), s(cy - 9), s(cx + 9), s(cy + 9)], fill=col)
    d.line([s(cx - 4.5), s(cy), s(cx - 1), s(cy + 4), s(cx + 5), s(cy - 4)],
           fill=(255, 255, 255), width=s(2.4), joint="curve")


# ---------- blocks: each draws at y and returns the next y ----------

def b_user(im, d, y, t, n):
    shown = t[:n] + ("▍" if n < len(t) else "")
    w = max(tw(t[:3], f16), tw(shown, f16)) + 32
    x1 = 900; x0 = x1 - w
    rrect(d, (x0, y, x1, y + 40), 14, fill=USERBG)
    text(d, (x0 + 16, y + 8), shown, f16, (255, 255, 255))
    return y + 56


def b_head(im, d, y):
    im.paste(logo, (s(60), s(y)), logo)
    text(d, (94, y + 2), "quark-search-save", fb16, INK)
    return y + 34


def b_cmd(im, d, y, t):
    rrect(d, (94, y, 900, y + 30), 8, fill=(241, 245, 249))
    text(d, (106, y + 7), "$ " + t, mono, (71, 85, 105))
    return y + 40


def b_status(im, d, y, kind, t, k=0, prog=None):
    if kind == "spin":
        spinner(d, 104, y + 11, k)
        text(d, (120, y), t, f15, MUTE)
        if prog is not None:
            x0 = 130 + tw(t, f15)
            rrect(d, (x0, y + 6, x0 + 200, y + 16), 5, fill=LINE)
            if prog * 200 > 4:
                rrect(d, (x0, y + 6, x0 + 200 * prog, y + 16), 5, fill=P1)
    else:
        tick(d, 104, y + 11, OK if kind == "ok" else WARN)
        text(d, (120, y), t, f15, INK)
    return y + 32


def b_table(im, d, y, cols, rows, n, sel=None, x1=900):
    tx0 = 94
    rrect(d, (tx0, y, x1, y + 32 + 30 * n), 10, outline=LINE, fill=(250, 251, 255))
    for cx, h in cols:
        text(d, (cx, y + 6), h, f14, MUTE)
    y2 = y + 32
    for i in range(n):
        if sel == i:
            rrect(d, (tx0 + 4, y2 + 1, x1 - 4, y2 + 29), 6, fill=(237, 233, 254))
        d.line([s(tx0), s(y2), s(x1), s(y2)], fill=LINE, width=s(1))
        for j, (cx, _) in enumerate(cols):
            col = P1 if (sel == i and j == 0) else (MUTE if j >= 2 else INK)
            text(d, (cx, y2 + 4), rows[i][j], f15, col)
        y2 += 30
    return y2 + 14


def b_box(im, d, y, label, value):
    w = tw(label + value, fb16) + 40
    rrect(d, (94, y, 94 + w, y + 46), 12, fill=(236, 253, 245), outline=(167, 243, 208))
    text(d, (110, y + 11), label, f16, MUTE)
    text(d, (110 + tw(label, f16), y + 11), value, fb16, (6, 95, 70))
    return y + 58


def b_note(im, d, y, t):
    text(d, (94, y), t, f15, MUTE)
    return y + 30


BLOCKS = {"user": b_user, "head": b_head, "cmd": b_cmd, "status": b_status,
          "table": b_table, "box": b_box, "note": b_note}


def render(blocks, offset):
    im = Image.new("RGB", (s(W), s(TALL)), WIN)
    d = ImageDraw.Draw(im)
    y = TOP + 10
    for b in blocks:
        y = BLOCKS[b[0]](im, d, y, *b[1:])
    bottom = y
    out = Image.new("RGB", (s(W), s(H)), BG)
    od = ImageDraw.Draw(out)
    rrect(od, (24, 20, W - 24, H - 20), 16, fill=WIN, outline=LINE)
    crop = im.crop((s(25), s(TOP + offset), s(W - 25), s(TOP + offset) + s(BOTTOM - TOP)))
    out.paste(crop, (s(25), s(TOP)))
    # window chrome
    od.rectangle([s(25), s(BOTTOM), s(W - 25), s(H - 22)], fill=WIN)
    od.rounded_rectangle([s(24), s(20), s(W - 24), s(H - 20)], radius=s(16), outline=LINE, width=s(1))
    od.rounded_rectangle([s(24), s(20), s(W - 24), s(80)], radius=s(16), fill=BAR, outline=LINE, width=s(1))
    od.rectangle([s(25), s(62), s(W - 25), s(80)], fill=WIN)
    od.line([s(24), s(62), s(W - 24), s(62)], fill=LINE, width=s(1))
    for i in range(3):
        od.ellipse([s(46 + i * 20 - 6), s(35), s(46 + i * 20 + 6), s(47)], fill=(203, 208, 220))
    title = "AI 智能体 · 对话"
    text(od, (W / 2 - tw(title, f14) / 2, 31), title, f14, MUTE)
    return out.resize((W, H), Image.LANCZOS), bottom


# ---------- script ----------

Q = "帮我找一下线性代数的课件，存到夸克网盘"
PICK = "第 1 个，只要第 3 章"
OKAY = "都存"
ROWS = [
    ("1", "专为程序员设计的线性代数（带源码课件）", "2026-11-11", "24", "第1章.pdf、第2章.pdf…"),
    ("2", "线性代数 经管类 郭文军", "2026-11-07", "36", "01 行列式.mp4…"),
    ("3", "应用数值线性代数 Demmel 中文版", "2026-11-05", "1", "应用数值线性代数.pdf"),
    ("4", "几何讲义 线性代数和微分几何", "2026-09-06", "12", "讲义01.pdf…"),
    ("5", "微分方程、动力系统和线性代数", "2026-08-30", "3", "Hirsch-Smale.pdf…"),
]
COLS = [(110, "#"), (138, "标题"), (478, "日期"), (578, "文件数"), (648, "内容预览")]
FILES = [("第3章 行列式.pdf", "2.1 MB", "文档"), ("第3章 习题.pdf", "0.8 MB", "文档")]
FCOLS = [(110, "文件名"), (330, "大小"), (420, "类型")]

frames, durs = [], []
cur = [0.0]


def add(blocks, ms, snap=False):
    _, bottom = render(blocks, 0)
    target = max(0.0, bottom - (BOTTOM - TOP) - 10)
    cur[0] = target if snap else cur[0] + (target - cur[0]) * 0.45
    if abs(cur[0] - target) < 2:
        cur[0] = target
    im, _ = render(blocks, cur[0])
    frames.append(im); durs.append(ms)


def settle(blocks, ms):
    for _ in range(5):
        add(blocks, 40)
    add(blocks, ms)


B = []
add([("user", Q, 0)], 600)
for i in range(1, len(Q) + 1):
    add([("user", Q, i)], 60)
B = [("user", Q, len(Q)), ("head",)]
add(B, 300)

# first-run install
for k in range(8):
    add(B + [("status", "spin", "首次使用：没找到夸克官方 Skill，经你同意后安装…", k)], 90)
B += [("status", "ok", "已从 quark.cn 安装夸克官方 Skill，并完成授权")]
add(B, 600)

# search
B += [("cmd", 'python3 pansou_search.py --kw "线性代数" --limit 10')]
for k in range(8):
    add(B + [("status", "spin", "PanSou 聚合搜索中，只保留夸克链接…", k)], 90)
B += [("status", "ok", "找到 95 条夸克链接")]
add(B, 400)

# pre-check
B += [("cmd", "python3 check_links.py   # 官方 share-detail 逐条验证")]
for k in range(11):
    add(B + [("status", "spin", "验证链接 [{}/10]".format(k), k, k / 10)], 110)
B += [("status", "ok", "7 条可用，3 条已失效已略过；前 5 条给你挑：")]
add(B, 300)
for r in range(1, 6):
    add(B + [("table", COLS, ROWS, r)], 200)
T = ("table", COLS, ROWS, 5)
settle(B + [T], 1800)
B += [("table", COLS, ROWS, 5, 0)]
add(B, 500)

# pick part of the share
for i in range(1, len(PICK) + 1):
    add(B + [("user", PICK, i)], 90)
B += [("user", PICK, len(PICK)), ("head",), ("cmd", 'node quark-drive.cjs share-search --keyword "第3章"')]
for k in range(6):
    add(B + [("status", "spin", "在分享里找「第3章」…", k)], 90)
B += [("status", "ok", "有 2 个文件匹配：")]
for r in range(1, 3):
    add(B + [("table", FCOLS, FILES, r, None, 520)], 200)
B += [("table", FCOLS, FILES, 2, None, 520)]
settle(B, 1200)

for i in range(1, len(OKAY) + 1):
    add(B + [("user", OKAY, i)], 120)
B += [("user", OKAY, len(OKAY)), ("head",), ("cmd", 'node quark-drive.cjs saveas --fid-list "f3a…,f3b…"')]
for k in range(14):
    add(B + [("status", "spin", "夸克官方 saveas 转存中…", k, min(1, k / 13))], 90)
B += [("status", "ok", "转存成功（code: 0）")]
add(B, 500)
B += [("status", "ok", "已回查：2 个文件都在网盘里"),
      ("box", "保存位置：", "/来自：分享/专为程序员设计的线性代数"),
      ("note", "以后跟我说「看看有没有更新」，只补新增的文件。")]
settle(B, 4000)

keys = [frames[i] for i in (0, len(frames) // 3, len(frames) // 2, len(frames) * 3 // 4, len(frames) - 1)]
sheet = Image.new("RGB", (W, H * len(keys)))
for i, k in enumerate(keys):
    sheet.paste(k, (0, H * i))
pal = sheet.quantize(colors=255, method=Image.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
frames[0].save(os.path.join(ROOT, "assets", "demo.gif"), save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True)
print(len(frames), sum(durs))
