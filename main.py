#!/usr/bin/env python3
"""news-image-20261127 - Friday 27 November 2026, the world in one page.
Stdlib only (struct, zlib, math, os, sys). No time, no randomness, no network.
Deterministic: repeated runs produce a byte-identical entry.png.
Draws a 1024x1024 broadsheet PNG with a hand-rolled encoder and an
embedded 5x7 bitmap font. All art is original vector drawing in code.
"""
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# --- palette ---
CREAM = (247, 241, 222)
PAPER = (252, 248, 236)
INK = (26, 26, 26)
RED = (179, 35, 27)
NAVY = (31, 58, 95)
MUTED = (107, 98, 82)
GOLD = (201, 162, 39)
GREEN = (46, 125, 50)
SKY = (135, 180, 210)
SAGE = (168, 178, 140)
WHITE = (255, 255, 255)
DARKRED = (122, 22, 16)

# --- 5x7 bitmap font: each glyph is 7 rows of 5 bits (MSB = left pixel) ---
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '-': (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '@': (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    '_': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
}


def _chunk(tag, data):
    out = struct.pack('>I', len(data)) + tag + data
    out += struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def png_bytes(w, h, rgb):
    """Encode an RGB bytearray as a PNG (8-bit, no interlace)."""
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr)
            + _chunk(b'IDAT', idat) + _chunk(b'IEND', b''))


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def border(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                    self.set(xx, yy, c)

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, c):
        return self.text(cx - self.text_w(s, scale) // 2, y, s, scale, c)

    def wrap(self, s, max_w, scale):
        words = s.upper().split(' ')
        lines, cur = [], ''
        for wd in words:
            trial = (cur + ' ' + wd).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, lines, scale, leading, c):
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += leading
        return y


# --- original vector illustrations (all drawn in code, no photos) ---

