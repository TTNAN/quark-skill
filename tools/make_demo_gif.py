"""Regenerate assets/demo.gif.

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
F = os.environ.get("CJK_FONT", os.path.expanduser("~/.fonts/NotoSansSC.otf"))
FB = os.environ.get("CJK_FONT_BOLD", os.path.expanduser("~/.fonts/NotoSansSC-Bold.otf"))

def font(p, s): return ImageFont.truetype(p, s * S)
f14, f15, f16, f18 = font(F, 14), font(F, 15), font(F, 16), font(F, 18)
fb16, fb18 = font(FB, 16), font(FB, 18)
mono13 = font(F, 14)

BG = (244, 246, 252); WIN = (255, 255, 255); BAR = (238, 240, 247)
INK = (30, 41, 59); MUTE = (100, 116, 139); LINE = (226, 232, 240)
P1 = (109, 91, 255); P2 = (31, 200, 242); OK = (16, 185, 129)
USERBG = (99, 102, 241)

logo = Image.open(os.path.join(ROOT, "assets", "logo-256.png")).convert("RGBA").resize((26 * S, 26 * S), Image.LANCZOS)

ROWS = [
    ("结合编程学数学 专为程序员设计的线性代数（带源码课件）", "2025-09-07", "c31a…"),
    ("线性代数 经管类 郭文军", "2026-11-07", "539e…"),
    ("几何讲义 第二学期 线性代数和微分几何", "2026-09-06", "ceac…"),
    ("应用数值线性代数 J.W.Demmel 中文版", "2026-11-11", "8699…"),
    ("微分方程、动力系统和线性代数 Hirsch & Smale", "2026-08-30", "65d3…"),
]
Q = "帮我找一下线性代数的课件，存到夸克网盘"
PICK = "要第 1 个"

def s(v): return int(v * S)

def rrect(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle([s(box[0]), s(box[1]), s(box[2]), s(box[3])], radius=s(r), fill=fill, outline=outline, width=s(w))

def text(d, xy, t, f, fill): d.text((s(xy[0]), s(xy[1])), t, font=f, fill=fill)

def tw(t, f): return f.getlength(t) / S

def bubble_user(d, y, t, cursor=False):
    shown = t + ("▍" if cursor else "")
    w = max(tw(Q[:4], f16), tw(shown, f16)) + 32
    x1 = 900; x0 = x1 - w
    rrect(d, (x0, y, x1, y + 40), 14, fill=USERBG)
    text(d, (x0 + 16, y + 8), shown, f16, (255, 255, 255))
    return y + 56

def agent_head(im, d, y):
    im.paste(logo, (s(60), s(y)), logo)
    text(d, (94, y + 2), "quark-search-save", fb16, INK)
    return y + 34

def spinner(d, cx, cy, k):
    for i in range(8):
        a = (i / 8) * 2 * math.pi + k * 0.8
        c = int(200 - 140 * ((i + k) % 8) / 8)
        x, y = cx + 7 * math.cos(a), cy + 7 * math.sin(a)
        d.ellipse([s(x - 1.8), s(y - 1.8), s(x + 1.8), s(y + 1.8)], fill=(c, c, 255))

def check(d, cx, cy, col=OK):
    d.ellipse([s(cx - 9), s(cy - 9), s(cx + 9), s(cy + 9)], fill=col)
    d.line([s(cx - 4.5), s(cy), s(cx - 1), s(cy + 4), s(cx + 5), s(cy - 4)], fill=(255, 255, 255), width=s(2.4), joint="curve")

def cmd(d, y, t):
    rrect(d, (94, y, 900, y + 30), 8, fill=(241, 245, 249))
    text(d, (106, y + 7), "$ " + t, mono13, (71, 85, 105))
    return y + 40

def frame(st):
    im = Image.new("RGB", (s(W), s(H)), BG)
    d = ImageDraw.Draw(im)
    rrect(d, (24, 20, W - 24, H - 20), 16, fill=WIN, outline=LINE)

    y = 80 - st.get("scroll", 0)
    y = bubble_user(d, y, Q[: st["q"]], cursor=st["q"] < len(Q))
    if st["stage"] >= 1:
        y = agent_head(im, d, y)
        y = cmd(d, y, 'python3 pansou_search.py --kw "线性代数" --limit 5')
        if st["stage"] == 1:
            spinner(d, 104, y + 11, st["k"]); text(d, (120, y), "PanSou 聚合搜索中，只保留夸克链接…", f15, MUTE)
            y += 34
        else:
            check(d, 104, y + 11); text(d, (120, y), "找到 95 条夸克链接，前 5 条给你挑：", f15, INK)
            y += 34
            # table
            tx0, tx1 = 94, 900
            rrect(d, (tx0, y, tx1, y + 32 + 30 * st["rows"]), 10, outline=LINE, fill=(250, 251, 255))
            for cx, h in ((110, "#"), (140, "标题"), (720, "日期"), (822, "链接")):
                text(d, (cx, y + 6), h, fb16 if False else f14, MUTE)
            y2 = y + 32
            for i in range(st["rows"]):
                sel = st.get("sel") == i
                if sel:
                    rrect(d, (tx0 + 4, y2 + 1, tx1 - 4, y2 + 29), 6, fill=(237, 233, 254))
                d.line([s(tx0), s(y2), s(tx1), s(y2)], fill=LINE, width=s(1))
                r = ROWS[i]
                text(d, (110, y2 + 4), str(i + 1), f15, P1 if sel else INK)
                text(d, (140, y2 + 4), r[0], f15, INK)
                text(d, (720, y2 + 4), r[1], f15, MUTE)
                text(d, (822, y2 + 4), r[2], f15, (59, 130, 246))
                y2 += 30
            y = y2 + 14
    if st["stage"] >= 3:
        y = bubble_user(d, y, PICK[: st["p"]], cursor=st["p"] < len(PICK))
    if st["stage"] >= 4:
        y = agent_head(im, d, y)
        y = cmd(d, y, 'node quark-drive.cjs saveas --url "https://pan.quark.cn/s/c31a…"')
        if st["stage"] == 4:
            spinner(d, 104, y + 11, st["k"]); text(d, (120, y), "夸克官方 saveas 转存中…", f15, MUTE)
            # progress
            pw = 300 * st["prog"]
            rrect(d, (300, y + 6, 600, y + 16), 5, fill=LINE)
            if pw > 4:
                rrect(d, (300, y + 6, 300 + pw, y + 16), 5, fill=P1)
            y += 34
        else:
            check(d, 104, y + 11); text(d, (120, y), "转存成功（code: 0）", f15, INK); y += 30
            if st["stage"] >= 6:
                check(d, 104, y + 11); text(d, (120, y), "已回查：文件在网盘里", f15, INK); y += 36
                rrect(d, (94, y, 620, y + 48), 12, fill=(236, 253, 245), outline=(167, 243, 208))
                text(d, (110, y + 12), "保存位置：", f16, MUTE)
                text(d, (110 + tw("保存位置：", f16), y + 12), "/来自：分享/线性代数（带源码课件）", fb16, (6, 95, 70))
                y += 60
    # chrome drawn on top so scrolled content is clipped
    d.rectangle([0, 0, s(W), s(62)], fill=BG)
    d.rounded_rectangle([s(24), s(20), s(W - 24), s(80)], radius=s(16), fill=BAR, outline=LINE, width=s(1))
    d.rectangle([s(25), s(62), s(W - 25), s(80)], fill=WIN)
    d.line([s(24), s(62), s(W - 24), s(62)], fill=LINE, width=s(1))
    d.rectangle([s(24), s(46), s(25), s(62)], fill=LINE); d.rectangle([s(W-25), s(46), s(W-24), s(62)], fill=LINE)
    for i, c in enumerate([(203, 208, 220)] * 3):
        d.ellipse([s(46 + i * 20 - 6), s(41 - 6), s(46 + i * 20 + 6), s(41 + 6)], fill=c)
    text(d, (W / 2 - tw("AI 智能体 · 对话", f14) / 2, 31), "AI 智能体 · 对话", f14, MUTE)
    return im.resize((W, H), Image.LANCZOS)

frames, durs = [], []
def add(st, ms): frames.append(frame(st)); durs.append(ms)

base = dict(q=0, stage=0, k=0, rows=0, p=0, prog=0)
add(dict(base), 700)
for i in range(1, len(Q) + 1):
    add(dict(base, q=i), 70)
add(dict(base, q=len(Q)), 500)
for k in range(10):
    add(dict(base, q=len(Q), stage=1, k=k), 90)
for r in range(0, 6):
    add(dict(base, q=len(Q), stage=2, rows=r), 260 if r else 300)
add(dict(base, q=len(Q), stage=2, rows=5), 1500)
add(dict(base, q=len(Q), stage=2, rows=5, sel=0), 500)
S3 = dict(base, q=len(Q), stage=3, rows=5, sel=0)
for i in range(1, len(PICK) + 1):
    add(dict(S3, p=i), 110)
add(dict(S3, p=len(PICK)), 400)
# scroll up to make room
SCROLL = 150
for j in range(1, 9):
    add(dict(S3, p=len(PICK), stage=4, scroll=int(SCROLL * (1 - (1 - j / 8) ** 2)), k=j, prog=j / 40), 50)
for k in range(16):
    add(dict(S3, p=len(PICK), stage=4, scroll=SCROLL, k=k + 8, prog=min(1, 0.2 + k / 15)), 90)
add(dict(S3, p=len(PICK), stage=5, scroll=SCROLL), 700)
add(dict(S3, p=len(PICK), stage=6, scroll=SCROLL), 3500)

keys = [frames[i] for i in (0, 30, 45, 52, len(frames) - 1)]
sheet = Image.new("RGB", (W, H * len(keys)))
for i, k in enumerate(keys): sheet.paste(k, (0, H * i))
pal = sheet.quantize(colors=255, method=Image.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
frames[0].save(os.path.join(ROOT, "assets", "demo.gif"), save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True)
print(len(frames), sum(durs))
