#!/usr/bin/env python3
"""THE WORLD IN A DAY - Sunday 22 November 2026.

Draws a newspaper front page that sums up one day of world news and
writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Pure Python standard library: the picture is painted pixel by pixel
into a buffer at run time (masthead, a drawn lead illustration, and a
grid of 27 stories plus the lead story, 28 in all) and encoded as a
PNG with zlib.  Nothing is read from disk and no image ships in the
repository, so two runs always produce the same bytes.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (18, 18, 18)
RED = (178, 34, 34)
GREY = (90, 86, 78)
DARK = (40, 40, 40)
SUM = (70, 66, 60)
RULE = (60, 60, 60)
FAINT = (205, 198, 184)

# (tag, colour, headline, one-line summary) - the day's stories as
# reported on Sunday 22 November 2026.
STORIES = [
    ("UKRAINE", (178, 34, 34),
     "Russia's biggest November strike hits Kyiv and Lviv",
     "400+ drones, 110 missiles; at least 8 killed."),
    ("POLAND / NATO", (178, 34, 34),
     "Russian missiles land in Poland during the attack",
     "Missiles land in Poland; Tusk cries provocation."),
    ("GULF", (178, 34, 34),
     "Iran claims a new F-16 hit; US says the claim is false",
     "Tehran claims a jet hit; CENTCOM denies it."),
    ("GULF", (178, 34, 34),
     "Two tankers hit near Oman as Gulf tensions rise",
     "UK agency reports projectiles in the strait."),
    ("GAZA", (178, 34, 34),
     "Peace board warns Gaza truce is at risk of collapse",
     "Board of Peace tells UN both sides fell short."),
    ("CLIMATE", (34, 120, 60),
     "COP31 deadlocked in overtime over fossil fuels",
     "Draft drops fossil-fuel wording, $120bn target."),
    ("TRADE", (0, 110, 130),
     "EU and Indonesia sign trade deal after ten years",
     "98.5% of tariffs to go; EU saves about \u20ac650m."),
    ("DIPLOMACY", (40, 70, 160),
     "After Shenzhen, a symbolic declaration and no deal",
     "Trilateral ends with a four-point declaration."),
    ("MEXICO", (120, 60, 160),
     "Mexico captures FBI most-wanted 'El Chapo Isidro'",
     "Sinaloa raid kills 11; boss faces US charges."),
    ("PERU", (200, 110, 0),
     "Magnitude 6.7 quake shakes Peru's Andes",
     "No damage or casualties reported at first."),
    ("ASIA", (200, 110, 0),
     "Magnitude 6.8 quake strikes off Timor-Leste",
     "Second strong quake of the day; no tsunami alert."),
    ("BRAZIL", (120, 60, 160),
     "Bolsonaro taken to intensive care in Brasilia",
     "Ex-president, 71, in ICU with bowel obstruction."),
    ("HONG KONG", (40, 70, 160),
     "Voting opens for Hong Kong's Election Committee",
     "About 5,700 voters choose the powerful committee."),
    ("ESTONIA", (40, 70, 160),
     "Estonia to shut its border with Russia",
     "Follows alleged sabotage bid on a drone maker."),
    ("BALTIC", (178, 34, 34),
     "Drones hit a Russian cargo ship in the Gulf of Finland",
     "Vessel on fire, drifts into Finnish waters."),
    ("FINLAND", (40, 70, 160),
     "Finland reports suspected Russian helicopter incursion",
     "Helicopter flew 4.1 km into Finnish airspace."),
    ("INDIA", (0, 110, 130),
     "Modi opens Nitish Setu bridge linking Patna and Vaishali",
     "Bridge opens; Cyclone Akvan cancels flights."),
    ("INDIA / JAPAN", (0, 110, 130),
     "Japanese troops to train live-fire in India for first time",
     "A first for Japan's forces; defence ties deepen."),
    ("GERMANY", (40, 70, 160),
     "Berlin meeting rallies allies to push Moscow to talks",
     "Allies send Moscow a united message on talks."),
    ("USA / CANADA", (40, 70, 160),
     "Pentagon limits 'social activities' with Canada's military",
     "Hegseth sets fresh boundaries on the ties."),
    ("USA", (120, 60, 160),
     "FBI investigates apparent hack of its crime database",
     "Bureau probes breach first reported on Sunday."),
    ("USA", (120, 60, 160),
     "US airlines warned of terror threat before Thanksgiving",
     "Alert cites possible al-Qaeda-linked plot."),
    ("MARKETS", (0, 110, 130),
     "Oil prices fall more than 3% on the day",
     "Crude futures slide despite rising Gulf tensions."),
    ("SPORT", (34, 120, 60),
     "England thrash the All Blacks 37-12 at Twickenham",
     "A record defeat for New Zealand at Twickenham."),
    ("SPORT", (34, 120, 60),
     "Ireland edge world champions South Africa in a thriller",
     "A late finish seals a famous home win."),
    ("SPORT", (34, 120, 60),
     "Arsenal six points clear after draw at Newcastle",
     "Leeds win at Chelsea for first time since 1999."),
    ("CULTURE", (120, 60, 160),
     "Spitting Image co-creator Peter Fluck dies at 85",
     "The satirist behind the show's famous caricatures."),
]

LEAD_TAG = "MIDDLE EAST - LEAD STORY"
LEAD_HEAD = "Iran's drones strike at a US base in Bahrain"
LEAD_DEK = ("Iran's Revolutionary Guards say six drones targeted a US "
            "air-defence radar at the Al-Riffa helicopter base early on "
            "Sunday. Bahrain says its defences intercepted the attack; "
            "the US military reports no casualties and no damage.")
LEAD_CAP = "Dawn over the Gulf: drones above a coastal radar station. Illustration."

# ---------------------------------------------------------------------
# A 5x7 pixel font.  Each glyph is 7 rows of 5 characters; '#' is ink.
# ---------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".###."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".###.", "#....", "#....", "#....", ".###."),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", "####.", ".#...", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#..#", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".####", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "\u20ac": ("..###", ".#...", "####.", ".#...", "####.", ".#...", "..###"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
}


# ---------------------------------------------------------------------
# Pixel canvas
# ---------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(col)

    def rect(self, x, y, w, h, col):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, col, thick=1):
        self.rect(x, y, w, thick, col)

    def vline(self, x, y, h, col, thick=1):
        self.rect(x, y, thick, h, col)

    def circle(self, cx, cy, r, col):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            for xx in range(cx - r, cx + r + 1):
                dx = xx - cx
                if dx * dx + dy * dy <= r2:
                    self.set(xx, yy, col)

    def line(self, x0, y0, x1, y1, col, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x, y, thick, thick, col)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def poly(self, pts, col):
        """Filled polygon by scanline over the point list."""
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            nodes = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    nodes.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                self.hline(int(nodes[i]), yy,
                           int(nodes[i + 1]) - int(nodes[i]) + 1, col)


# ---------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def text(cv, x, y, s, scale, col):
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "#":
                    cv.rect(x + gx * scale, y + gy * scale, scale, scale, col)
        x += 6 * scale
    return x


def text_c(cv, cx, y, s, scale, col):
    return text(cv, cx - text_w(s, scale) // 2, y, s, scale, col)


def text_r(cv, xr, y, s, scale, col):
    return text(cv, xr - text_w(s, scale), y, s, scale, col)


def wrap(s, scale, width):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if text_w(trial, scale) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(s, scale, width, max_lines):
    lines = wrap(s, scale, width)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    last = lines[-1]
    while last and text_w(last + "...", scale) > width:
        last = last[:-1].rstrip()
    lines[-1] = last + "..."
    return lines


# ---------------------------------------------------------------------
# PNG writer (filter 0 scanlines, zlib level 9)
# ---------------------------------------------------------------------
def encode_png(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------------
# Lead illustration: dawn over the Gulf, drawn at run time.
# Flat shapes only - a sky in bands, a low sun, a coastal radar
# station on a headland, three drones, and the sea.
# ---------------------------------------------------------------------
def drone(cv, cx, cy, col):
    cv.rect(cx - 8, cy - 2, 17, 5, col)          # body
    cv.hline(cx - 13, cy - 5, 7, col, 2)         # rotor arms
    cv.hline(cx + 7, cy - 5, 7, col, 2)
    cv.line(cx - 5, cy + 3, cx - 8, cy + 7, col, 2)   # legs
    cv.line(cx + 5, cy + 3, cx + 8, cy + 7, col, 2)
    cv.set(cx - 16, cy + 2, col)                 # trail dots
    cv.set(cx - 20, cy + 4, col)
    cv.set(cx - 24, cy + 6, col)


def lead_art(cv, x, y, w, h):
    sea_h = 36
    horizon = y + h - sea_h
    bands = [(43, 50, 96), (74, 74, 120), (120, 96, 128),
             (178, 116, 102), (226, 156, 92)]
    sky_h = h - sea_h
    bh = sky_h // len(bands) + 1
    for i, col in enumerate(bands):
        cv.rect(x, y + i * bh, w, bh, col)
    # Sun, low over the water.
    cv.circle(x + 330, horizon - 14, 17, (246, 199, 94))
    cv.circle(x + 330, horizon - 14, 10, (250, 220, 140))
    # Headland silhouette with a raised platform for the radar.
    cv.poly([(x, horizon), (x + 150, horizon), (x + 190, horizon - 8),
             (x + 300, horizon - 8), (x + 340, horizon), (x + w, horizon),
             (x + w, horizon + 2), (x, horizon + 2)], (24, 26, 36))
    cv.rect(x + 205, horizon - 12, 70, 12, (24, 26, 36))
    # Radar dome on its base, and a mast with a slanted scanner bar.
    cv.rect(x + 224, horizon - 14, 32, 4, (24, 26, 36))
    cv.circle(x + 240, horizon - 24, 13, (203, 208, 218))
    cv.rect(x + 227, horizon - 24, 26, 12, (203, 208, 218))
    cv.vline(x + 239, horizon - 66, 30, (24, 26, 36), 3)
    cv.line(x + 226, horizon - 58, x + 254, horizon - 70, (24, 26, 36), 3)
    # Drones crossing the dawn sky.
    drone(cv, x + 74, y + 30, (16, 16, 24))
    drone(cv, x + 138, y + 54, (16, 16, 24))
    drone(cv, x + 296, y + 24, (16, 16, 24))
    # Two birds, far right.
    for bx, by in ((x + 384, y + 22), (x + 402, y + 32)):
        cv.line(bx - 5, by, bx, by + 3, (30, 30, 40), 2)
        cv.line(bx, by + 3, bx + 5, by, (30, 30, 40), 2)
    # The sea.
    cv.rect(x, horizon, w, sea_h, (46, 78, 104))
    for dx, dy in ((40, 8), (120, 20), (210, 12), (330, 24), (392, 8)):
        cv.hline(x + dx, horizon + dy, 26, (120, 160, 180), 2)
    # Sun path glitter.
    for i in range(4):
        cv.hline(x + 318 + i * 3, horizon + 6 + i * 7, 24 - i * 4,
                 (246, 199, 94), 2)
    # Frame.
    cv.hline(x, y, w, INK, 2)
    cv.hline(x, y + h - 2, w, INK, 2)
    cv.vline(x, y, h, INK, 2)
    cv.vline(x + w - 2, y, h, INK, 2)


# ---------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------
def draw_page():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(30, 24, 964, 4, RED)
    text_c(cv, 512, 38, "THE WORLD IN A DAY", 6, INK)
    text_c(cv, 512, 92, "SUNDAY, 22 NOVEMBER 2026", 2, RED)
    text_c(cv, 512, 114, "ONE DAY OF WORLD NEWS - 28 STORIES FROM EVERY CONTINENT",
           1, GREY)
    cv.hline(30, 132, 964, RULE, 2)

    # Lead story: illustration left, words right.
    lead_art(cv, 30, 146, 440, 136)
    for i, line in enumerate(wrap(LEAD_CAP, 1, 440)):
        text(cv, 30, 288 + i * 9, line, 1, GREY)
    tx, tw = 486, 508
    text(cv, tx, 146, LEAD_TAG, 2, RED)
    y = 168
    for line in wrap(LEAD_HEAD, 3, tw):
        text(cv, tx, y, line, 3, INK)
        y += 23
    y += 6
    for line in wrap(LEAD_DEK, 1, tw):
        text(cv, tx, y, line, 1, DARK)
        y += 10
    cv.hline(30, 316, 964, RULE, 2)

    # Story grid: 3 columns x 9 rows.
    gx, gy, col_w, row_h = 30, 330, 304, 72
    for sep_x in (347, 677):
        cv.vline(sep_x, gy, 9 * row_h, FAINT, 1)
    for r in range(1, 9):
        cv.hline(30, gy + r * row_h - 5, 964, FAINT, 1)
    for idx, (tag, colour, head, summ) in enumerate(STORIES):
        cx = gx + (idx % 3) * (col_w + 26)
        cy = gy + (idx // 3) * row_h
        cv.rect(cx, cy + 1, 8, 8, colour)
        text(cv, cx + 13, cy + 1, tag, 1, colour)
        hy = cy + 13
        for line in fit(head, 2, col_w, 3):
            text(cv, cx, hy, line, 2, INK)
            hy += 16
        text(cv, cx, cy + 63, fit(summ, 1, col_w, 1)[0], 1, SUM)

    # Footer.
    fy = 988
    cv.hline(30, fy, 964, RULE, 1)
    text(cv, 30, fy + 8,
         "All stories as reported on Sunday 22 November 2026. Lead picture drawn by the program.",
         1, GREY)
    text_r(cv, 994, fy + 8, "THE WORLD IN A DAY", 1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(draw_page())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
