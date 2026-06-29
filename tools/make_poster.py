"""生成 MAOE 项目海报 —— 65cm × 110cm 竖版 jpg。

使用：
    .venv/bin/python tools/make_poster.py
输出：
    docs/poster/maoe-poster-65x110.jpg
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ============== 物理尺寸 ==============
CM_W, CM_H = 65, 110
DPI = 150
PX_W = int(CM_W / 2.54 * DPI)   # ≈3839
PX_H = int(CM_H / 2.54 * DPI)   # ≈6496

# ============== 配色（科技深蓝 + 青色高光） ==============
BG_TOP = (8, 12, 28)
BG_BOTTOM = (18, 28, 56)
ACCENT = (88, 198, 255)        # 主色（青）
ACCENT_2 = (255, 184, 77)      # 强调（金）
TEXT = (235, 240, 250)
TEXT_DIM = (160, 180, 210)
GRID = (40, 60, 100)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "poster"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "maoe-poster-65x110.jpg"


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if not bold
        else [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/HelveticaNeue.ttc",
        ]
    )
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _gradient_bg(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / h
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _draw_grid(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    step = 120
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=GRID, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=GRID, width=1)


def _accent_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int = 240, h: int = 18) -> None:
    draw.rectangle([x, y, x + w, y + h], fill=ACCENT)


def _section_title(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> int:
    _accent_bar(draw, x, y + 8)
    draw.text((x + 270, y), text, font=font, fill=TEXT)
    return y + 110


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    buf = ""
    for ch in text:
        candidate = buf + ch
        bbox = font.getbbox(candidate)
        if bbox[2] - bbox[0] > max_w and buf:
            lines.append(buf)
            buf = ch
        else:
            buf = candidate
    if buf:
        lines.append(buf)
    return lines


def _draw_paragraph(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int],
    max_w: int,
    line_gap: int = 14,
) -> int:
    for line in text.split("\n"):
        for wrapped in _wrap_text(line, font, max_w):
            draw.text((x, y), wrapped, font=font, fill=color)
            bbox = font.getbbox(wrapped)
            y += (bbox[3] - bbox[1]) + line_gap
        y += line_gap // 2
    return y


def _arrow(
    draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, color=ACCENT, width: int = 6
) -> None:
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # 简易箭头
    if x2 > x1:
        draw.polygon([(x2, y2), (x2 - 24, y2 - 12), (x2 - 24, y2 + 12)], fill=color)
    else:
        draw.polygon([(x1, y1), (x1 - 24, y1 - 12), (x1 - 24, y1 + 12)], fill=color)


def _node(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    accent: tuple[int, int, int] = ACCENT,
) -> None:
    draw.rectangle([x, y, x + w, y + h], outline=accent, width=4)
    # 左侧色条
    draw.rectangle([x, y, x + 12, y + h], fill=accent)
    # 居中文字
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w - tw) // 2 + 6, y + (h - th) // 2 - 4), text, font=font, fill=TEXT)


def build() -> None:
    img = _gradient_bg(PX_W, PX_H)
    draw = ImageDraw.Draw(img)
    _draw_grid(draw, PX_W, PX_H)

    # ============== Header ==============
    title_font = _find_font(220, bold=True)
    sub_font = _find_font(96)
    badge_font = _find_font(64)
    h1 = "MAOE"
    draw.text((140, 120), h1, font=title_font, fill=TEXT)

    # accent block beside title
    draw.rectangle([140 + 700, 120 + 40, 140 + 700 + 24, 120 + 240], fill=ACCENT)

    draw.text(
        (140, 380),
        "Multi-Agent Dynamic Orchestration Engine",
        font=sub_font,
        fill=ACCENT,
    )
    draw.text(
        (140, 510),
        "Skill 原生工作流编译 · 三档候选 Pareto 调度 · 决策可追溯",
        font=_find_font(64),
        fill=TEXT_DIM,
    )
    draw.text(
        (140, 620),
        "海聚英才 OPC 专项赛 · 极客组参赛项目",
        font=badge_font,
        fill=ACCENT_2,
    )

    # 主分割
    draw.rectangle([140, 740, PX_W - 140, 752], fill=ACCENT)

    # ============== Section 1: 核心问题 ==============
    sec_font = _find_font(96, bold=True)
    y = 820
    y = _section_title(draw, 140, y, "我们要解决的问题", sec_font)
    body_font = _find_font(54)
    y = _draw_paragraph(
        draw,
        160,
        y,
        "Agent 编排现状：\n"
        "  · 工作流靠拍脑袋，成本不可预算\n"
        "  · 失败靠重跑，决策不可追溯\n"
        "  · Skill 是文档，没法当代码管\n\n"
        "MAOE 的回答：把 Skill 变成带类型契约的胶囊，\n"
        "让编译器在动 LLM 之前算清 cost / risk / quality，\n"
        "再用 economy/balanced/quality 三档候选做 Pareto 决策。",
        body_font,
        TEXT,
        PX_W - 320,
    )

    # ============== Section 2: 架构图（手绘节点）==============
    y += 60
    y = _section_title(draw, 140, y, "系统架构", sec_font)
    arch_top = y + 30
    node_font = _find_font(48, bold=True)
    cx = PX_W // 2

    # 第 1 行：CLI
    _node(draw, cx - 380, arch_top, 760, 110, "CLI: maoe run / benchmark", node_font, ACCENT_2)

    # 第 2 行：Engine
    _node(
        draw, cx - 380, arch_top + 200, 760, 110, "MAOEEngine（运行管线总指挥）", node_font, ACCENT
    )
    _arrow(draw, cx, arch_top + 110, cx, arch_top + 200)

    # 第 3 行：六个子系统
    row3_y = arch_top + 380
    titles = ["Parser", "Evaluator", "Router", "Economist", "Executor", "Quality"]
    box_w = 470
    box_h = 130
    gap_x = 60
    total_w = box_w * 3 + gap_x * 2
    start_x = (PX_W - total_w) // 2
    for i, t in enumerate(titles[:3]):
        x = start_x + i * (box_w + gap_x)
        _node(draw, x, row3_y, box_w, box_h, t, node_font)
    for i, t in enumerate(titles[3:]):
        x = start_x + i * (box_w + gap_x)
        _node(draw, x, row3_y + box_h + 50, box_w, box_h, t, node_font)
    _arrow(draw, cx, arch_top + 310, cx, row3_y)

    # 第 4 行：LLM
    llm_y = row3_y + 2 * box_h + 130
    _node(draw, cx - 380, llm_y, 760, 110, "LLM Client → 代理 LLM API", node_font, ACCENT_2)
    _arrow(draw, cx, row3_y + 2 * box_h + 50, cx, llm_y)

    # 旁路：编译/实验/运行态
    side_y = arch_top + 200
    _node(draw, 140, side_y, 600, 110, "Compiler（GoalIR→DAG）", node_font, (180, 220, 255))
    _node(draw, 140, side_y + 200, 600, 110, "Experiments（Pareto）", node_font, (180, 220, 255))
    _node(draw, 140, side_y + 400, 600, 110, "Runtime（持久化）", node_font, (180, 220, 255))

    _node(draw, PX_W - 740, side_y, 600, 110, "Registry（Skill 注册表）", node_font, (180, 220, 255))
    _node(draw, PX_W - 740, side_y + 200, 600, 110, "Bootstrap（合规检查）", node_font, (180, 220, 255))
    _node(draw, PX_W - 740, side_y + 400, 600, 110, "Models（数据契约）", node_font, (180, 220, 255))

    y = llm_y + 200

    # ============== Section 3: 关键创新 ==============
    y += 60
    y = _section_title(draw, 140, y, "三项关键创新", sec_font)
    inn_font = _find_font(54)
    inn_title_font = _find_font(64, bold=True)

    innovations = [
        (
            "01  Skill 即类型契约",
            "每个 Skill 是 YAML 胶囊：provides / requires / schemas + risk + rollback；\n"
            "编译期就能发现 capability gap 和 schema 不匹配，避免烧钱跑错管线。",
        ),
        (
            "02  三档候选 + Pareto",
            "对每个 goal 同时编译 economy / balanced / quality 三个 DAG，\n"
            "在 (quality↑, cost↓, latency↓, risk↓) 五维 Pareto 前沿挑推荐档。",
        ),
        (
            "03  决策可复现 lockfile",
            "编译产出 sha256 lock_digest 写入 workflow.lock.json，\n"
            "Runtime 自动 redact API key 后落盘 events / decisions，做到事实可追溯。",
        ),
    ]
    for title, body in innovations:
        draw.text((160, y), title, font=inn_title_font, fill=ACCENT_2)
        y = _draw_paragraph(draw, 160, y + 80, body, inn_font, TEXT, PX_W - 320)
        y += 30

    # ============== Section 4: 指标 ==============
    y += 40
    y = _section_title(draw, 140, y, "工程现状指标", sec_font)
    metric_font = _find_font(140, bold=True)
    metric_label = _find_font(50)

    metrics = [
        ("48", "测试用例"),
        ("100%", "ruff 清洁"),
        ("10", "Skill 胶囊"),
        ("8", "Agent 角色"),
        ("3", "候选档位"),
        ("5", "静态校验"),
    ]
    mw = (PX_W - 280) // 3
    mh = 280
    for i, (num, label) in enumerate(metrics):
        row, col = divmod(i, 3)
        mx = 140 + col * mw
        my = y + row * mh
        draw.rectangle([mx + 20, my + 20, mx + mw - 20, my + mh - 20], outline=ACCENT, width=4)
        draw.text((mx + 60, my + 50), num, font=metric_font, fill=ACCENT_2)
        draw.text((mx + 60, my + 200), label, font=metric_label, fill=TEXT_DIM)
    y += 2 * mh + 40

    # ============== Footer ==============
    foot_font = _find_font(48)
    draw.rectangle([140, PX_H - 220, PX_W - 140, PX_H - 210], fill=ACCENT)
    draw.text(
        (140, PX_H - 180),
        "GitHub: github.com/<your-user>/maoe  ·  Stack: Python 3.12 / asyncio / pydantic / httpx / uv / hatchling",
        font=foot_font,
        fill=TEXT_DIM,
    )
    draw.text(
        (140, PX_H - 110),
        "tests: 48 passed in 0.4s   ·   lint: ruff All checks passed   ·   build: uv sync + hatchling wheel",
        font=foot_font,
        fill=TEXT_DIM,
    )

    img.save(OUT_PATH, format="JPEG", quality=90, optimize=True)
    print(f"poster saved: {OUT_PATH}  ({PX_W}x{PX_H}px @ {DPI} dpi)")


if __name__ == "__main__":
    build()