def draw_bag(cv, x, y, w, h):
    """Shopping bag with a SALE tag."""
    cv.rect(x + 8, y + 22, w - 16, h - 22, RED)
    cv.rect(x + 8, y + 22, w - 16, 6, DARKRED)
    # handles
    cv.line(x + w // 3, y + 22, x + w // 3, y + 8, INK, 3)
    cv.line(x + 2 * w // 3, y + 22, x + 2 * w // 3, y + 8, INK, 3)
    cv.line(x + w // 3, y + 8, x + 2 * w // 3, y + 8, INK, 3)
    # tag
    tx, ty = x + w - 62, y + h - 46
    cv.rect(tx, ty, 56, 30, GOLD)
    cv.border(tx, ty, 56, 30, INK, 2)
    cv.text(tx + 4, ty + 8, 'SALE', 2, INK)


def draw_ballot(cv, x, y, w, h):
    """Ballot box with a paper going in and a check mark."""
    cv.rect(x + 10, y + 42, w - 20, h - 42, NAVY)
    cv.rect(x + 10, y + 42, w - 20, 8, (20, 42, 72))
    cv.rect(x + w // 2 - 34, y + 34, 68, 10, INK)
    # ballot paper sliding into the slot
    cv.rect(x + w // 2 - 26, y + 2, 52, 40, PAPER)
    cv.border(x + w // 2 - 26, y + 2, 52, 40, INK, 2)
    cv.line(x + w // 2 - 18, y + 12, x + w // 2 - 6, y + 24, GREEN, 3)
    cv.line(x + w // 2 - 6, y + 24, x + w // 2 + 18, y + 6, GREEN, 3)
    # big tick on the box front
    cv.line(x + 110, y + 70, x + 140, y + 88, WHITE, 4)
    cv.line(x + 140, y + 88, x + 220, y + 52, WHITE, 4)


def draw_chess(cv, x, y, w, h):
    """4x4 chess board with a king and a pawn."""
    sq = min(w, h) // 4
    bx, by = x + (w - sq * 4) // 2, y + (h - sq * 4) // 2
    for r in range(4):
        for c in range(4):
            col = PAPER if (r + c) % 2 == 0 else NAVY
            cv.rect(bx + c * sq, by + r * sq, sq, sq, col)
    cv.border(bx, by, sq * 4, sq * 4, INK, 2)
    # king on a light square
    kx, ky = bx + sq + sq // 2, by + sq // 2
    cv.circle(kx, ky + 2, sq // 2 - 2, GOLD)
    cv.border(kx - sq // 2 + 2, ky - sq // 2 + 2, sq - 4, sq - 4, INK, 1)
    cv.text(kx - 3, ky - 11, '+', 2, INK)
    # pawn on a dark square
    px, py = bx + 2 * sq + sq // 2, by + 2 * sq + sq // 2
    cv.circle(px, py - 2, sq // 3, RED)
    cv.rect(px - sq // 3, py + 2, 2 * sq // 3, sq // 4, RED)


def draw_cricket(cv, x, y, w, h):
    """Cricket bat, ball and stumps."""
    # stumps
    sx = x + 16
    for i in range(3):
        cv.rect(sx + i * 10, y + h - 52, 5, 52, GOLD)
    cv.rect(sx - 2, y + h - 56, 34, 5, GOLD)
    # bat leaning
    cv.line(x + w - 46, y + 8, x + w - 26, y + h - 20, INK, 3)
    cv.rect(x + w - 52, y + h - 62, 26, 44, (214, 164, 92))
    cv.border(x + w - 52, y + h - 62, 26, 44, INK, 2)
    # ball
    cv.circle(x + w - 22, y + 26, 13, RED)
    cv.circle(x + w - 26, y + 22, 4, WHITE)


def draw_film(cv, x, y, w, h):
    """Film reel and strip."""
    cx, cy = x + w // 2 - 12, y + h // 2
    cv.circle(cx, cy, 34, NAVY)
    cv.circle(cx, cy, 34, INK, fill=False)
    cv.circle(cx, cy, 8, PAPER)
    for ang in range(0, 360, 72):
        a = math.radians(ang)
        cv.circle(int(cx + 20 * math.cos(a)), int(cy + 20 * math.sin(a)),
                  6, PAPER)
    # film strip
    fx = x + w - 34
    cv.rect(fx, y + 6, 26, h - 12, INK)
    for i in range(4):
        cv.rect(fx + 4, y + 12 + i * ((h - 24) // 4), 18, 10, PAPER)


def draw_chart(cv, x, y, w, h):
    """Rising market chart with bars and an arrow (scales to its box)."""
    vals = [18, 30, 24, 42, 36, 56, 72]
    n = len(vals)
    step = max(4, (w - 8) // n)
    bw = max(3, step - 3)
    top = y + 10
    base = y + h - 6
    vmax = max(vals)
    pts = []
    for i, v in enumerate(vals):
        bh = int((base - top) * v / vmax)
        bx = x + 4 + i * step
        cv.rect(bx, base - bh, bw, bh, NAVY if i % 2 else RED)
        pts.append((bx + bw // 2, base - bh - 4))
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], GREEN, 3)
    ex, ey = pts[-1]
    cv.line(ex, ey, ex - 10, ey + 2, GREEN, 3)
    cv.line(ex, ey, ex - 2, ey + 10, GREEN, 3)


# --- stylised world map (equirectangular, lon -180..180, lat 75..-60) ---

def map_xy(mx, my, mw, mh, lon, lat):
    x = mx + int((lon + 180.0) / 360.0 * mw)
    y = my + int((75.0 - lat) / 135.0 * mh)
    return x, y


def draw_map(cv, mx, my, mw, mh):
    cv.rect(mx, my, mw, mh, (232, 240, 244))
    cv.border(mx, my, mw, mh, INK, 2)
    # continents as overlapping ellipses (stylised, not to scale)
    blobs = [
        (120, 40, 70, 26), (185, 58, 52, 24), (95, 66, 42, 18),   # N America
        (255, 16, 20, 10),                                          # Greenland
        (272, 96, 30, 34), (288, 122, 22, 24),                     # S America
        (332, 26, 26, 14), (352, 36, 20, 12), (322, 20, 6, 8),     # Europe+UK
        (342, 82, 36, 38), (356, 112, 28, 28),                     # Africa
        (452, 42, 112, 34), (522, 62, 82, 30), (602, 46, 52, 24),  # Asia
        (586, 132, 36, 14),                                         # Australia
        (628, 142, 8, 12),                                          # New Zealand
    ]
    for (cx, cy, rx, ry) in blobs:
        cv.ellipse(mx + cx * mw // 636, my + cy * mh // 164,
                   max(2, rx * mw // 636), max(2, ry * mh // 164), SAGE)
    # pins: (number, lon, lat, nudge_x, nudge_y)
    pins = [
        (1, -74.0, 40.7, 0, 0),      # New York
        (2, 174.8, -41.3, 6, -4),    # Wellington
        (3, 6.1, 46.2, 0, 0),        # Geneva
        (4, 172.6, -43.5, -10, 6),   # Christchurch
        (5, 72.8, 19.1, 0, 0),       # Mumbai
        (6, 139.7, 35.7, 0, 0),      # Tokyo
    ]
    for num, lon, lat, nx, ny in pins:
        px, py = map_xy(mx, my, mw, mh, lon, lat)
        px += nx
        py += ny
        cv.circle(px, py, 11, RED)
        cv.circle(px, py, 11, INK, fill=False)
        cv.text(px - 3, py - 6, str(num), 2, WHITE)
    return pins


# --- layout ---

def hero_panel(cv, x, y, w, h, num, cat, title, body, draw_fn):
    cv.border(x, y, w, h, INK, 2)
    cv.rect(x, y, w, 26, NAVY)
    cv.text(x + 10, y + 6, num + ' | ' + cat, 2, WHITE)
    draw_fn(cv, x + 8, y + 34, w - 16, 96)
    scale = 4
    lines = cv.wrap(title, w - 20, scale)
    if len(lines) > 2:
        scale = 3
        lines = cv.wrap(title, w - 20, scale)
    lead = 8 * scale + 2
    ty = y + 138
    for ln in lines:
        cv.text(x + 10, ty, ln, scale, INK)
        ty += lead
    by = ty + 4
    wrapped = []
    for ln in body:
        wrapped.extend(cv.wrap(ln, w - 20, 2))
    for ln in wrapped:
        cv.text(x + 10, by, ln, 2, INK)
        by += 17


def tile_panel(cv, x, y, w, h, num, cat, title, body, draw_fn):
    cv.border(x, y, w, h, INK, 2)
    cv.rect(x, y, w, 26, RED)
    cv.text(x + 10, y + 6, num + ' | ' + cat, 2, WHITE)
    lines = cv.wrap(title, w - 20, 3)
    ty = y + 32
    for ln in lines:
        cv.text(x + 10, ty, ln, 3, INK)
        ty += 23
    iy = ty + 4
    draw_fn(cv, x + 8, iy, 88, h - (iy - y) - 8)
    bx = x + 104
    by = iy + 2
    wrapped = []
    for ln in body:
        wrapped.extend(cv.wrap(ln, w - 112, 2))
    for ln in wrapped:
        cv.text(bx, by, ln, 2, INK)
        by += 16


def build():
    cv = Canvas(W, H, CREAM)
    cv.border(8, 8, W - 16, H - 16, INK, 2)
    cv.border(14, 14, W - 28, H - 28, INK, 1)

    # masthead
    cv.text_center(W // 2, 30, 'THE WORLD IN ONE PAGE', 2, MUTED)
    cv.text_center(W // 2, 56, 'FRIDAY 27 NOVEMBER 2026', 6, INK)
    cv.hline(24, 1000, 106, RED, 3)
    cv.text_center(W // 2, 114,
                   '6 STORIES | 4 REGIONS | 5 FIELDS - ALL FROM TODAY, '
                   '27 NOVEMBER 2026', 2, RED)

    # UTC timeline strip
    cv.rect(24, 136, 976, 22, NAVY)
    cv.text_center(W // 2, 141,
                   '01:00 UTC - NZ FINAL RESULTS DUE  |  11:00 UTC - BLACK '
                   'FRIDAY DOORS OPEN  |  14:00 UTC - CHESS GAME 4, GENEVA  '
                   '|  ALL DAY - BLACK FRIDAY SALES', 1, WHITE)

    # numbers strip
    cv.text_center(W // 2, 166,
                   'NUMBERS: 6 STORIES | 67/131 SEATS | TOP CARD $1,000 | '
                   '1.5-1.5 | RS 4.80 CR', 2, INK)
    cv.hline(24, 1000, 190, INK, 2)

    # heroes
    hw = 312
    hero_panel(cv, 24, 196, hw, 274, '01', 'RETAIL',
               'BLACK FRIDAY BEGINS',
               ['DOORS OPEN 6AM AT',
                'TARGET, BEST BUY,',
                'WALMART. FIRST 100',
                'GIFT CARDS, ONE $1,000'],
               draw_bag)
    hero_panel(cv, 356, 196, hw, 274, '02', 'POLITICS',
               'NEW ZEALAND DECIDES',
               ['FINAL RESULTS DUE TODAY,',
                '2PM NZDT. INTERIM COUNT:',
                'COALITION 67/131 SEATS.',
                '400,000 SPECIAL VOTES.'],
               draw_ballot)
    hero_panel(cv, 688, 196, hw, 274, '03', 'CHESS',
               'GAME 4 TODAY IN GENEVA',
               ['MATCH LEVEL 1.5-1.5',
                'AFTER THREE DRAWS.',
                'GAME 4 AT 15:00 CET',
                'IN GENEVA.'],
               draw_chess)

    # tiles
    tile_panel(cv, 24, 478, hw, 168, '04', 'CRICKET',
               'SECOND TEST STARTS TODAY',
               ['INDIA V NEW ZEALAND, CHRISTCHURCH, 11AM NZDT.'],
               draw_cricket)
    tile_panel(cv, 356, 478, hw, 168, '05', 'CINEMA',
               'RAMAYANA NEARS 1,000 CRORE',
               ['FRIDAY ADVANCE BOOKINGS RS 4.80 CRORE WORLDWIDE. '
                '(REPORTED: ONE TRACKER)'],
               draw_film)
    tile_panel(cv, 688, 478, hw, 168, '06', 'MARKETS',
               'WALL STREET REOPENS',
               ['SHORTENED SESSION, CLOSES 1PM ET. NIKKEI +0.4% IN '
                'EARLY FRIDAY TRADE.'],
               draw_chart)

    # map + pin legend
    cv.text(24, 654, 'WHERE IT HAPPENED', 2, RED)
    draw_map(cv, 24, 676, 636, 136)
    legend = [
        (1, 'NEW YORK - BLACK FRIDAY'),
        (2, 'WELLINGTON - ELECTION'),
        (3, 'GENEVA - CHESS GAME 4'),
        (4, 'CHRISTCHURCH - 2ND TEST'),
        (5, 'MUMBAI - RAMAYANA'),
        (6, 'TOKYO - ASIAN MARKETS'),
    ]
    ly = 676
    for num, label in legend:
        cv.rect(672, ly, 20, 20, RED)
        cv.text(672 + 7, ly + 3, str(num), 2, WHITE)
        cv.text(700, ly + 3, label, 2, INK)
        ly += 23

    # DATE CHECK
    cv.border(24, 826, 976, 120, INK, 2)
    cv.text(32, 832, 'DATE CHECK - NOT TODAY, SO NOT IN THIS PAGE', 2, RED)
    left = [
        '- KUWAIT DRONE ATTACK, 2 ITALIANS KILLED - THU 26 NOV',
        '- TRUMP TELLS PUTIN TO PULL BACK - THU 26 NOV',
        '- JAZAN REFINERY ATTACK, 1 KILLED - THU 26 NOV',
        '- THANKSGIVING STORM, PARADE POSTPONED - THU 26 NOV',
        '- NFL THANKSGIVING RESULTS - THU 26 NOV',
        '- LILLE BEAT BAYERN - THU 26 NOV EVENING',
        '- ZELENSKY BBC INTERVIEW - PUBLISHED THU 26 NOV',
        '- UK NET MIGRATION 77,000, LOWEST SINCE 1997 - THU 26 NOV',
    ]
    right = [
        '- HAMAS WEIGHS RESPONSE, 10 KILLED IN GAZA - THU 26 NOV',
        '- DE COS PICKED AS NEXT ECB PRESIDENT - THU 26 NOV',
        '- MANDELSON FILES RELEASED - THU 26 NOV',
        '- CIA WATERBOARDING REPORT (NYT) - THU 26 NOV',
        '- PERU BURNS 10.7 TONNES OF DRUGS - THU 26 NOV',
        '- MARIE-ANTOINETTE BOWL SELLS EUR 2.9M - THU 26 NOV',
        '- JORDIE BARRETT NAMED ALL BLACKS CAPTAIN - THU 26 NOV',
    ]
    yy = 854
    for ln in left:
        cv.text(32, yy, ln, 1, INK)
        yy += 11
    yy = 854
    for ln in right:
        cv.text(516, yy, ln, 1, INK)
        yy += 11

    # footer
    cv.text_center(W // 2, 954,
                   'NOT YET: NZ FINAL RESULTS (2PM NZDT) - CHESS GAME 4 '
                   '(3PM CET) - 2ND TEST (11AM NZDT). NO RESULTS AT PRESS '
                   'TIME.', 1, MUTED)
    cv.text_center(W // 2, 970,
                   'CONFIRMED = 2+ OUTLETS | OFFICIAL = ON THE RECORD | '
                   'REPORTED = ONE OUTLET | CLAIM = UNVERIFIED', 1, MUTED)
    cv.text_center(W // 2, 986,
                   'SOURCES: REUTERS, NZ HERALD, CHESS.COM, '
                   'BOXOFFICEINDIA24, NYSE. ORIGINAL DRAWINGS. ALL STORIES '
                   'HAPPENED OR WERE FIRST REPORTED ON 27 NOVEMBER 2026.',
                   1, MUTED)
    return cv


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'entry.png'
    cv = build()
    data = png_bytes(W, H, cv.px)
    with open(out, 'wb') as f:
        f.write(data)
    print('wrote %s (%d bytes)' % (out, len(data)))


if __name__ == '__main__':
    main()
