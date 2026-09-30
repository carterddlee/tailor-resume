"""Render resume JSON files into PDFs that match base/Resume.pdf.

Usage:
  python3 build_resume.py                    # builds every output/*/resume.json
  python3 build_resume.py path/to/resume.json [...]

Layout (fonts, sizes, colors, spacing) was measured from base/Resume.pdf, which
was exported from LibreOffice with Carlito. Spacing uses the same model Writer
does: baseline gap = descent(prev) + space_after(prev) + space_before(next) + ascent(next).
"""
import glob
import json
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_DIR = Path(__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Carlito", FONT_DIR / "Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Carlito-Bold", FONT_DIR / "Carlito-Bold.ttf"))
REG, BOLD = "Carlito", "Carlito-Bold"

PAGE_W, PAGE_H = 612, 792
LEFT, RIGHT, TOP, BOTTOM = 45, 567, 36, 756
DATE_RIGHT = 496.35      # right edge of right-aligned dates
BULLET_INDENT = 13       # text starts at LEFT + 13
ASC, LEAD = 0.952, 1.2207  # Carlito ascent and line height, in em

TEXT = HexColor("#222222")
GRAY = HexColor("#555555")
ACCENT = HexColor("#1F3A5F")

# Paragraph styles: font, size, color, space_before, space_after
STYLES = {
    "name":    (BOLD, 17, TEXT, 0, 2),
    "contact": (REG, 9, GRAY, 0, 2.5),
    "header":  (BOLD, 11, ACCENT, 4.5, 5.0),  # space_after includes the rule
    "title":   (BOLD, 10, TEXT, 1.5, 1),
    "body":    (REG, 9.5, TEXT, 0.5, 2),
    "bullet":  (REG, 9.5, TEXT, 0, 2),
    "gray":    (REG, 9, GRAY, 0, 2),
}


class Page:
    def __init__(self, out_path):
        self.c = canvas.Canvas(str(out_path), pagesize=(PAGE_W, PAGE_H))
        self.prev = None  # (descent, space_after) of the previous paragraph
        self.y = TOP      # top-down y of the previous paragraph's last baseline

    def _baseline(self, style, first_line):
        _, size, _, before, _ = STYLES[style]
        if self.prev is None:
            return TOP + ASC * size
        if not first_line:
            return self.y + LEAD * size
        desc, after = self.prev
        return self.y + desc + after + before + ASC * size

    def _done(self, style):
        _, size, _, _, after = STYLES[style]
        self.prev = ((LEAD - ASC) * size, after)

    def _draw(self, x, y, text, font, size, color, align="left"):
        if y > BOTTOM:
            raise ValueError(f"resume is longer than one page (overflows at: {text[:40]!r}); cut content")
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        py = PAGE_H - y
        if align == "right":
            self.c.drawRightString(x, py, text)
        elif align == "center":
            self.c.drawCentredString(x, py, text)
        else:
            self.c.drawString(x, py, text)

    def paragraph(self, style, runs, x=LEFT + 0.1, width=None, align="left"):
        """runs: list of (text, font). Wraps greedily at spaces, like Writer."""
        _, size, color, _, _ = STYLES[style]
        width = width or RIGHT - x
        for i, line in enumerate(wrap(runs, size, width)):
            self.y = self._baseline(style, first_line=i == 0)
            if align == "center":
                text = "".join(t for t, _ in line)
                self._draw(PAGE_W / 2, self.y, text, line[0][1], size, color, "center")
                continue
            cx = x
            for text, font in line:
                self._draw(cx, self.y, text, font, size, color)
                cx += pdfmetrics.stringWidth(text, font, size)
        self._done(style)

    def header(self, text):
        self.paragraph("header", [(text.upper(), BOLD)])
        rule_y = PAGE_H - (self.y + 5.43)
        self.c.setStrokeColor(ACCENT)
        self.c.setLineWidth(1)
        self.c.line(LEFT, rule_y, RIGHT - 0.05, rule_y)

    def title(self, left, right):
        self.paragraph("title", [(left, BOLD)])
        if right:
            self._draw(DATE_RIGHT, self.y, right, REG, 9, GRAY, "right")

    def bullets(self, items):
        for text in items:
            self.y = self._baseline("bullet", first_line=True)
            self._draw(LEFT + 0.1, self.y, "•", REG, 9.5, ACCENT)
            # Draw the text lines ourselves so the bullet shares the first baseline.
            _, size, color, _, _ = STYLES["bullet"]
            for i, line in enumerate(wrap([(text, REG)], size, RIGHT - LEFT - BULLET_INDENT)):
                if i:
                    self.y += LEAD * size
                self._draw(LEFT + BULLET_INDENT + 0.1, self.y, "".join(t for t, _ in line), REG, size, color)
            self._done("bullet")

    def save(self):
        self.c.save()


def wrap(runs, size, width):
    """Split runs into lines of (text, font) pieces no wider than width."""
    words = []  # (word, font, trailing_space)
    for text, font in runs:
        parts = text.split(" ")
        for j, w in enumerate(parts):
            words.append((w, font, j < len(parts) - 1))
    lines, line, used = [], [], 0.0
    for w, font, space in words:
        w_width = pdfmetrics.stringWidth(w, font, size)
        if line and used + w_width > width and w:
            lines.append(line)
            line, used = [], 0.0
        piece = w + (" " if space else "")
        if line and line[-1][1] == font:
            line[-1] = (line[-1][0] + piece, font)
        else:
            line.append((piece, font))
        used += pdfmetrics.stringWidth(piece, font, size)
    if line:
        lines.append(line)
    return [[(t.rstrip(" ") if k == len(l) - 1 else t, f) for k, (t, f) in enumerate(l)] for l in lines]


def join_skills(items):
    """Join with commas, or semicolons if an item has its own comma outside parentheses."""
    def bare_comma(item):
        depth = 0
        for ch in item:
            depth += (ch == "(") - (ch == ")")
            if ch == "," and depth == 0:
                return True
        return False
    return ("; " if any(bare_comma(i) for i in items) else ", ").join(items)


def build(data, out_path):
    page = Page(out_path)
    page.paragraph("name", [(data["name"], BOLD)], align="center")
    page.paragraph("contact", [("  ·  ".join(data.get("contact", [])), REG)], align="center")

    if data.get("summary"):
        page.header("Summary")
        page.paragraph("body", [(data["summary"], REG)])

    if data.get("experience"):
        page.header("Experience")
        for job in data["experience"]:
            page.title(f"{job['title']}  |  {job['company']}", job.get("dates", ""))
            page.bullets(job.get("bullets", []))

    if data.get("education"):
        page.header("Education")
        for ed in data["education"]:
            page.title(f"{ed['degree']}  |  {ed['school']}", ed.get("dates", ""))
            if ed.get("details"):
                page.paragraph("gray", [(ed["details"], REG)])

    # Each entry: name, org, dates, and a gray description and/or bullets.
    if data.get("certifications_projects"):
        page.header("Certifications / Projects")
        for item in data["certifications_projects"]:
            left = item["name"] + (f"  |  {item['org']}" if item.get("org") else "")
            page.title(left, item.get("dates", ""))
            if item.get("description"):
                page.paragraph("gray", [(item["description"], REG)])
            page.bullets(item.get("bullets", []))

    if data.get("skills"):
        page.header("Skills")
        for group, items in data["skills"].items():
            page.paragraph("body", [(f"{group}: ", BOLD), (join_skills(items), REG)])

    page.save()


def main():
    paths = sys.argv[1:] or glob.glob("output/*/resume.json")
    if not paths:
        print("No resume.json files found in output/.")
        return
    for path in paths:
        path = Path(path)
        try:
            data = json.loads(path.read_text())
            out = path.parent / f"{path.parent.name}-resume.pdf"
            build(data, out)
            print(f"OK   {out}")
        except Exception as e:
            print(f"FAIL {path}: {e}")


if __name__ == "__main__":
    main()
