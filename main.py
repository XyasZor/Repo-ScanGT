#!/usr/bin/env python3
# ============================================================
#   GENETIC TOOLS  v2.0.0
#   Futuristic terminal hub: SCAN REPO - analisa keamanan repository
#   Windows ┬╖ Linux ┬╖ Termux   (tanpa dependency eksternal)
#
#   Pakai interaktif :  python genetic_tools.py
#   Pakai langsung   :  python genetic_tools.py https://github.com/owner/repo
# ============================================================

import collections
import datetime
import json
import math
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

APP_NAME = "GENETIC TOOLS"
VERSION = "2.0.0"
MIN_W, MIN_H = 50, 16
FRAME = 0.04
BOOT_SECONDS = 4.0
HOME_DIR = os.path.join(os.path.expanduser("~"), ".genetic-tools")
REPORT_DIR = os.path.join(HOME_DIR, "reports")
UA = f"GeneticTools/{VERSION} (repo-scanner)"

# ---- batas keamanan & performa ----
MAX_DOWNLOAD = 200 * 1024 * 1024        # ukuran arsip maksimum
MAX_EXTRACT_TOTAL = 600 * 1024 * 1024   # total hasil ekstrak maksimum
MAX_FILES = 40000                       # jumlah berkas maksimum
MAX_FILE_EXTRACT = 12 * 1024 * 1024     # berkas lebih besar dari ini tidak diekstrak
MAX_SCAN_BYTES = 1536 * 1024            # byte pertama tiap berkas yang dipindai
SCAN_TIME_LIMIT = 300                   # detik

PRUNE_DIRS = {".git", "node_modules", ".venv", "venv", "site-packages", "bower_components"}

MENU_ITEMS = [
    {"name": "TOOLS", "icon": "Γùå", "desc": "Scan repo: analisa bahaya, risiko & isi"},
    {"name": "ABOUT", "icon": "Γùç", "desc": "Tentang Genetic Tools & fiturnya"},
    {"name": "INFORMATION", "icon": "Γùê", "desc": "Versi, status sistem & panduan"},
]

BOOT_STEPS = [
    "Mengaktifkan inti genetik",
    "Memuat mesin analisa risiko",
    "Memuat basis pola ancaman",
    "Memeriksa Git & Python",
    "Membangun antarmuka neon",
    "Sistem siap",
]

EXAMPLES = [
    "https://github.com/yt-dlp/yt-dlp",
    "https://github.com/httpie/cli",
    "github.com/pallets/flask/tree/main",
    "psf/requests",
    "https://gitlab.com/gitlab-org/cli",
    "https://codeberg.org/forgejo/forgejo",
]

GUIDE = [
    ("GitHub", "https://github.com/owner/repo"),
    ("Cabang", "github.com/owner/repo/tree/main"),
    ("Singkat", "owner/repo   (dianggap GitHub)"),
    ("GitLab", "https://gitlab.com/grup/proyek"),
    ("Bitbucket", "https://bitbucket.org/owner/repo"),
    ("Codeberg", "https://codeberg.org/owner/repo"),
    ("Git SSH", "git@github.com:owner/repo.git"),
    ("Arsip", "https://situs.com/file.zip  (.zip/.tar.gz)"),
    ("Lokal", "/path/folder    atau    C:\\proyek\\app"),
]

# ============================================================
# TERMINAL & STYLE
# ============================================================

if os.name == "nt":
    os.system("")  # aktifkan dukungan ANSI di Windows console

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

RESET = "\033[0m"
BOLD = "\033[1m"
ALT_ON, ALT_OFF = "\033[?1049h", "\033[?1049l"
HIDE_CURSOR, SHOW_CURSOR = "\033[?25l", "\033[?25h"
CLEAR_ALL = "\033[2J\033[H"


def fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def bg(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"


def out(text):
    sys.stdout.write(text)
    sys.stdout.flush()


NEON = (0, 255, 140)
CYAN = (0, 215, 255)
YELLOW = fg(255, 214, 0) + BOLD
WHITE = fg(230, 255, 238)
GREY = fg(95, 125, 112)
RED = fg(255, 95, 95)
RED_S = RED + BOLD
NEON_C = fg(*NEON)
NEON_S = NEON_C + BOLD
CYAN_S = fg(*CYAN) + BOLD
CODE_C = fg(120, 190, 255)
GREEN_DARK = fg(0, 95, 50)
HILITE_BG = bg(0, 52, 28)
HEADER_BG = bg(0, 38, 20)
HEAD_STYLE = fg(215, 255, 225) + BOLD

# tingkat bahaya: (batas atas persen, nama, warna)
LEVELS = [
    (10, "AMAN", (0, 255, 140)),
    (25, "RENDAH", (150, 255, 60)),
    (50, "SEDANG", (255, 214, 0)),
    (75, "TINGGI", (255, 140, 0)),
    (101, "KRITIS", (255, 60, 60)),
]
LEVEL_RGB = {name: rgb for _, name, rgb in LEVELS}
LEVEL_STYLE = {name: fg(*rgb) + BOLD for _, name, rgb in LEVELS}

SEV_STYLE = {
    "crit": fg(255, 60, 60) + BOLD,
    "high": fg(255, 140, 0) + BOLD,
    "med": YELLOW,
    "low": fg(150, 255, 60),
    "info": GREY,
}
SEV_LABEL = {"crit": "KRITIS", "high": "TINGGI", "med": "SEDANG", "low": "RENDAH", "info": "INFO"}
SEV_W = {"crit": 20, "high": 8, "med": 3, "low": 1, "info": 0}
SEV_ORDER = ["crit", "high", "med", "low", "info"]

KIND_STYLE = {
    "title": YELLOW,
    "h": NEON_S,
    "txt": WHITE,
    "dim": GREY,
    "ok": NEON_C,
    "code": CODE_C,
}


def level_of(pct):
    for limit, name, _ in LEVELS:
        if pct < limit:
            return name
    return "KRITIS"


def style_for(kind):
    if kind.startswith("L:"):
        return LEVEL_STYLE.get(kind[2:], WHITE)
    if kind in SEV_STYLE:
        return SEV_STYLE[kind]
    return KIND_STYLE.get(kind, WHITE)


def mix(t, a=NEON, b=CYAN):
    """Warna neon hasil campuran hijau-cyan yang berayun mengikuti waktu."""
    k = (math.sin(t) + 1) / 2
    return fg(*(int(a[i] + (b[i] - a[i]) * k) for i in range(3)))


def lerp(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def heat(k):
    """Gradasi merah -> kuning -> hijau neon (k: 0..1)."""
    red, yel, grn = (255, 70, 70), (255, 214, 0), (0, 255, 140)
    return lerp(red, yel, k * 2) if k < 0.5 else lerp(yel, grn, (k - 0.5) * 2)


def rain_palette(factor=1.0):
    tail, mid, head = (0, 30, 15), (0, 150, 75), (0, 255, 140)
    pal = []
    for i in range(10):
        t = i / 9
        if t < 0.5:
            a, b, k = tail, mid, t * 2
        else:
            a, b, k = mid, head, (t - 0.5) * 2
        pal.append(fg(*(int((a[j] + (b[j] - a[j]) * k) * factor) for j in range(3))))
    return pal


def term_size():
    s = shutil.get_terminal_size((80, 24))
    return max(1, s.columns), max(1, s.lines)


def clear_console():
    out(CLEAR_ALL)


def fmt_uptime(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{(sec // 60) % 60:02d}:{sec % 60:02d}"


def fmt_size(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


_CTRL_RE = re.compile("[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069\u200b-\u200f]")


def clean(text):
    """Buang karakter kontrol agar isi repo tidak bisa 'membajak' terminal."""
    return _CTRL_RE.sub("┬ñ", str(text))


# ============================================================
# CANVAS  -  buffer per frame, ditulis sekali (anti-flicker)
# ============================================================

class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        blank = ("", " ")
        self.cells = [[blank] * w for _ in range(h)]

    def put(self, x, y, text, style=""):
        if 0 <= y < self.h:
            row = self.cells[y]
            for i, ch in enumerate(text):
                cx = x + i
                if 0 <= cx < self.w:
                    row[cx] = (style, ch)

    def fill(self, x, y, w, h, style=""):
        for yy in range(max(0, y), min(self.h, y + h)):
            row = self.cells[yy]
            for xx in range(max(0, x), min(self.w, x + w)):
                row[xx] = (style, " ")

    def center(self, y, text, style=""):
        self.put((self.w - len(text)) // 2, y, text, style)

    def gradient(self, x, y, text, tick, extra="", spread=0.15):
        for i, ch in enumerate(text):
            if ch != " ":
                self.put(x + i, y, ch, mix(tick + i * spread) + extra)

    def frame(self):
        parts = []
        for y, row in enumerate(self.cells):
            parts.append(f"\033[{y + 1};1H")
            last = None
            for style, ch in row:
                if style != last:
                    parts.append(RESET + style)
                    last = style
                parts.append(ch)
            parts.append(RESET)
        return "".join(parts)


# ============================================================
# INPUT  -  Windows (msvcrt) / Linux & Termux (termios cbreak)
#   Teks yang diketik/ditempel dikembalikan sebagai Text (huruf
#   besar-kecil dipertahankan); tombol khusus berupa str biasa.
# ============================================================

class Text(str):
    """Karakter atau teks yang diketik (bukan tombol khusus)."""


ARROWS = {
    "[A": "UP", "[B": "DOWN", "[C": "RIGHT", "[D": "LEFT",
    "OA": "UP", "OB": "DOWN", "OC": "RIGHT", "OD": "LEFT",
    "[H": "HOME", "[F": "END", "OH": "HOME", "OF": "END",
    "[1~": "HOME", "[4~": "END", "[7~": "HOME", "[8~": "END",
    "[5~": "PGUP", "[6~": "PGDN",
}


def _flush_text(events, buf):
    if buf:
        events.append(Text("".join(buf)))
        buf.clear()


class Keys:
    def __init__(self):
        self.posix = os.name != "nt"
        self.fd = sys.stdin.fileno() if self.posix else None
        self._old = None
        self.queue = []

    def __enter__(self):
        self.resume()
        return self

    def __exit__(self, *exc):
        self.suspend()
        return False

    def resume(self):
        if self.posix:
            import termios
            import tty
            self._old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)

    def suspend(self):
        if self.posix and self._old is not None:
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)
            self._old = None

    def read(self, timeout):
        """Kembalikan satu tombol/teks, atau None bila tidak ada input dalam timeout."""
        if self.queue:
            return self.queue.pop(0)
        events = self._read_posix(timeout) if self.posix else self._read_windows(timeout)
        if not events:
            return None
        self.queue.extend(events[1:])
        return events[0]

    def _read_posix(self, timeout):
        import select
        if not select.select([self.fd], [], [], timeout)[0]:
            return []
        data = os.read(self.fd, 4096)
        if not data:
            raise KeyboardInterrupt  # stdin ditutup
        return self._parse(data.decode("utf-8", errors="ignore"))

    @staticmethod
    def _parse(s):
        events, buf = [], []
        i, n = 0, len(s)
        while i < n:
            ch = s[i]
            if ch == "\x1b":
                _flush_text(events, buf)
                if i + 1 >= n:
                    events.append("ESC")
                    i += 1
                    continue
                if s[i + 1] in "[O":
                    j = i + 2
                    while j < n and not (s[j].isalpha() or s[j] == "~"):
                        j += 1
                    name = ARROWS.get(s[i + 1:j + 1])
                    if name:
                        events.append(name)
                    i = j + 1
                    continue
                i += 2  # Alt+tombol: abaikan
                continue
            if ch in "\r\n":
                _flush_text(events, buf)
                if not (ch == "\n" and i > 0 and s[i - 1] == "\r"):
                    events.append("ENTER")
            elif ch in "\x7f\x08":
                _flush_text(events, buf)
                events.append("BACK")
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ch == "\x15":
                _flush_text(events, buf)
                events.append("CLEAR")
            elif ch.isprintable():
                buf.append(ch)
            i += 1
        _flush_text(events, buf)
        return events

    def _read_windows(self, timeout):
        import msvcrt
        end = time.time() + timeout
        while not msvcrt.kbhit():
            if time.time() >= end:
                return []
            time.sleep(0.01)
        events, buf = [], []
        special = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT",
                   "I": "PGUP", "Q": "PGDN", "G": "HOME", "O": "END"}
        while True:
            c = msvcrt.getwch()
            if c in ("\x00", "\xe0"):
                _flush_text(events, buf)
                name = special.get(msvcrt.getwch())
                if name:
                    events.append(name)
            elif c == "\r":
                _flush_text(events, buf)
                events.append("ENTER")
            elif c == "\x03":
                raise KeyboardInterrupt
            elif c == "\x1b":
                _flush_text(events, buf)
                events.append("ESC")
            elif c == "\x08":
                _flush_text(events, buf)
                events.append("BACK")
            elif c == "\x15":
                _flush_text(events, buf)
                events.append("CLEAR")
            elif c.isprintable():
                buf.append(c)
            if not msvcrt.kbhit():
                break
        _flush_text(events, buf)
        return events


# ============================================================
# MATRIX RAIN  -  angka biner hijau yang berjatuhan
# ============================================================

class Rain:
    def __init__(self, density, factor):
        self.density = density          # rata-rata aliran per kolom
        self.pal = rain_palette(factor)
        self.w = self.h = -1
        self.streams = []

    def _stream(self, x):
        n = random.randint(7, 22)
        return {
            "x": x,
            "y": -random.uniform(0, max(1, self.h)),
            "v": random.uniform(5, 18),
            "n": n,
            "bits": [random.choice("01") for _ in range(n)],
        }

    def update(self, dt, w, h):
        if (w, h) != (self.w, self.h):
            self.w, self.h = w, h
            self.streams = []
            for x in range(w):
                count = int(self.density) + (1 if random.random() < self.density % 1 else 0)
                for _ in range(count):
                    s = self._stream(x)
                    s["y"] = random.uniform(0, h)
                    self.streams.append(s)
        for s in self.streams:
            s["y"] += s["v"] * dt
            if random.random() < 0.08:
                s["bits"][random.randrange(s["n"])] = random.choice("01")
            if s["y"] - s["n"] > self.h:
                s.update(self._stream(s["x"]))

    def draw(self, cv):
        for s in self.streams:
            x = s["x"]
            if x >= cv.w:
                continue
            n = s["n"]
            head = int(s["y"])
            for i in range(n):
                y = head - i
                if 0 <= y < cv.h:
                    style = HEAD_STYLE if i == 0 else self.pal[max(0, 9 - (i * 9) // n)]
                    cv.cells[y][x] = (style, s["bits"][i])


# ============================================================
# LOGO  -  huruf blok 5 baris untuk judul
# ============================================================

BLOCK_FONT = {
    "G": [" ΓûêΓûêΓûêΓûê", "Γûê    ", "Γûê ΓûêΓûêΓûê", "Γûê   Γûê", " ΓûêΓûêΓûêΓûê"],
    "E": ["ΓûêΓûêΓûêΓûêΓûê", "Γûê    ", "ΓûêΓûêΓûêΓûê ", "Γûê    ", "ΓûêΓûêΓûêΓûêΓûê"],
    "N": ["Γûê   Γûê", "ΓûêΓûê  Γûê", "Γûê Γûê Γûê", "Γûê  ΓûêΓûê", "Γûê   Γûê"],
    "T": ["ΓûêΓûêΓûêΓûêΓûê", "  Γûê  ", "  Γûê  ", "  Γûê  ", "  Γûê  "],
    "I": ["ΓûêΓûêΓûêΓûêΓûê", "  Γûê  ", "  Γûê  ", "  Γûê  ", "ΓûêΓûêΓûêΓûêΓûê"],
    "C": [" ΓûêΓûêΓûêΓûê", "Γûê    ", "Γûê    ", "Γûê    ", " ΓûêΓûêΓûêΓûê"],
}


def logo_rows(word):
    rows = [""] * 5
    for ch in word:
        glyph = BLOCK_FONT[ch]
        for i in range(5):
            rows[i] += glyph[i] + " "
    return [r.rstrip() for r in rows]


def logo_width(word):
    return max(len(r) for r in logo_rows(word))


def draw_logo(cv, x, y, word, tick):
    for r, line in enumerate(logo_rows(word)):
        for c, ch in enumerate(line):
            if ch != " ":
                cv.put(x + c, y + r, ch, mix(tick + c * 0.13 + r * 0.3))


# ============================================================
# UI PRIMITIVES
# ============================================================

def panel(cv, x, y, w, h, title="", tick=0.0, title_style=None):
    edge = mix(tick * 0.6)
    cv.fill(x, y, w, h)
    cv.put(x, y, "Γò¡" + "ΓöÇ" * (w - 2) + "Γò«", edge)
    cv.put(x, y + h - 1, "Γò░" + "ΓöÇ" * (w - 2) + "Γò»", edge)
    for yy in range(y + 1, y + h - 1):
        cv.put(x, yy, "Γöé", edge)
        cv.put(x + w - 1, yy, "Γöé", edge)
    if title:
        cv.put(x + 2, y, f" {title} ", title_style or NEON_S)


def draw_card(cv, x, y, w, item, num, selected, tick):
    edge = mix(tick * 2.0) if selected else GREEN_DARK
    body = HILITE_BG if selected else ""
    cv.fill(x, y + 1, w, 1, body)
    cv.put(x, y, "Γò¡" + "ΓöÇ" * (w - 2) + "Γò«", edge)
    cv.put(x, y + 2, "Γò░" + "ΓöÇ" * (w - 2) + "Γò»", edge)
    cv.put(x, y + 1, "Γöé", edge)
    cv.put(x + w - 1, y + 1, "Γöé", edge)
    cv.put(x + 2, y, f" {item['icon']} {item['name']} ", YELLOW)
    cv.put(x + w - 8, y, f" {num:02d} ", GREY)
    cv.put(x + 3, y + 1, item["desc"][: w - 6], WHITE + body)
    if selected:
        cv.put(x - 2, y + 1, "Γû╢", mix(tick * 2.0))


def draw_bar(cv, x, y, w, ratio, tick):
    filled = int(w * max(0.0, min(1.0, ratio)))
    for i in range(w):
        if i < filled:
            cv.put(x + i, y, "Γûê", mix(tick + i * 0.2))
        else:
            cv.put(x + i, y, "Γûæ", GREEN_DARK)


def draw_scan_bar(cv, x, y, w, ratio, tick, done=False):
    """Loading bar berwarna: gradasi merah-kuning-hijau + kilau yang berjalan."""
    ratio = max(0.0, min(1.0, ratio))
    filled = int(round(w * ratio))
    sweep = (tick * 9) % (max(1, filled) + 6)
    for i in range(w):
        if i < filled:
            if done:
                style = mix(tick * 1.5 + i * 0.2) + BOLD
            else:
                r, g, b = heat(i / max(1, w - 1))
                d = abs(i - sweep)
                if d < 3:
                    k = (3 - d) / 3 * 0.6
                    r, g, b = lerp((r, g, b), (255, 255, 255), k)
                style = fg(r, g, b)
            cv.put(x + i, y, "Γûê", style)
        else:
            cv.put(x + i, y, "Γûæ", GREEN_DARK)


def draw_gauge(cv, x, y, w, pct, level):
    rgb = LEVEL_RGB[level]
    filled = int(round(w * pct / 100))
    for i in range(w):
        if i < filled:
            cv.put(x + i, y, "Γûê", fg(*lerp(heat(1 - i / max(1, w - 1)), rgb, 0.35)))
        else:
            cv.put(x + i, y, "Γûæ", GREEN_DARK)


def draw_header(cv, left, right, tick):
    cv.fill(0, 0, cv.w, 1, HEADER_BG)
    cv.gradient(1, 0, left, tick, HEADER_BG)
    if right:
        cv.put(cv.w - len(right) - 1, 0, right, WHITE + HEADER_BG)


def draw_hints(cv, y, pairs):
    x = 2
    for key, label in pairs:
        if x + len(key) + len(label) + 1 > cv.w:
            break
        cv.put(x, y, key, NEON_S)
        x += len(key) + 1
        cv.put(x, y, label, GREY)
        x += len(label) + 3


def draw_msg(cv, msg):
    text, style = msg
    cv.put(2, cv.h - 2, ("ΓùÅ " + text)[: cv.w - 3], style)


def draw_boot(cv, prog, tick):
    pw = min(66, cv.w - 4)
    ph = 17
    px = (cv.w - pw) // 2
    py = max(0, (cv.h - ph) // 2)
    panel(cv, px, py, pw, ph, "SYSTEM BOOT", tick, NEON_S)
    draw_logo(cv, px + (pw - logo_width("GENETIC")) // 2, py + 2, "GENETIC", tick)
    sub = "T O O L S   ┬╖   R E P O   S C A N N E R"
    cv.put(px + (pw - len(sub)) // 2, py + 8, sub, GREY)

    bw = pw - 16
    draw_bar(cv, px + 4, py + 10, bw, prog, tick)
    cv.put(px + 6 + bw, py + 10, f"{int(prog * 100):3d}%", WHITE + BOLD)

    last = min(int(prog * len(BOOT_STEPS)), len(BOOT_STEPS) - 1)
    spin = "|/-\\"[int(tick * 8) % 4]
    for row, idx in enumerate(range(max(0, last - 3), last + 1)):
        done = idx < last or prog >= 1.0
        if done:
            cv.put(px + 4, py + 12 + row, "Γ£ö " + BOOT_STEPS[idx], NEON_C)
        else:
            cv.put(px + 4, py + 12 + row, f"{spin} {BOOT_STEPS[idx]}...", WHITE)
    cv.center(cv.h - 1, "ketik apa saja untuk melewati", GREY)


# ============================================================
# ATURAN DETEKSI  -  tambah pola baru cukup di fungsi _build_rules()
#   scope : text (semua teks) ┬╖ code ┬╖ shell ┬╖ py ┬╖ js ┬╖ php ┬╖ ci ┬╖ setuppy
#   kw    : kata kunci murah (huruf kecil) agar regex hanya jalan bila perlu
#   mal   : True = indikator khas malware
# ============================================================

CAT_NAMES = {
    "SECRET": "Kebocoran Kredensial",
    "EXEC": "Eksekusi Kode Dinamis",
    "OBFUS": "Obfuscation / Penyamaran",
    "NET": "Jaringan & Exfiltrasi",
    "SYS": "Sistem & Persistensi",
    "PRIV": "Pencurian Data & Pengawasan",
    "SUPPLY": "Rantai Pasok & Dependensi",
    "FILE": "Berkas Berbahaya",
    "META": "Reputasi Repository",
}

CAT_ADVICE = {
    "SECRET": "Cabut dan rotasi semua kredensial yang bocor; jangan pakai kunci yang tertanam di repo publik.",
    "EXEC": "Periksa asal input pada eval/exec/shell dan pastikan data pengguna tidak ikut dieksekusi.",
    "OBFUS": "Kode yang diencode/disamarkan sering dipakai menyembunyikan payload; minta sumber asli atau hindari.",
    "NET": "Verifikasi tujuan koneksi (webhook, IP mentah, tunnel, pipe ke shell); blokir bila tidak dikenal.",
    "SYS": "Pastikan skrip tidak mengubah startup, firewall, atau berkas sistem tanpa sepengetahuan Anda.",
    "PRIV": "Skrip yang membaca data browser/SSH/wallet atau merekam input adalah red flag; jangan jalankan di mesin utama.",
    "SUPPLY": "Kunci versi dependensi, hindari hook instalasi yang mengunduh/menjalankan kode, dan cek ejaan nama paket.",
    "FILE": "Jangan jalankan biner tanpa sumber; bandingkan hash dengan rilis resmi.",
    "META": "Reputasi rendah bukan bukti bahaya, tetapi tinjau lebih hati-hati sebelum memakai.",
}


class Rule:
    __slots__ = ("id", "cat", "sev", "name", "rx", "scope", "kw", "desc",
                 "mal", "filt", "mask", "maxlen")

    def __init__(self, rid, cat, sev, name, pattern, scope, kw, desc,
                 flags=0, mal=False, filt=None, mask=None, maxlen=0):
        self.id, self.cat, self.sev, self.name = rid, cat, sev, name
        self.rx = re.compile(pattern, flags) if pattern else None
        self.scope, self.kw, self.desc = scope, kw, desc
        self.mal, self.filt, self.mask, self.maxlen = mal, filt, mask, maxlen


_PLACEHOLDER = ("example", "your", "xxxx", "changeme", "change_me", "placeholder", "<", ">",
                "{{", "${", "***", "dummy", "sample", "redacted", "password", "passwd",
                "12345", "abcde", "fake", "process.", "os.environ", "getenv")


def _real_secret(m):
    quoted = re.findall(r"[\"']([^\"']+)[\"']", m.group(0))
    if not quoted:
        return False
    v = quoted[-1]
    lv = v.lower()
    if any(p in lv for p in _PLACEHOLDER) or len(set(v)) < 4:
        return False
    classes = sum(bool(re.search(p, v)) for p in ("[a-z]", "[A-Z]", "[0-9]", "[^A-Za-z0-9]"))
    return classes >= 2


def _real_dburl(m):
    v = m.group(0).lower()
    bad = ("user:pass", "username:password", "user:password", "localhost", "127.0.0.1",
           "example", "<", "${", "{", "%s", "pass@", "password@", "root:root", "postgres:postgres")
    return not any(b in v for b in bad)


def _build_rules():
    R = []

    def add(*a, **k):
        R.append(Rule(*a, **k))

    I = re.I
    # ---------------- kredensial ----------------
    add("aws-key", "SECRET", "high", "AWS Access Key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", "text",
        ("akia", "asia"), "Kunci akses AWS tertanam di berkas.", mask="token")
    add("private-key", "SECRET", "high", "Private key tertanam",
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----", "text",
        ("private key",), "Kunci privat (RSA/EC/OpenSSH/PGP) ikut tersimpan di repo.")
    add("github-token", "SECRET", "high", "GitHub token",
        r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b", "text",
        ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"),
        "Token akses GitHub tertanam; siapa pun bisa memakainya.", mask="token")
    add("slack-token", "SECRET", "high", "Slack token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b", "text",
        ("xox",), "Token Slack tertanam.", mask="token")
    add("google-api-key", "SECRET", "med", "Google API key", r"\bAIza[0-9A-Za-z_\-]{35}\b", "text",
        ("aiza",), "API key Google tertanam.", mask="token")
    add("stripe-live", "SECRET", "high", "Stripe live key", r"\b[sr]k_live_[0-9A-Za-z]{20,}\b", "text",
        ("_live_",), "Kunci pembayaran Stripe mode live tertanam.", mask="token")
    add("telegram-token", "SECRET", "med", "Telegram bot token", r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b",
        "text", None, "Token bot Telegram tertanam.", mask="token")
    add("discord-token", "SECRET", "med", "Discord token",
        r"\b[MNO][A-Za-z\d_-]{23,25}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27,38}\b", "text", (".",),
        "Token akun/bot Discord tertanam.", mask="token")
    add("generic-secret", "SECRET", "med", "Password/secret hardcoded",
        r"(?:[A-Za-z0-9]{1,20}[_-]){0,3}(?:password|passwd|secret|api[_-]?key|apikey|access[_-]?token|"
        r"auth[_-]?token|client[_-]?secret)(?:[_-][A-Za-z0-9]{1,20}){0,3}\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']",
        "text", ("password", "passwd", "secret", "api_key", "apikey", "api-key", "token"),
        "Nilai rahasia ditulis langsung di kode.", flags=I, filt=_real_secret, mask="value")
    add("jwt", "SECRET", "med", "JWT tertanam",
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "text", ("eyj",),
        "Token JWT lengkap ditemukan di berkas.", mask="token")
    add("db-url", "SECRET", "med", "URL database berisi password",
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^:\s/@]+:[^@\s]{3,}@[^\s'\"]+", "text",
        ("://",), "String koneksi database memuat username & password.", filt=_real_dburl, mask="dburl")

    # ---------------- eksekusi kode ----------------
    add("py-exec-eval", "EXEC", "low", "Python eval()/exec()", r"(?<![\w.])(?:eval|exec)\s*\(", "py",
        ("eval", "exec"), "Mengeksekusi string sebagai kode; berbahaya bila inputnya tak tepercaya.")
    add("py-os-system", "EXEC", "med", "Python os.system/popen", r"\bos\.(?:system|popen)\s*\(", "py",
        ("os.",), "Menjalankan perintah shell langsung dari Python.")
    add("py-shell-true", "EXEC", "med", "subprocess shell=True",
        r"\bsubprocess\.\w+\([^)\n]*shell\s*=\s*True", "py", ("shell",),
        "Perintah dijalankan lewat shell sehingga rentan injeksi.")
    add("py-unsafe-deser", "EXEC", "med", "Deserialisasi tidak aman",
        r"\b(?:pickle|cPickle|_pickle|dill|marshal)\.loads?\s*\(|\byaml\.load\s*\((?![^)\n]*Safe)", "py",
        ("pickle", "marshal", "yaml", "dill"), "pickle/marshal/yaml.load dapat menjalankan kode saat memuat data.")
    add("js-eval", "EXEC", "low", "JavaScript eval()/new Function",
        r"(?<![\w.$])eval\s*\(|\bnew\s+Function\s*\(", "js", ("eval", "new function"),
        "Mengeksekusi string sebagai kode JavaScript.")
    add("js-child-process", "EXEC", "low", "Node child_process", r"\bchild_process\b", "js",
        ("child_process",), "Menjalankan proses/perintah sistem dari Node.js.")
    add("php-exec", "EXEC", "med", "PHP exec/system dengan variabel",
        r"\b(?:shell_exec|passthru|proc_open|popen|system|exec)\s*\(\s*\$", "php",
        ("shell_exec", "passthru", "proc_open", "popen", "system", "exec"),
        "Perintah sistem dibentuk dari variabel PHP.")
    add("php-webshell", "EXEC", "crit", "Pola web shell PHP",
        r"\beval\s*\(\s*(?:base64_decode|gzinflate|gzuncompress|str_rot13|\$_(?:POST|GET|REQUEST|COOKIE))|"
        r"\bassert\s*\(\s*\$_(?:POST|GET|REQUEST)", "php", ("eval", "assert"),
        "Pola klasik web shell: kode dari request dieksekusi.", mal=True)
    add("java-exec", "EXEC", "low", "Java Runtime.exec/ProcessBuilder",
        r"\bRuntime\.getRuntime\(\)\.exec\(|\bnew\s+ProcessBuilder\(", "code",
        ("runtime.getruntime", "processbuilder"), "Menjalankan proses sistem dari Java.")

    # ---------------- obfuscation ----------------
    add("py-exec-decode", "OBFUS", "crit", "Eksekusi payload ter-encode (Python)",
        r"(?<![\w.])(?:exec|eval)\s*\(\s*(?:[\w.]*\.)?(?:b64decode|decompress|unhexlify|fromhex|loads)\b|"
        r"(?<![\w.])(?:exec|eval)\s*\([^\n]{0,100}(?:b64decode|decompress|marshal\.loads|unhexlify|codecs\.decode)|"
        r"__import__\(\s*[\"'](?:base64|zlib|marshal)[\"']\s*\)[^\n]{0,80}(?:exec|eval|decode)", "py",
        ("exec", "eval", "__import__"), "Kode disembunyikan (base64/zlib/marshal) lalu langsung dieksekusi.", mal=True)
    add("js-decode-eval", "OBFUS", "crit", "Eksekusi payload ter-encode (JS)",
        r"(?<![\w.$])(?:eval|Function)\s*\(\s*(?:atob|unescape|decodeURIComponent|String\.fromCharCode)\b|"
        r"(?<![\w.$])eval\s*\([^\n]{0,80}Buffer\.from\([^\n]{0,60}base64", "js", ("eval", "function("),
        "String ter-decode (atob/Buffer) langsung dijalankan sebagai kode.", mal=True)
    add("js-packer", "OBFUS", "high", "JavaScript packed/obfuscated", r"eval\(function\(p,a,c,k,e,[dr]\)", "js",
        ("eval(function(p",), "Kode JavaScript dikompres/disamarkan dengan packer.")
    add("hex-escape", "OBFUS", "med", "Rantai karakter hex-escape", r"(?:\\x[0-9a-fA-F]{2}){12,}", "code",
        ("\\x",), "String panjang berisi escape heksadesimal, lazim untuk menyamarkan payload.")
    add("chr-chain", "OBFUS", "med", "Rangkaian chr()/fromCharCode",
        r"(?:\bchr\(\s*\d+\s*\)\s*\+\s*){6,}|String\.fromCharCode\((?:\s*\d+\s*,){10,}", "code",
        ("chr(", "fromcharcode"), "String disusun dari kode angka untuk menyamarkan isinya.")
    add("base64-blob", "OBFUS", "low", "Blob base64 panjang di kode", r"[A-Za-z0-9+/]{400,}={0,2}", "code",
        None, "Data terenkode sangat panjang tertanam di kode (bisa aset, bisa payload).", maxlen=400_000)
    add("ps-encoded", "OBFUS", "crit", "PowerShell -EncodedCommand",
        r"powershell(?:\.exe)?[^\n]{0,80}\s-(?:e|ec|enc|encodedcommand)\s+[A-Za-z0-9+/=]{20,}", "code",
        ("powershell",), "PowerShell menjalankan perintah ter-encode base64.", flags=I, mal=True)
    add("ps-iex-download", "OBFUS", "crit", "PowerShell download & eksekusi (IEX)",
        r"\b(?:iex|invoke-expression)\b[^\n]{0,100}(?:downloadstring|net\.webclient|invoke-webrequest|\biwr\b|downloadfile)|"
        r"(?:downloadstring|invoke-webrequest|\biwr\b)[^\n]{0,100}\|\s*(?:iex|invoke-expression)", "code",
        ("iex", "invoke-expression"), "Mengunduh skrip dari internet lalu langsung mengeksekusinya.", flags=I, mal=True)
    add("ps-hidden", "OBFUS", "high", "PowerShell window tersembunyi",
        r"powershell[^\n]{0,60}-w(?:indowstyle)?\s+hidden", "code", ("hidden",),
        "Menjalankan PowerShell tanpa jendela terlihat.", flags=I)
    add("bidi-trojan", "OBFUS", "high", "Karakter bidi tersembunyi (Trojan Source)",
        "[\u202a-\u202e\u2066-\u2069]", "code", None,
        "Karakter arah-teks tak terlihat bisa membuat kode tampak berbeda dari yang dieksekusi.")

    # ---------------- jaringan ----------------
    add("discord-webhook", "NET", "high", "Discord webhook",
        r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+", "text", ("discord",),
        "Webhook Discord sering dipakai stealer untuk mengirim data curian.")
    add("telegram-exfil", "NET", "med", "Telegram Bot API (kirim data)",
        r"api\.telegram\.org/bot[^\s/'\"]*/(?:sendMessage|sendDocument|sendPhoto)", "text",
        ("api.telegram.org",), "Mengirim pesan/berkas via bot Telegram; sah untuk bot, juga dipakai exfiltrasi.")
    add("file-drop", "NET", "low", "Layanan paste/file-drop",
        r"\b(?:pastebin\.com/raw|paste\.ee/r|hastebin\.com/raw|transfer\.sh|anonfiles\.com|gofile\.io|file\.io|0x0\.st|temp\.sh)\b",
        "code", ("pastebin", "paste.ee", "hastebin", "transfer.sh", "anonfiles", "gofile", "file.io", "0x0.st", "temp.sh"),
        "Memakai layanan paste/penyimpanan sementara untuk memuat atau mengirim data.")
    add("tunnel", "NET", "low", "Tunnel / expose lokal",
        r"\b(?:[\w-]+\.)?(?:ngrok\.io|ngrok-free\.app|trycloudflare\.com|serveo\.net|localhost\.run|loca\.lt|portmap\.io)\b",
        "text", ("ngrok", "trycloudflare", "serveo", "localhost.run", "loca.lt", "portmap"),
        "Menghubungkan mesin ke internet lewat tunnel pihak ketiga.")
    add("raw-ip-url", "NET", "med", "URL ke alamat IP mentah",
        r"https?://(?!(?:127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.))(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?",
        "code", ("://",), "Koneksi ke IP publik langsung (tanpa domain), umum pada C2/payload.")
    add("curl-pipe-sh", "NET", "high", "Unduh lalu pipe ke shell",
        r"\b(?:curl|wget)\b[^\n|;]{0,200}\|\s*(?:sudo\s+)?(?:ba|z|da|k)?sh\b|(?:\biwr\b|invoke-webrequest)[^\n|]{0,150}\|\s*iex\b",
        "text", ("curl", "wget", "iwr", "invoke-webrequest"),
        "Mengeksekusi skrip dari internet tanpa diperiksa (curl | sh).", flags=I)
    add("reverse-shell", "NET", "crit", "Pola reverse shell",
        r"/dev/(?:tcp|udp)/[\w.${}\-]+/\d+|\bnc(?:at)?\b[^\n]{0,60}\s-e\s+\S*(?:ba|z)?sh\b|\bmkfifo\b[^\n]{0,80}\bn(?:c|cat)\b|"
        r"\bpty\.spawn\s*\(\s*[\"']/bin/(?:ba)?sh|\bos\.dup2\([^\n]{0,40}\.fileno\(\)\s*,\s*[012]\s*\)|System\.Net\.Sockets\.TCPClient",
        "text", ("/dev/tcp", "/dev/udp", "nc ", "ncat", "mkfifo", "pty.spawn", "dup2", "tcpclient"),
        "Memberi pihak luar akses shell ke mesin Anda.", mal=True)
    add("crypto-miner", "NET", "crit", "Penambang kripto (miner)",
        r"\bstratum\+(?:tcp|ssl)://|\b(?:xmrig|cpuminer|minerd|coinhive|cryptonight)\b|\bmonero(?:ocean)?\.(?:com|org)\b|pool\.minexmr|supportxmr",
        "text", ("stratum", "xmrig", "cpuminer", "minerd", "coinhive", "cryptonight", "monero", "minexmr", "supportxmr"),
        "Referensi miner/pool kripto; dapat membajak CPU/GPU Anda.", flags=I, mal=True)
    add("ssl-disabled", "NET", "low", "Verifikasi TLS dimatikan",
        r"\bverify\s*=\s*False\b|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*[\"']?0",
        "code", ("verify", "rejectunauthorized", "insecureskipverify", "node_tls_reject_unauthorized"),
        "Koneksi HTTPS tidak memverifikasi sertifikat (rawan MITM).")
    add("download-exec", "NET", "med", "Mengunduh berkas eksekusi",
        r"(?:urlretrieve|urlopen|requests\.get|wget|curl|Invoke-WebRequest|DownloadFile)\b[^\n]{0,150}\.(?:exe|dll|scr|bat|ps1|vbs|jar|apk)\b",
        "code", ("urlretrieve", "urlopen", "requests.get", "wget", "curl", "invoke-webrequest", "downloadfile"),
        "Kode mengunduh berkas yang dapat dieksekusi dari internet.", flags=I)

    # ---------------- sistem ----------------
    add("destructive-cmd", "SYS", "high", "Perintah destruktif",
        r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(?:--no-preserve-root\s+)?(?:/|~|\$HOME|/\*)(?=[\s\"';]|\Z)|"
        r"\bmkfs(?:\.\w+)?\s+/dev/|\bdd\s+if=\S+\s+of=/dev/(?:sd|nvme|mmcblk|disk|hd)|:\(\)\s*\{\s*:\|:&\s*\};:",
        "text", ("rm ", "mkfs", "dd if=", ":()"), "Menghapus/menimpa disk atau direktori penting (rm -rf /, mkfs, fork bomb).")
    add("chmod-777", "SYS", "low", "chmod 777", r"\bchmod\s+(?:-R\s+)?(?:0?777|a\+rwx|ugo\+rwx)\b", "text",
        ("chmod",), "Memberi izin tulis/eksekusi ke semua pengguna.")
    add("setuid", "SYS", "low", "chmod setuid/setgid", r"\bchmod\s+(?:[ug]\+s|[2467][0-7]{3})\b", "text",
        ("chmod",), "Mengaktifkan bit setuid/setgid (potensi eskalasi hak akses).")
    add("persist-unix", "SYS", "med", "Persistensi Linux/Unix",
        r">>\s*~?/?[\w/.$\{\}]*\.(?:bashrc|zshrc|profile|bash_profile)\b|/etc/rc\.local|/etc/cron\.(?:d|daily|hourly)/|"
        r"\.config/autostart/|/etc/systemd/system/[\w.@-]+\.service", "text",
        ("rc.local", "cron", "autostart", "systemd", "bashrc", "zshrc", "profile"),
        "Mengubah startup/cron/service agar berjalan otomatis setiap boot atau login.")
    add("persist-win", "SYS", "high", "Persistensi Windows",
        r"CurrentVersion\\+Run(?:Once)?\b|schtasks(?:\.exe)?\s+/create|\\Start Menu\\Programs\\Startup|\breg(?:\.exe)?\s+add\s+[^\n]*\\Run\b",
        "text", ("currentversion", "schtasks", "startup", "reg add"),
        "Menambah entri startup/scheduled task Windows.", flags=I)
    add("ssh-authkeys", "SYS", "high", "Menulis authorized_keys",
        r"(?:>>?|\.write\(|open\()[^\n]{0,60}authorized_keys|authorized_keys[^\n]{0,60}(?:>>|\.write\()", "text",
        ("authorized_keys",), "Menambahkan kunci SSH sehingga pihak lain bisa masuk ke mesin Anda.")
    add("disable-security", "SYS", "high", "Mematikan proteksi keamanan",
        r"Set-MpPreference\s+-DisableRealtimeMonitoring|Add-MpPreference\s+-ExclusionPath|"
        r"netsh\s+advfirewall\s+set\s+\w+\s+state\s+off|\bsetenforce\s+0\b|\bufw\s+disable\b|\bsc(?:\.exe)?\s+(?:stop|config)\s+WinDefend",
        "text", ("set-mppreference", "advfirewall", "setenforce", "ufw disable", "windefend", "exclusionpath"),
        "Mematikan antivirus/firewall/SELinux.", flags=I)
    add("docker-privileged", "SYS", "low", "Docker privileged / docker.sock",
        r"/var/run/docker\.sock|privileged:\s*true|--privileged\b", "text", ("docker.sock", "privileged"),
        "Kontainer diberi akses penuh ke host.")

    # ---------------- pencurian data & pengawasan ----------------
    add("browser-steal", "PRIV", "high", "Akses data login browser",
        r"(?:chrome|chromium|brave|edge|opera|firefox|vivaldi)[^\n]{0,120}(?:Login Data|logins\.json|key[34]\.db|Local State)",
        "text", ("login data", "logins.json", "key4.db", "key3.db", "local state"),
        "Membaca database password/cookie browser, ciri khas stealer.", flags=I, mal=True)
    add("wallet-steal", "PRIV", "med", "Akses dompet kripto",
        r"wallet\.dat|\\Exodus\\|Electrum[\\/]wallets|nkbihfbeogaeaoehlefnkodbefgpgknn|keystore[\\/]UTC--", "text",
        ("wallet.dat", "exodus", "electrum", "nkbihfbeogaeaoehlefnkodbefgpgknn", "utc--"),
        "Menyentuh berkas dompet kripto.", flags=I)
    add("cred-files", "PRIV", "med", "Membaca berkas kredensial pengguna",
        r"(?:~|\$HOME|expanduser\([^)\n]*\)|%USERPROFILE%)[^\n]{0,30}[\\/]\.(?:ssh[\\/]id_\w+|aws[\\/]credentials|kube[\\/]config|docker[\\/]config\.json|git-credentials|netrc|npmrc)",
        "text", (".ssh", ".aws", ".kube", ".docker", ".git-credentials", ".netrc", ".npmrc"),
        "Mengakses kunci SSH / kredensial cloud / token milik pengguna.")
    add("etc-shadow", "PRIV", "med", "Membaca /etc/shadow", r"(?:open\(|cat\s+|read\w*\(|cp\s+)[^\n]{0,20}/etc/shadow",
        "text", ("/etc/shadow",), "Mengambil hash password sistem.")
    add("keylogger", "PRIV", "high", "Keylogger / hook keyboard",
        r"\bGetAsyncKeyState\b|\bSetWindowsHookEx\w*\b|\bpyxhook\b|\bkeylogger\b|\bfrom\s+pynput\.keyboard\s+import\s+Listener|"
        r"\bkeyboard\.(?:on_press|on_release|hook|record|add_hotkey)\s*\(", "code",
        ("getasynckeystate", "setwindowshook", "pyxhook", "keylog", "pynput", "keyboard."),
        "Merekam ketikan pengguna.", flags=I, mal=True)
    add("capture", "PRIV", "med", "Tangkap layar / kamera / mikrofon",
        r"\bImageGrab\.grab\b|pyautogui\.screenshot|\bmss\.mss\b|cv2\.VideoCapture\(|\bBitBlt\b|\bpyaudio\b|sounddevice\.rec\b",
        "code", ("imagegrab", "screenshot", "mss", "videocapture", "bitblt", "pyaudio", "sounddevice"),
        "Mengambil gambar layar, kamera, atau suara.")
    add("clipboard", "PRIV", "low", "Akses clipboard",
        r"\bpyperclip\.(?:paste|copy)\b|\bwin32clipboard\b|GetClipboardData|navigator\.clipboard\.readText", "code",
        ("pyperclip", "win32clipboard", "getclipboarddata", "readtext"), "Membaca/mengubah isi clipboard.")
    add("env-harvest", "PRIV", "med", "Mengumpulkan environment variable",
        r"\bdict\(\s*os\.environ\s*\)|json\.dumps\(\s*(?:dict\()?os\.environ|JSON\.stringify\(\s*process\.env\s*\)", "code",
        ("os.environ", "process.env"), "Menyalin seluruh environment (sering memuat token) untuk dikirim/disimpan.")

    # ---------------- rantai pasok ----------------
    add("setuppy-exec", "SUPPLY", "med", "setup.py menjalankan kode/jaringan",
        r"\b(?:os\.system|os\.popen|subprocess\.\w+|urlopen|urlretrieve|requests\.(?:get|post)|exec\s*\(|eval\s*\()",
        "setuppy", None, "Kode di setup.py berjalan otomatis saat pip install.")
    add("ci-pr-target", "SUPPLY", "med", "CI: pull_request_target", r"\bpull_request_target\b", "ci", ("pull_request_target",),
        "Workflow berhak tinggi yang dipicu PR dari fork; rawan pencurian secret.")
    add("ci-injection", "SUPPLY", "med", "CI: injeksi ekspresi GitHub Actions",
        r"\$\{\{\s*github\.(?:event\.(?:issue|pull_request|comment|review|head_commit|pages)[\w.\[\]\*]*\.(?:title|body|head_ref|message|name|label|email)|head_ref)\s*\}\}",
        "ci", ("github.",), "Input yang dikontrol penyerang dipakai langsung dalam workflow.")
    add("ci-unpinned", "SUPPLY", "low", "CI: action tidak dikunci versi",
        r"uses:\s*[\w./-]+@(?:main|master|latest|dev)\b", "ci", ("uses:",),
        "Action mengikuti branch bergerak; isinya bisa berubah tanpa pemberitahuan.")
    add("docker-add-url", "SUPPLY", "low", "Dockerfile ADD dari URL", r"^\s*ADD\s+https?://", "shell", ("add ",),
        "Dockerfile mengunduh berkas jarak jauh tanpa verifikasi.", flags=I | re.M)
    return R


RULES = _build_rules()
RULES_BY_SCOPE = collections.defaultdict(list)
for _r in RULES:
    RULES_BY_SCOPE[_r.scope].append(_r)

# aturan meta (tanpa regex) - dipakai oleh pemeriksaan berkas, dependensi & metadata
META = {}
for _args in [
    ("sensitive-file", "FILE", "high", "Berkas rahasia ikut di repo", "Berkas seperti .env/kunci privat tidak seharusnya dikomit."),
    ("bin-exec", "FILE", "med", "Biner executable di dalam repo", "File biner (exe/dll/ELF/Mach-O) tidak bisa ditinjau sebagai kode sumber."),
    ("pyc", "FILE", "med", "Bytecode Python (.pyc) tanpa sumber", "Bytecode dapat menyembunyikan logika yang tak tampak di kode sumber."),
    ("build-artifact", "FILE", "low", "Artefak build (jar/apk/class)", "Artefak terkompilasi tidak bisa diperiksa seperti kode sumber."),
    ("embedded-archive", "FILE", "low", "Arsip tertanam di repo", "Arsip (zip/rar/7z) bisa membungkus muatan yang tidak terpindai."),
    ("minified", "OBFUS", "low", "File minified/bundle tidak dipindai", "File minified sulit ditinjau; isinya tidak dianalisa pola."),
    ("symlink-out", "FILE", "med", "Symlink keluar repo", "Symlink ke path absolut/di luar repo dapat membaca berkas sistem."),
    ("committed-deps", "SUPPLY", "low", "Folder dependensi ikut dikomit", "node_modules/venv ikut di repo: kode pihak ketiga tak terverifikasi."),
    ("npm-hook-susp", "SUPPLY", "high", "npm: hook instalasi mencurigakan", "Skrip preinstall/postinstall menjalankan unduhan/eksekusi saat npm install."),
    ("npm-hook", "SUPPLY", "low", "npm: memiliki hook instalasi", "Skrip lifecycle otomatis berjalan saat npm install."),
    ("dep-vcs", "SUPPLY", "med", "Dependensi dari URL/VCS", "Paket diambil langsung dari git/URL, bukan registry resmi."),
    ("dep-insecure", "SUPPLY", "high", "Dependensi lewat HTTP polos", "Unduhan tanpa TLS dapat disusupi di jaringan."),
    ("dep-unpinned", "SUPPLY", "low", "Dependensi tidak dikunci versi", "Versi bebas membuka peluang pembaruan berbahaya."),
    ("typosquat", "SUPPLY", "high", "Nama paket mirip paket populer", "Kemungkinan typosquatting: nama berbeda satu huruf dari paket terkenal."),
    ("docker-root", "SYS", "low", "Dockerfile tanpa USER non-root", "Kontainer berjalan sebagai root secara default."),
    ("no-license", "META", "low", "Tidak ada lisensi", "Tanpa lisensi, hak pakai/redistribusi tidak jelas."),
    ("repo-new", "META", "low", "Repo sangat baru & belum populer", "Reputasi belum teruji; waspadai repo baru berbintang sedikit."),
    ("repo-archived", "META", "low", "Repo diarsipkan", "Tidak lagi dirawat; celah baru tidak akan ditambal."),
    ("repo-stale", "META", "low", "Repo lama tidak diperbarui", "Tidak ada aktivitas > 2 tahun; dependensi mungkin usang."),
    ("repo-fork", "META", "info", "Repo adalah fork", "Bandingkan dengan repo asli untuk memastikan tak ada perubahan berbahaya."),
    ("scan-truncated", "META", "info", "Pemindaian dipotong oleh batas", "Sebagian berkas tidak terpindai karena batas ukuran/waktu."),
]:
    META[_args[0]] = Rule(_args[0], _args[1], _args[2], _args[3], None, "meta", None, _args[4])


class Findings(dict):
    """Kumpulan temuan: id aturan -> statistik + contoh."""

    def add(self, rule, path, line, snippet, factor=1.0, count=1):
        f = self.get(rule.id)
        if f is None:
            f = self[rule.id] = {"rule": rule, "hits": 0, "eff": 0.0, "files": set(), "samples": []}
        path = clean(path)
        f["hits"] += count
        f["eff"] += factor * count
        f["files"].add(path)
        damp = factor < 1.0
        item = {"path": path, "line": line, "snippet": clean(snippet), "damped": damp}
        s = f["samples"]
        if len(s) < 5:
            s.append(item)
        elif not damp:
            for i, x in enumerate(s):
                if x["damped"]:
                    s[i] = item
                    break


# ============================================================
# PENGOLAH TARGET (URL / folder)
# ============================================================

class ScanError(Exception):
    """Kesalahan yang pesannya aman ditampilkan ke pengguna."""


class ScanCancelled(Exception):
    pass


PROVIDERS = {
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "bitbucket.org": "Bitbucket",
    "codeberg.org": "Codeberg",
}

_SEG_RE = re.compile(r"^[A-Za-z0-9._~-]+$")
_REF_RE = re.compile(r"^[A-Za-z0-9._/@~+-]{1,100}$")
_HOST_RE = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$")


def parse_target(raw):
    raw = (raw or "").strip().strip("\"'").strip()
    if not raw:
        raise ScanError("URL repo masih kosong.")
    if len(raw) > 400:
        raise ScanError("Input terlalu panjang.")

    lp = os.path.expanduser(raw)
    if os.path.isdir(lp):
        lp = os.path.abspath(lp)
        return {"kind": "local", "provider": "Folder lokal", "host": "lokal", "name": os.path.basename(lp) or "folder",
                "ref": None, "display": lp, "web": None, "root": lp, "archives": [], "clone": None}
    if raw.startswith(("/", "./", "../", "~")) or re.match(r"^[A-Za-z]:[\\/]", raw):
        raise ScanError("Folder lokal tidak ditemukan.")

    ref = None
    m = re.match(r"^(?:ssh://)?git@([\w.-]+)[:/](.+?)(?:\.git)?/?$", raw)
    if m:
        host, path = m.group(1).lower(), m.group(2)
    elif re.match(r"^[\w.-]+/[\w.-]+$", raw):
        host, path = "github.com", raw
    else:
        url = raw if re.match(r"^[a-z][a-z0-9+.-]*://", raw, re.I) else "https://" + raw
        u = urllib.parse.urlparse(url)
        if u.scheme.lower() not in ("http", "https", "git", "ssh"):
            raise ScanError("Skema URL tidak didukung. Pakai https://, git@, owner/repo, atau path folder.")
        host = (u.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = u.path
        if path.lower().endswith((".zip", ".tar.gz", ".tgz", ".tar")) and _HOST_RE.match(host):
            if u.scheme.lower() not in ("http", "https"):
                raise ScanError("Arsip harus berupa URL http/https.")
            name = os.path.basename(urllib.parse.unquote(path)) or "arsip"
            clean_url = urllib.parse.urlunparse(("https" if u.scheme == "ssh" else u.scheme, u.netloc, u.path, "", u.query, ""))
            return {"kind": "archive", "provider": "Arsip langsung", "host": host, "name": name, "ref": None,
                    "display": f"{host}/{name}", "web": None, "archives": [clean_url], "clone": None}

    if not _HOST_RE.match(host or ""):
        raise ScanError("Host tidak valid. Contoh: https://github.com/owner/repo")
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    segs = [s for s in path.split("/") if s]

    if "-" in segs:                                   # GitLab: /grup/proyek/-/tree/ref
        i = segs.index("-")
        rest = segs[i + 1:]
        segs = segs[:i]
        if len(rest) >= 2 and rest[0] in ("tree", "blob"):
            ref = rest[1]
    elif host == "github.com":
        if len(segs) >= 4 and segs[2] in ("tree", "blob", "commit", "releases"):
            ref = segs[3] if segs[2] != "releases" else None
        segs = segs[:2]
    elif host == "bitbucket.org":
        if len(segs) >= 4 and segs[2] == "src":
            ref = segs[3]
        segs = segs[:2]
    elif len(segs) >= 5 and segs[2] == "src" and segs[3] in ("branch", "tag", "commit"):   # Gitea/Codeberg
        ref = segs[4]
        segs = segs[:2]

    if len(segs) < 2:
        raise ScanError("URL belum lengkap: butuh minimal owner/repo.")
    if not all(_SEG_RE.match(s) for s in segs):
        raise ScanError("Nama owner/repo mengandung karakter yang tidak diizinkan.")
    if ref is not None and not _REF_RE.match(ref):
        ref = None

    name = segs[-1]
    owner = "/".join(segs[:-1])
    repo_path = "/".join(segs)
    rp = ref or "HEAD"
    if host == "github.com":
        archives = [f"https://codeload.github.com/{owner}/{name}/tar.gz/{rp}"]
    elif host == "bitbucket.org":
        archives = [f"https://bitbucket.org/{owner}/{name}/get/{rp}.tar.gz"]
    elif host == "gitlab.com" or host.startswith("gitlab."):
        archives = [f"https://{host}/{repo_path}/-/archive/{rp}/{name}.tar.gz"]
    else:
        archives = [f"https://{host}/{repo_path}/archive/{rp}.tar.gz"]
    return {
        "kind": "git", "provider": PROVIDERS.get(host, f"Git ({host})"), "host": host,
        "owner": owner, "name": name, "ref": ref,
        "display": f"{host}/{repo_path}" + (f" @ {ref}" if ref else ""),
        "web": f"https://{host}/{repo_path}", "archives": archives,
        "clone": f"https://{host}/{repo_path}.git",
    }


# ============================================================
# PROGRESS
# ============================================================

STAGES = [
    ("Menghubungi sumber", 0.04),
    ("Mengunduh repo", 0.24),
    ("Mengekstrak arsip", 0.10),
    ("Memetakan isi repo", 0.08),
    ("Memindai pola berbahaya", 0.34),
    ("Menganalisa dependensi", 0.08),
    ("Menghitung risiko", 0.06),
    ("Mengirim hasil", 0.06),
]


class Progress:
    def __init__(self, echo=False):
        self.stage = 0
        self.frac = 0.0
        self.detail = ""
        self.cancel = False
        self.complete = False
        self.echo = echo
        self.files = 0
        self.findings = 0
        self.mb = 0.0

    def check(self):
        if self.cancel:
            raise ScanCancelled()

    def begin(self, i, detail=""):
        self.check()
        self.stage, self.frac, self.detail = i, 0.0, detail
        if self.echo:
            print(f"  [{i + 1}/{len(STAGES)}] {STAGES[i][0]}...", flush=True)

    def set(self, frac, detail=None):
        self.frac = max(0.0, min(1.0, frac))
        if detail is not None:
            self.detail = detail

    def finish(self):
        self.complete = True

    @property
    def ratio(self):
        if self.complete:
            return 1.0
        base = sum(w for _, w in STAGES[:self.stage])
        return min(0.995, base + STAGES[self.stage][1] * self.frac)


# ============================================================
# AKUISISI REPO  (arsip -> ekstrak aman, cadangan: git clone)
# ============================================================

def _rm(path):
    def onerr(func, p, _exc):
        try:
            os.chmod(p, 0o700)
            func(p)
        except OSError:
            pass
    shutil.rmtree(path, onerror=onerr)


def _http_error(code, host):
    if code in (401, 403, 404):
        return f"Repo tidak ditemukan atau bersifat privat (HTTP {code}) di {host}."
    if code == 429:
        return f"Terkena batas permintaan {host} (HTTP 429). Coba lagi nanti."
    return f"Server {host} menolak permintaan (HTTP {code})."


def fetch_archive(url, dest, prog):
    host = urllib.parse.urlparse(url).hostname or ""
    headers = {"User-Agent": UA, "Accept": "application/octet-stream, */*"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and host.endswith("github.com"):
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=25)
    except urllib.error.HTTPError as exc:
        raise ScanError(_http_error(exc.code, host))
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ScanError(f"Koneksi ke {host} gagal: {reason}")
    got = 0
    try:
        with resp, open(dest, "wb") as fh:
            total = int(resp.headers.get("Content-Length") or 0)
            while True:
                prog.check()
                chunk = resp.read(65536)
                if not chunk:
                    break
                got += len(chunk)
                if got > MAX_DOWNLOAD:
                    raise ScanError(f"Arsip lebih besar dari batas {fmt_size(MAX_DOWNLOAD)}.")
                fh.write(chunk)
                frac = got / total if total else 1 - math.exp(-got / (8 * 1024 * 1024))
                prog.set(frac, f"{fmt_size(got)} diunduh")
                prog.mb = got / 1048576
    except (socket.timeout, OSError) as exc:
        raise ScanError(f"Unduhan terputus: {exc}")
    return got


def _open_archive(path):
    """Kembalikan (daftar entri, fungsi tutup). Entri: dict name,size,kind,open,link."""
    entries = []
    if zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
        for zi in zf.infolist():
            mode = (zi.external_attr >> 16) & 0o170000
            kind = "dir" if zi.is_dir() else ("link" if mode == 0o120000 else "file")
            link = zf.read(zi).decode("utf-8", "ignore") if kind == "link" and zi.file_size < 4096 else ""
            entries.append({"name": zi.filename, "size": zi.file_size, "kind": kind,
                            "open": (lambda zi=zi: zf.open(zi)), "link": link})
        return entries, zf.close
    if tarfile.is_tarfile(path):
        tf = tarfile.open(path, "r:*")
        for m in tf.getmembers():
            if m.isfile():
                kind = "file"
            elif m.issym() or m.islnk():
                kind = "link"
            else:
                kind = "dir"
            entries.append({"name": m.name, "size": m.size, "kind": kind,
                            "open": (lambda m=m: tf.extractfile(m)), "link": m.linkname if kind == "link" else ""})
        return entries, tf.close
    raise ScanError("Format arsip tidak dikenali (hanya .zip / .tar.gz yang didukung).")


def extract_archive(path, root, prog):
    info = {"big": [], "links": [], "pruned": collections.Counter(), "truncated": False, "unwritable": 0}
    entries, closer = _open_archive(path)
    try:
        split = [[p for p in e["name"].replace("\\", "/").split("/") if p not in ("", ".")] for e in entries]
        firsts = {p[0] for p in split if p}
        strip = 1 if len(firsts) == 1 and all(len(p) > 1 or e["kind"] == "dir" for p, e in zip(split, entries) if p) else 0
        realroot = os.path.realpath(root)
        files = total = 0
        n = max(1, len(entries))
        for i, (e, parts) in enumerate(zip(entries, split)):
            if i % 200 == 0:
                prog.check()
                prog.set(i / n, f"{i}/{n} entri")
            rest = parts[strip:]
            if not rest or ".." in rest:
                continue
            rel = "/".join(rest)
            hit = next((p for p in rest[:-1] if p in PRUNE_DIRS), None)
            if hit:
                if e["kind"] == "file":
                    info["pruned"][hit] += 1
                continue
            if e["kind"] == "link":
                info["links"].append((rel, e["link"]))
                continue
            if e["kind"] != "file":
                continue
            if e["size"] > MAX_FILE_EXTRACT:
                info["big"].append((rel, e["size"]))
                continue
            if files >= MAX_FILES or total + e["size"] > MAX_EXTRACT_TOTAL:
                info["truncated"] = True
                break
            dest = os.path.join(root, *rest)
            if not os.path.realpath(dest).startswith(realroot + os.sep):
                continue
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                src = e["open"]()
                with src, open(dest, "wb") as out_fh:
                    shutil.copyfileobj(src, out_fh)
                files += 1
                total += e["size"]
            except (OSError, KeyError, zipfile.BadZipFile, tarfile.TarError):
                info["unwritable"] += 1
    finally:
        closer()
    return info


def git_clone(url, ref, dest, prog):
    if not shutil.which("git"):
        raise ScanError("Git belum terpasang (Termux: pkg install git).")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1", GIT_ALLOW_PROTOCOL="https:http")
    cmd = ["git", "-c", "core.symlinks=false", "-c", "protocol.ext.allow=never", "clone", "--depth", "1", "--quiet"]
    if ref:
        cmd += ["--branch", ref]
    cmd += ["--", url, dest]
    try:
        proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except OSError as exc:
        raise ScanError(f"Gagal menjalankan git: {exc}")
    t0 = time.time()
    try:
        while proc.poll() is None:
            prog.check()
            el = time.time() - t0
            if el > 240:
                proc.kill()
                raise ScanError("git clone melewati batas waktu 240 detik.")
            prog.set(1 - math.exp(-el / 20), f"git clone {int(el)} dtk")
            time.sleep(0.1)
    except (ScanCancelled, ScanError):
        proc.kill()
        raise
    err = (proc.stderr.read() or b"").decode("utf-8", "ignore").strip().splitlines()
    if proc.returncode != 0:
        last = clean(err[-1]) if err else "kode keluar " + str(proc.returncode)
        raise ScanError(f"git clone gagal: {last[:120]}")


def acquire(target, work, prog):
    ws = {"root": None, "big": [], "links": [], "pruned": collections.Counter(),
          "truncated": False, "method": "", "unwritable": 0}
    if target["kind"] == "local":
        prog.begin(1, "Folder lokal - tanpa unduhan")
        prog.set(1.0)
        prog.begin(2, "Membaca langsung dari folder")
        prog.set(1.0)
        ws.update(root=target["root"], method="folder lokal")
        return ws
    errors = []
    root = os.path.join(work, "repo")
    arc = os.path.join(work, "repo.arc")
    prog.begin(1, "Menghubungi server")
    for url in target["archives"]:
        try:
            prog.begin(1, urllib.parse.urlparse(url).hostname or "")
            fetch_archive(url, arc, prog)
            prog.begin(2, "Membuka arsip")
            os.makedirs(root, exist_ok=True)
            info = extract_archive(arc, root, prog)
            ws.update(root=root, big=info["big"], links=info["links"], pruned=info["pruned"],
                      truncated=info["truncated"], unwritable=info["unwritable"], method="arsip (tanpa eksekusi)")
            return ws
        except ScanError as exc:
            errors.append(str(exc))
            if os.path.isdir(root):
                _rm(root)
    if target.get("clone"):
        try:
            prog.begin(1, "Cadangan: git clone")
            git_clone(target["clone"], target.get("ref"), root, prog)
            prog.begin(2, "Merapikan hasil clone")
            prog.set(1.0)
            ws.update(root=root, method="git clone --depth 1")
            return ws
        except ScanError as exc:
            errors.append(str(exc))
    raise ScanError(errors[0] if len(errors) == 1 else errors[0] + " | " + errors[-1])


def github_meta(target):
    url = f"https://api.github.com/repos/{target['owner']}/{target['name']}"
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=8) as r:
            d = json.load(r)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ScanError("Repo GitHub tidak ditemukan atau privat (HTTP 404). Periksa URL-nya.")
        return {"error": f"HTTP {exc.code}"}
    except (OSError, ValueError) as exc:
        return {"error": clean(str(exc))[:80]}
    lic = d.get("license") or {}
    return {
        "description": clean(d.get("description") or ""), "stars": d.get("stargazers_count", 0),
        "forks": d.get("forks_count", 0), "issues": d.get("open_issues_count", 0),
        "license": lic.get("spdx_id") or lic.get("name"), "archived": bool(d.get("archived")),
        "fork": bool(d.get("fork")), "created": d.get("created_at"), "pushed": d.get("pushed_at"),
        "language": d.get("language"), "default_branch": d.get("default_branch"),
        "size_kb": d.get("size"), "owner_type": (d.get("owner") or {}).get("type"),
    }


def _days_since(iso):
    try:
        t = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
        return (datetime.datetime.utcnow() - t).days
    except (TypeError, ValueError):
        return None


# ============================================================
# ANALISA ISI REPO
# ============================================================

LANG = {
    "py": "Python", "pyw": "Python", "js": "JavaScript", "mjs": "JavaScript", "cjs": "JavaScript",
    "jsx": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript", "java": "Java", "kt": "Kotlin",
    "go": "Go", "rs": "Rust", "c": "C", "h": "C/C++ Header", "cc": "C++", "cpp": "C++", "cxx": "C++",
    "hpp": "C++", "cs": "C#", "rb": "Ruby", "php": "PHP", "phtml": "PHP", "swift": "Swift",
    "sh": "Shell", "bash": "Shell", "zsh": "Shell", "ps1": "PowerShell", "psm1": "PowerShell",
    "bat": "Batch", "cmd": "Batch", "lua": "Lua", "pl": "Perl", "pm": "Perl", "r": "R", "dart": "Dart",
    "scala": "Scala", "groovy": "Groovy", "html": "HTML", "htm": "HTML", "css": "CSS", "scss": "CSS",
    "sass": "CSS", "less": "CSS", "vue": "Vue", "svelte": "Svelte", "sql": "SQL", "vbs": "VBScript",
    "asm": "Assembly", "s": "Assembly", "jl": "Julia", "ex": "Elixir", "exs": "Elixir", "zig": "Zig",
    "nim": "Nim", "m": "Objective-C", "mm": "Objective-C", "gradle": "Gradle", "hta": "HTA", "wsf": "WSH",
}
SHELL_EXT = {"sh", "bash", "zsh", "ps1", "psm1", "bat", "cmd", "vbs"}
SHELL_NAMES = {"dockerfile", "containerfile", "makefile", "gnumakefile"}
CODE_EXT = {e for e in LANG if e not in ("html", "htm", "css", "scss", "sass", "less", "sql")} | {"vbe"}
DOC_EXT = {"md", "rst", "txt", "adoc", "markdown"}
CFG_EXT = {"json", "yml", "yaml", "toml", "ini", "cfg", "conf", "xml", "csv", "tsv", "env", "properties", "lock"}
MEDIA_EXT = {"png", "jpg", "jpeg", "gif", "svg", "ico", "webp", "bmp", "mp3", "mp4", "wav", "ogg", "mov", "avi",
             "woff", "woff2", "ttf", "otf", "eot", "pdf"}
ARCH_EXT = {"zip", "tar", "gz", "tgz", "bz2", "xz", "7z", "rar"}
BIN_EXT = {"exe", "dll", "so", "dylib", "bin", "dat", "class", "jar", "apk", "pyc", "o", "a", "lib", "msi", "dmg", "iso"}
LOCK_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "go.sum",
              "composer.lock", "gemfile.lock", "pipfile.lock"}
DAMP_DIRS = {"test", "tests", "__tests__", "spec", "specs", "docs", "doc", "example", "examples", "sample",
             "samples", "fixtures", "fixture", "mocks", "mock", "demo", "demos", "testdata", "test_data",
             "benchmark", "benchmarks", "vendor", "third_party", "thirdparty", "extern", "external", "e2e"}
SENSITIVE_NAMES = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".npmrc", ".pypirc", ".netrc", ".git-credentials",
                   "credentials.json", "service-account.json", "secrets.yml", "secrets.yaml", "wallet.dat",
                   ".htpasswd", "terraform.tfstate"}
KEY_EXT = {"p12", "pfx", "jks", "keystore", "ppk"}
CI_NAMES = {".gitlab-ci.yml", "azure-pipelines.yml", ".travis.yml", "bitbucket-pipelines.yml", "jenkinsfile"}
NOISE_DOMAINS = {"www.w3.org", "schemas.microsoft.com", "json-schema.org", "schema.org", "xml.org",
                 "www.apache.org", "creativecommons.org", "opensource.org", "www.opensource.org", "www.gnu.org"}
SUSP_DOMAIN_RE = re.compile(
    r"^(?:\d{1,3}(?:\.\d{1,3}){3}|bit\.ly|tinyurl\.com|is\.gd|cutt\.ly|rb\.gy|goo\.gl|pastebin\.com|transfer\.sh|"
    r"anonfiles\.com|gofile\.io|0x0\.st|discord(?:app)?\.com|api\.telegram\.org|.*\.(?:ngrok\.io|ngrok-free\.app|"
    r"trycloudflare\.com|serveo\.net|loca\.lt))$")
DOMAIN_RE = re.compile(r"https?://([A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?)+)")
LIFECYCLE_SUSP = re.compile(r"\b(?:curl|wget|powershell|bash\s+-c|sh\s+-c|node\s+-e|eval|base64|nc\s)\b|https?://|\.exe\b", re.I)

PY_POP = ("requests", "numpy", "pandas", "urllib3", "setuptools", "django", "flask", "cryptography", "colorama",
          "beautifulsoup4", "pillow", "boto3", "pyyaml", "selenium", "scipy", "tensorflow", "matplotlib", "jinja2",
          "click", "pytest", "sqlalchemy", "fastapi", "aiohttp", "paramiko", "lxml", "scrapy", "tqdm", "rich",
          "pydantic", "httpx", "certifi")
NPM_POP = ("react", "lodash", "express", "axios", "chalk", "moment", "webpack", "typescript", "commander", "request",
           "debug", "colors", "jquery", "angular", "eslint", "prettier", "dotenv", "uuid", "mongoose", "cors",
           "passport", "bcrypt", "jsonwebtoken", "socket.io")


def ctx_factor(rel):
    p = rel.lower().replace("\\", "/")
    parts = p.split("/")
    base = parts[-1]
    ext = base.rsplit(".", 1)[-1] if "." in base else ""
    if any(x in DAMP_DIRS for x in parts[:-1]):
        return 0.25
    if ext in DOC_EXT:
        return 0.25
    if base.startswith("test_") or base.endswith(("_test.py", "_test.go", ".test.js", ".test.ts", ".spec.js", ".spec.ts")):
        return 0.25
    return 1.0


def group_of(ext, is_bin):
    if ext in LANG:
        return "Kode"
    if ext in DOC_EXT:
        return "Dokumen"
    if ext in CFG_EXT:
        return "Konfigurasi/Data"
    if ext in MEDIA_EXT:
        return "Media"
    if ext in ARCH_EXT:
        return "Arsip"
    if ext in BIN_EXT or is_bin:
        return "Biner"
    return "Lainnya"


def file_scopes(rel, lname, ext, text):
    scopes = ["text"]
    if ext in CODE_EXT or lname in SHELL_NAMES:
        scopes.append("code")
    if ext in SHELL_EXT or lname in SHELL_NAMES:
        scopes.append("shell")
    if ext in ("py", "pyw"):
        scopes.append("py")
    if ext in ("js", "mjs", "cjs", "ts", "jsx", "tsx"):
        scopes.append("js")
    if ext in ("php", "phtml"):
        scopes.append("php")
    if lname == "setup.py":
        scopes.append("setuppy")
    p = rel.lower()
    if ext in ("yml", "yaml") and (".github/workflows/" in p or ".circleci/" in p or lname in CI_NAMES):
        scopes.append("ci")
    if not ext and text.startswith("#!"):
        first = text.split("\n", 1)[0].lower()
        scopes.append("code")
        if "python" in first:
            scopes.append("py")
        elif "node" in first:
            scopes.append("js")
        elif "sh" in first or "bash" in first:
            scopes.append("shell")
        elif "php" in first:
            scopes.append("php")
    return scopes


def snippet_at(text, pos, end, mask):
    ls = text.rfind("\n", 0, pos) + 1
    le = text.find("\n", end)
    le = len(text) if le == -1 else le
    s = text[max(ls, pos - 30):min(le, end + 60)].strip()
    if mask == "token":
        tok = text[pos:end]
        s = s.replace(tok, tok[:4] + "ΓÇª[disembunyikan]")
    elif mask == "value":
        s = re.sub(r"([\"'])([^\"'\s]{3})[^\"'\s]*\1", r"\1\2ΓÇª***\1", s)
    elif mask == "dburl":
        s = re.sub(r"(://[^:\s/@]+):[^@\s]+@", r"\1:***@", s)
    return " ".join(s.split())[:140]


def detect_license(text):
    t = text[:4000].lower()
    checks = [
        ("GNU AGPL", "gnu affero general public license"), ("GNU LGPL", "gnu lesser general public license"),
        ("GNU GPL", "gnu general public license"), ("Apache-2.0", "apache license"),
        ("MIT", "permission is hereby granted, free of charge"), ("MPL-2.0", "mozilla public license"),
        ("Unlicense", "this is free and unencumbered software"), ("BSD", "redistribution and use in source and binary forms"),
        ("ISC", "permission to use, copy, modify, and/or distribute this software"),
    ]
    for name, key in checks:
        if key in t:
            return name
    return "Kustom / tidak dikenali"


def near_miss(a, b):
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diff) == 1:
            return True
        return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def _typo_check(F, rel, names, popular):
    pop = set(popular)
    for name in names:
        n = name.lower().replace("_", "-")
        if len(n) < 5 or n in pop:
            continue
        for p in popular:
            if near_miss(n, p):
                F.add(META["typosquat"], rel, 0, f"'{name}' mirip dengan '{p}'")
                break


def _read_small(path, limit=500_000):
    try:
        with open(path, "rb") as fh:
            return fh.read(limit).decode("utf-8", "replace")
    except OSError:
        return ""


def analyze_manifests(manifests, F, S):
    deps = collections.defaultdict(set)
    for rel, full in manifests[:60]:
        base = rel.rsplit("/", 1)[-1].lower()
        text = _read_small(full)
        if not text:
            continue
        try:
            if base.startswith("requirements") and base.endswith(".txt"):
                lines = [ln.split("#")[0].strip() for ln in text.splitlines()]
                lines = [ln for ln in lines if ln and not ln.startswith(("-r", "-c", "--"))]
                names, unpinned = [], 0
                for ln in lines:
                    if ln.startswith("-e"):
                        ln = ln[2:].strip()
                    if "http://" in ln:
                        F.add(META["dep-insecure"], rel, 0, ln[:100])
                    elif "git+" in ln or "://" in ln or " @ " in ln:
                        F.add(META["dep-vcs"], rel, 0, ln[:100])
                        continue
                    nm = re.split(r"[<>=!~\[;@ ]", ln)[0]
                    if nm:
                        names.append(nm)
                        if "==" not in ln:
                            unpinned += 1
                deps["Python (pip)"].update(names)
                _typo_check(F, rel, names, PY_POP)
                if len(names) >= 5 and unpinned / len(names) > 0.6:
                    F.add(META["dep-unpinned"], rel, 0, f"{unpinned}/{len(names)} paket tanpa versi terkunci (==)")
            elif base == "package.json":
                d = json.loads(text)
                if not isinstance(d, dict):
                    continue
                names = []
                for key in ("dependencies", "devDependencies", "optionalDependencies"):
                    for nm, val in (d.get(key) or {}).items():
                        names.append(nm)
                        v = str(val).lower()
                        if v.startswith(("github:", "git+", "git:", "http:", "https:", "git@")):
                            F.add(META["dep-vcs"], rel, 0, f"{nm} -> {str(val)[:70]}")
                        elif v in ("*", "latest"):
                            F.add(META["dep-unpinned"], rel, 0, f"{nm}: {val}")
                deps["JavaScript (npm)"].update(names)
                _typo_check(F, rel, names, NPM_POP)
                for hook in ("preinstall", "install", "postinstall"):
                    cmd = (d.get("scripts") or {}).get(hook)
                    if cmd:
                        rule = META["npm-hook-susp"] if LIFECYCLE_SUSP.search(str(cmd)) else META["npm-hook"]
                        F.add(rule, rel, 0, f"{hook}: {str(cmd)[:100]}")
            elif base == "pyproject.toml":
                names = []
                m = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)\]", text)
                if m:
                    names += [re.split(r"[<>=!~\[;@ ]", x)[0] for x in re.findall(r"[\"']([^\"']+)[\"']", m.group(1))]
                m = re.search(r"(?ms)^\[tool\.poetry\.dependencies\]\s*(.*?)(?=^\[|\Z)", text)
                if m:
                    names += [x for x in re.findall(r"(?m)^([A-Za-z0-9_.-]+)\s*=", m.group(1)) if x.lower() != "python"]
                deps["Python (pip)"].update(n for n in names if n)
                _typo_check(F, rel, [n for n in names if n], PY_POP)
            elif base == "go.mod":
                deps["Go (modules)"].update(re.findall(r"(?m)^\s*(?:require\s+)?([\w.\-]+\.[\w.\-/]+)\s+v[\w.\-+]+", text))
            elif base == "cargo.toml":
                for sec in re.findall(r"(?ms)^\[(?:dev-|build-)?dependencies\]\s*(.*?)(?=^\[|\Z)", text):
                    deps["Rust (cargo)"].update(re.findall(r"(?m)^([A-Za-z0-9_-]+)\s*=", sec))
            elif base == "gemfile":
                deps["Ruby (gem)"].update(re.findall(r"gem\s+[\"']([^\"']+)[\"']", text))
            elif base == "composer.json":
                d = json.loads(text)
                if isinstance(d, dict):
                    req = list((d.get("require") or {}).keys()) + list((d.get("require-dev") or {}).keys())
                    deps["PHP (composer)"].update(x for x in req if x != "php" and not x.startswith("ext-"))
        except (ValueError, TypeError, AttributeError):
            continue
    S["deps"] = {k: sorted(v) for k, v in deps.items() if v}


def analyze(ws, prog):
    root = ws["root"]
    F = Findings()
    S = {
        "files": 0, "bytes": 0, "text": 0, "binary": 0, "loc": 0,
        "lang": collections.defaultdict(lambda: [0, 0, 0]), "groups": collections.Counter(),
        "top": collections.Counter(), "largest": [], "binaries": [], "manifests": [], "deps": {},
        "domains": collections.Counter(), "ci": [], "docker": False, "license": None, "readme": False,
        "tests": False, "minified": 0, "hidden": [], "symlinks": 0, "truncated": bool(ws["truncated"]),
        "big_skipped": len(ws["big"]), "pruned": dict(ws["pruned"]), "unwritable": ws.get("unwritable", 0),
        "scanned_bytes": 0, "submodules": False,
    }

    # ---- tahap 3: peta berkas ----
    prog.begin(3, "Membaca struktur folder")
    entries = [(rel, None, size) for rel, size in ws["big"]]
    links = list(ws["links"])
    pruned = collections.Counter(ws["pruned"])
    for dp, dns, fns in os.walk(root, followlinks=False):
        prog.check()
        rel_dir = os.path.relpath(dp, root).replace(os.sep, "/")
        keep = []
        for d in dns:
            full = os.path.join(dp, d)
            if d in PRUNE_DIRS:
                if d != ".git" or rel_dir != ".":
                    pruned[d] += 1
                continue
            if os.path.islink(full):
                links.append((d if rel_dir == "." else rel_dir + "/" + d, os.readlink(full)))
                continue
            keep.append(d)
        dns[:] = keep
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = fn if rel_dir == "." else rel_dir + "/" + fn
            try:
                if os.path.islink(full):
                    links.append((rel, os.readlink(full)))
                    continue
                size = os.path.getsize(full)
            except OSError:
                continue
            entries.append((rel, full, size))
        if len(entries) >= MAX_FILES:
            S["truncated"] = True
            break
        prog.set(1 - math.exp(-len(entries) / 4000), f"{len(entries)} berkas ditemukan")
    entries.sort(key=lambda e: e[0])
    n = max(1, len(entries))

    # ---- tahap 4: pindai ----
    prog.begin(4, "Memulai pemindaian")
    t0 = time.time()
    for i, (rel, full, size) in enumerate(entries):
        if i % 20 == 0:
            prog.check()
            prog.set(i / n, clean(rel))
            prog.files, prog.findings = i, len(F)
        if time.time() - t0 > SCAN_TIME_LIMIT or S["scanned_bytes"] > 250 * 1024 * 1024:
            S["truncated"] = True
            break

        lname = rel.rsplit("/", 1)[-1].lower()
        ext = lname.rsplit(".", 1)[-1] if "." in lname else ""
        S["files"] += 1
        S["bytes"] += size
        S["top"][rel.split("/")[0] if "/" in rel else "(root)"] += 1
        if "/" not in rel and lname.startswith(".") and lname not in (".git",):
            S["hidden"].append(clean(rel))
        S["largest"].append((rel, size))
        parts = rel.lower().split("/")
        if any(p in ("test", "tests", "__tests__", "spec", "specs") for p in parts[:-1]) or \
                lname.startswith("test_") or lname.endswith(("_test.go", ".spec.js", ".test.js")):
            S["tests"] = True
        if lname.startswith("readme"):
            S["readme"] = True
        if lname == ".gitmodules":
            S["submodules"] = True

        if full is None:                          # berkas besar: hanya inventaris
            S["groups"][group_of(ext, False)] += 1
            continue
        try:
            with open(full, "rb") as fh:
                data = fh.read(MAX_SCAN_BYTES + 1)
        except OSError:
            continue
        cut = len(data) > MAX_SCAN_BYTES
        data = data[:MAX_SCAN_BYTES]
        S["scanned_bytes"] += len(data)
        head = data[:8192]

        if b"\0" in head:                         # ---- biner ----
            S["binary"] += 1
            S["groups"][group_of(ext, True)] += 1
            kind = None
            if head[:2] == b"MZ":
                kind = "Windows PE (exe/dll)"
            elif head[:4] == b"\x7fELF":
                kind = "Linux ELF"
            elif head[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf"):
                kind = "macOS Mach-O"
            elif ext in ("exe", "dll", "scr", "msi", "sys", "ocx"):
                kind = f".{ext} (biner)"
            if kind:
                F.add(META["bin-exec"], rel, 0, f"{kind}, {fmt_size(size)}")
                S["binaries"].append((clean(rel), kind, size))
            elif ext == "pyc":
                F.add(META["pyc"], rel, 0, "bytecode Python")
            elif ext in ("jar", "apk", "class", "aab", "dex", "ipa"):
                F.add(META["build-artifact"], rel, 0, f".{ext}, {fmt_size(size)}")
            elif ext in ARCH_EXT:
                F.add(META["embedded-archive"], rel, 0, f".{ext}, {fmt_size(size)}")
            if ext in KEY_EXT:
                F.add(META["sensitive-file"], rel, 0, "keystore/kunci biner")
            continue

        S["text"] += 1
        S["groups"][group_of(ext, False)] += 1
        if lname in LOCK_NAMES or lname.endswith((".min.js", ".min.css", ".map")):
            if lname not in LOCK_NAMES:
                S["minified"] += 1
                F.add(META["minified"], rel, 0, fmt_size(size))
            continue

        text = data.decode("utf-8", "replace")
        lines = text.count("\n") + 1
        if cut:
            lines = int(lines * size / MAX_SCAN_BYTES)
        S["loc"] += lines
        lang = LANG.get(ext)
        if lang is None and not ext and text.startswith("#!"):
            first = text.split("\n", 1)[0].lower()
            lang = "Python" if "python" in first else "JavaScript" if "node" in first else "Shell" if "sh" in first else None
        if lang:
            st = S["lang"][lang]
            st[0] += 1
            st[1] += lines
            st[2] += size
        lower = text.lower()
        factor = ctx_factor(rel)

        # nama berkas sensitif
        if lname in SENSITIVE_NAMES or lname.startswith("id_rsa"):
            if lname != ".npmrc" or "_authtoken" in lower:
                F.add(META["sensitive-file"], rel, 0, lname, factor)
        elif lname == ".env" or (lname.startswith(".env.") and not lname.endswith(("example", "sample", "template", "dist", "defaults"))):
            if re.search(r"(?m)^[A-Z][A-Z0-9_]*\s*=\s*[^\s#]{4,}", text):
                F.add(META["sensitive-file"], rel, 0, f"{lname} berisi nilai", factor)

        if lname.startswith(("license", "licence", "copying", "unlicense")) and S["license"] is None:
            S["license"] = detect_license(text)
        if lname in ("dockerfile", "containerfile") or lname.startswith("docker-compose"):
            S["docker"] = True
            if lname in ("dockerfile", "containerfile") and not re.search(r"(?im)^\s*USER\s+(?!root)\S+", text):
                F.add(META["docker-root"], rel, 0, "tidak ada instruksi USER non-root", factor)
        if lname in CI_NAMES or ".github/workflows/" in rel.lower() or ".circleci/" in rel.lower():
            S["ci"].append(clean(rel))
        if lname in ("package.json", "pyproject.toml", "go.mod", "cargo.toml", "gemfile", "composer.json") or \
                (lname.startswith("requirements") and lname.endswith(".txt")):
            S["manifests"].append((rel, full))
        elif lname in ("setup.py", "setup.cfg", "pipfile", "pom.xml", "build.gradle", "build.gradle.kts"):
            S["manifests"].append((rel, full))

        if "http" in lower and lname not in LOCK_NAMES:
            for d in set(DOMAIN_RE.findall(text)):
                S["domains"][d.lower()] += 1

        # ---- aturan regex ----
        for sc in file_scopes(rel, lname, ext, text):
            for rule in RULES_BY_SCOPE.get(sc, ()):
                if rule.maxlen and len(text) > rule.maxlen:
                    continue
                if rule.kw and not any(k in lower for k in rule.kw):
                    continue
                cnt, first = 0, None
                for m in rule.rx.finditer(text):
                    if rule.filt and not rule.filt(m):
                        continue
                    cnt += 1
                    if first is None:
                        first = (text.count("\n", 0, m.start()) + 1, snippet_at(text, m.start(), m.end(), rule.mask))
                    if cnt >= 60:
                        break
                if cnt:
                    F.add(rule, rel, first[0], first[1], factor, cnt)

    # ---- simlink & folder dependensi ----
    S["symlinks"] = len(links)
    for rel, target in links:
        t = str(target)
        if t.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", t) or ".." in t.replace("\\", "/").split("/"):
            F.add(META["symlink-out"], rel, 0, f"-> {t[:80]}")
    S["pruned"] = {k: v for k, v in pruned.items()}
    for d, c in pruned.items():
        if d != ".git":
            F.add(META["committed-deps"], d, 0, f"folder {d}/ ikut dikomit ({c} berkas)")
    if S["truncated"]:
        F.add(META["scan-truncated"], "(pemindaian)", 0, "batas ukuran/jumlah/waktu tercapai")

    # ---- tahap 5: dependensi ----
    prog.begin(5, "Membaca manifest paket")
    analyze_manifests(S["manifests"], F, S)
    prog.set(1.0)
    S["largest"] = sorted(S["largest"], key=lambda x: -x[1])[:6]
    S["manifests"] = [clean(r) for r, _ in S["manifests"]]
    return S, F


# ============================================================
# PERHITUNGAN RISIKO & PENYUSUNAN LAPORAN
# ============================================================

def contribution(rule, eff):
    w = SEV_W[rule.sev]
    return w * (eff if eff < 1 else min(1 + 0.6 * math.log(eff), 3.0))


def build_report(target, ws, S, F, meta, elapsed):
    # ---- metadata repo -> temuan ----
    if meta and not meta.get("error"):
        if not meta.get("license") and not S["license"]:
            F.add(META["no-license"], "(metadata)", 0, "tidak ada berkas/identitas lisensi")
        age = _days_since(meta.get("created"))
        if age is not None and age < 30 and meta.get("stars", 0) < 5:
            F.add(META["repo-new"], "(metadata)", 0, f"dibuat {age} hari lalu, {meta.get('stars', 0)} bintang")
        if meta.get("archived"):
            F.add(META["repo-archived"], "(metadata)", 0, "status: archived")
        idle = _days_since(meta.get("pushed"))
        if idle is not None and idle > 730:
            F.add(META["repo-stale"], "(metadata)", 0, f"push terakhir {idle // 365} tahun lalu")
        if meta.get("fork"):
            F.add(META["repo-fork"], "(metadata)", 0, "repo ini adalah fork")
    elif target["kind"] != "git" or not meta:
        if not S["license"] and target["kind"] != "local":
            F.add(META["no-license"], "(isi repo)", 0, "tidak ditemukan berkas LICENSE")

    # ---- skor ----
    items = []
    cat_raw = collections.Counter()
    sev_count = collections.Counter()
    total = 0.0
    mal = 0
    crit_mal = 0
    for fid, f in F.items():
        r = f["rule"]
        c = contribution(r, f["eff"])
        total += c
        cat_raw[r.cat] += c
        sev_count[r.sev] += 1
        items.append((c, f))
        if r.mal and f["eff"] >= 1.0:
            mal += 1
            if r.sev == "crit":
                crit_mal += 1
    danger = 100 * (1 - math.exp(-total / 60.0)) if total > 0 else 0.0
    if crit_mal >= 2:
        danger = max(danger, 85.0)
    elif crit_mal == 1:
        danger = max(danger, 70.0)
    danger = int(min(100, round(danger)))
    level = level_of(danger)
    cats = {k: int(round(100 * (1 - math.exp(-cat_raw[k] / 30.0)))) for k in CAT_NAMES if cat_raw.get(k)}

    items.sort(key=lambda x: (-x[0], SEV_ORDER.index(x[1]["rule"].sev)))
    sev_rank = {s: i for i, s in enumerate(SEV_ORDER)}
    findings = []
    for c, f in sorted(items, key=lambda x: (sev_rank[x[1]["rule"].sev], -x[0])):
        r = f["rule"]
        findings.append({
            "id": r.id, "name": r.name, "category": r.cat, "category_name": CAT_NAMES[r.cat],
            "severity": r.sev, "severity_label": SEV_LABEL[r.sev], "hits": f["hits"],
            "files": len(f["files"]), "score": round(c, 2), "malware_indicator": r.mal,
            "description": r.desc, "samples": f["samples"],
        })

    # ---- narasi ----
    secret_hits = sum(1 for f in findings if f["category"] == "SECRET" and f["severity"] in ("high", "crit"))
    summary = {
        "AMAN": "Tidak ditemukan pola berbahaya yang berarti. Tetap tinjau kode sebelum menjalankannya.",
        "RENDAH": "Hanya indikator ringan, umumnya pemakaian API sensitif yang wajar untuk sebuah tool.",
        "SEDANG": "Ada fitur/pola sensitif (eksekusi perintah, jaringan, dsb). Tinjau temuan sebelum memasang atau menjalankan.",
        "TINGGI": "Banyak indikator berisiko. Jalankan hanya di sandbox/VM/kontainer, dan periksa temuan utama dahulu.",
        "KRITIS": "Terdeteksi pola yang lazim pada malware. Sebaiknya JANGAN dijalankan di perangkat utama Anda.",
    }[level]
    notes = []
    if mal:
        notes.append(f"{mal} indikator khas malware terdeteksi (di luar konteks tes/dokumen).")
    elif level in ("RENDAH", "SEDANG"):
        notes.append("Tidak ada indikator malware yang jelas; temuan umumnya fitur sensitif yang lazim pada tool.")
    if secret_hits:
        notes.append(f"{secret_hits} jenis kredensial/kunci bocor ditemukan; anggap sudah terkompromi.")

    risks = []
    for c, f in items[:8]:
        if c <= 0:
            continue
        r = f["rule"]
        risks.append({"severity": r.sev, "title": r.name,
                      "detail": f"{r.desc} ({f['hits']}x di {len(f['files'])} berkas)"})
    advice = []
    seen = set()
    for f in findings:
        if f["category"] not in seen and f["severity"] in ("crit", "high", "med"):
            seen.add(f["category"])
            advice.append(CAT_ADVICE[f["category"]])
    if level in ("SEDANG", "TINGGI", "KRITIS"):
        advice.append("Uji di mesin terisolasi (VM/kontainer) tanpa kredensial pribadi sebelum memakai di perangkat utama.")
    advice.append("Pindai ini heuristik: cocokkan dengan peninjauan manual, terutama berkas yang ditandai.")

    # ---- kandungan ----
    loc_total = max(1, sum(v[1] for v in S["lang"].values()))
    languages = [{"name": k, "files": v[0], "lines": v[1], "pct": round(100 * v[1] / loc_total, 1)}
                 for k, v in sorted(S["lang"].items(), key=lambda kv: -kv[1][1])[:10]]
    domains = []
    for d, cnt in S["domains"].most_common(40):
        if d in NOISE_DOMAINS:
            continue
        domains.append({"domain": clean(d), "files": cnt, "suspicious": bool(SUSP_DOMAIN_RE.match(d))})
        if len(domains) >= 12:
            break
    contents = {
        "files": S["files"], "bytes": S["bytes"], "text_files": S["text"], "binary_files": S["binary"],
        "lines": S["loc"], "languages": languages, "groups": dict(S["groups"]),
        "top_dirs": [[clean(k), v] for k, v in S["top"].most_common(8)],
        "largest": [[clean(r), s] for r, s in S["largest"]],
        "binaries": [[p, k, s] for p, k, s in S["binaries"][:8]],
        "manifests": S["manifests"][:12],
        "dependencies": {k: {"count": len(v), "sample": v[:12]} for k, v in S["deps"].items()},
        "ci": S["ci"][:6], "docker": S["docker"], "license": S["license"], "readme": S["readme"],
        "tests": S["tests"], "domains": domains, "hidden": S["hidden"][:8],
        "pruned": S["pruned"], "minified": S["minified"], "symlinks": S["symlinks"],
        "big_skipped": S["big_skipped"], "truncated": S["truncated"], "submodules": S["submodules"],
    }
    return {
        "meta": {
            "tool": APP_NAME, "version": VERSION, "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "display": clean(target["display"]), "provider": target["provider"], "name": clean(target["name"]),
            "url": target.get("web"), "ref": clean(target["ref"]) if target.get("ref") else None,
            "method": ws["method"], "seconds": round(elapsed, 1),
        },
        "repo": meta if (meta and not meta.get("error")) else None,
        "verdict": {
            "danger": danger, "safe": 100 - danger, "level": level, "malware": mal,
            "counts": {s: sev_count.get(s, 0) for s in SEV_ORDER},
            "categories": cats, "summary": summary, "notes": notes,
        },
        "risks": risks, "advice": advice, "findings": findings, "contents": contents,
    }


# ============================================================
# RENDER LAPORAN  (teks polos untuk TUI, berkas .txt & layar)
# ============================================================

def _bar(pct, w=24):
    n = int(round(w * max(0, min(100, pct)) / 100))
    return "Γûê" * n + "Γûæ" * (w - n)


def render_lines(rep, width=96):
    out_lines = []
    width = max(40, width)

    def L(text="", kind="txt"):
        out_lines.append((text, kind))

    def P(text, kind="txt", ind=0, sub=None):
        sub = ind if sub is None else sub
        for ln in textwrap.wrap(text, width, initial_indent=" " * ind, subsequent_indent=" " * sub,
                                break_long_words=True) or [""]:
            L(ln, kind)

    def H(title):
        L()
        L(f"ΓöüΓöü {title} " + "Γöü" * max(2, width - len(title) - 4), "h")

    m, v, c = rep["meta"], rep["verdict"], rep["contents"]
    L("ΓòÉ" * width, "title")
    L(f"{APP_NAME}  ┬╖  LAPORAN SCAN REPO".center(width), "title")
    L("ΓòÉ" * width, "title")
    L(f"Target     : {m['display']}")
    L(f"Sumber     : {m['provider']}" + (f"  ┬╖  cabang/tag: {m['ref']}" if m["ref"] else ""))
    L(f"Metode     : {m['method']}  ┬╖  durasi {m['seconds']} dtk")
    L(f"Dibuat     : {m['generated'].replace('T', ' ')}  ┬╖  Genetic Tools v{m['version']}")

    H("RINGKASAN")
    L(f"PERSENTASE BAHAYA  : {v['danger']}%  {_bar(v['danger'])}  {v['level']}", f"L:{v['level']}")
    L(f"Skor keamanan      : {v['safe']}/100")
    L(f"Indikator malware  : {v['malware']} pola")
    cn = v["counts"]
    L(f"Temuan             : {cn['crit']} kritis ┬╖ {cn['high']} tinggi ┬╖ {cn['med']} sedang ┬╖ {cn['low']} rendah ┬╖ {cn['info']} info")
    L(f"Berkas dipindai    : {c['files']} berkas ┬╖ {fmt_size(c['bytes'])} ┬╖ ┬▒{c['lines']} baris kode/teks")
    L()
    P(v["summary"], f"L:{v['level']}")
    for note in v["notes"]:
        P("ΓÇó " + note, "txt", 0, 2)

    if v["categories"]:
        H("PROFIL RISIKO PER KATEGORI")
        for key, pct in sorted(v["categories"].items(), key=lambda kv: -kv[1]):
            L(f"{CAT_NAMES[key]:<30} {_bar(pct, 18)} {pct:>3}%", f"L:{level_of(pct)}")

    H("ANALISA & RESIKO")
    if not rep["risks"]:
        L("Tidak ada risiko signifikan yang terdeteksi.", "ok")
    for i, r in enumerate(rep["risks"], 1):
        L(f"{i}. [{SEV_LABEL[r['severity']]}] {r['title']}", r["severity"])
        P(r["detail"], "txt", 5)

    H("SARAN TINDAKAN")
    for a in rep["advice"]:
        P("ΓÇó " + a, "txt", 0, 2)

    H("TEMUAN DETAIL")
    shown = [f for f in rep["findings"] if f["severity"] != "info" or True]
    if not shown:
        L("Tidak ada temuan.", "ok")
    for f in shown:
        tag = "  ΓÜá indikator malware" if f["malware_indicator"] else ""
        L(f"[{f['severity_label']}] {f['name']}  ({f['id']}){tag}", f["severity"])
        P(f"{f['hits']} kemunculan di {f['files']} berkas ┬╖ {f['category_name']} ΓÇö {f['description']}", "dim", 4)
        for s in f["samples"][:3]:
            loc = f"{s['path']}:{s['line']}" if s["line"] else s["path"]
            extra = "  (konteks tes/dokumen)" if s["damped"] else ""
            P(f"{loc}  {s['snippet']}{extra}", "code", 6, 8)
        L()

    H("KANDUNGAN REPO")
    L(f"Total berkas   : {c['files']}  (teks {c['text_files']} ┬╖ biner {c['binary_files']})")
    L(f"Ukuran         : {fmt_size(c['bytes'])}")
    L(f"Baris          : ┬▒{c['lines']}")
    if c["groups"]:
        L("Jenis berkas   : " + " ┬╖ ".join(f"{k} {n}" for k, n in sorted(c["groups"].items(), key=lambda kv: -kv[1])))
    if c["languages"]:
        L()
        L("Bahasa pemrograman:", "h")
        for lg in c["languages"]:
            L(f"  {lg['name']:<16} {_bar(lg['pct'], 16)} {lg['pct']:>5.1f}%  {lg['files']} berkas ┬╖ {lg['lines']} baris")
    if c["top_dirs"]:
        L()
        L("Struktur teratas: " + "  ".join(f"{k}({n})" for k, n in c["top_dirs"]), "txt")
    L()
    yn = lambda b: "ya" if b else "tidak"
    L(f"Lisensi: {c['license'] or 'tidak ditemukan'}   ┬╖   README: {yn(c['readme'])}   ┬╖   Tes: {yn(c['tests'])}   ┬╖   Docker: {yn(c['docker'])}")
    if c["ci"]:
        P("CI/CD: " + ", ".join(c["ci"]), "txt", 0, 7)
    if c["hidden"]:
        P("Berkas tersembunyi di root: " + ", ".join(c["hidden"]), "dim", 0, 4)
    if c["manifests"]:
        P("Manifest paket: " + ", ".join(c["manifests"]), "txt", 0, 4)
    for eco, d in c["dependencies"].items():
        more = f" ΓÇª (+{d['count'] - len(d['sample'])})" if d["count"] > len(d["sample"]) else ""
        P(f"Dependensi {eco}: {d['count']} paket ΓÇö " + ", ".join(d["sample"]) + more, "txt", 0, 4)
    if c["binaries"]:
        L()
        L("Biner executable:", "med")
        for p, k, s in c["binaries"]:
            L(f"  {p}  [{k}, {fmt_size(s)}]", "code")
    if c["domains"]:
        L()
        L("Domain eksternal yang dirujuk:", "h")
        for d in c["domains"]:
            L(f"  {'ΓÜá' if d['suspicious'] else ' '} {d['domain']:<40} {d['files']} berkas", "high" if d["suspicious"] else "txt")
    if c["largest"]:
        L()
        L("Berkas terbesar: " + " ┬╖ ".join(f"{r} ({fmt_size(s)})" for r, s in c["largest"][:4]), "dim")
    skipped = []
    if c["pruned"]:
        skipped.append("folder dilewati: " + ", ".join(f"{k}/ ({n})" for k, n in c["pruned"].items()))
    if c["minified"]:
        skipped.append(f"{c['minified']} berkas minified/map")
    if c["big_skipped"]:
        skipped.append(f"{c['big_skipped']} berkas > {fmt_size(MAX_FILE_EXTRACT)} tidak diekstrak")
    if c["symlinks"]:
        skipped.append(f"{c['symlinks']} symlink tidak diikuti")
    if skipped:
        P("Tidak dipindai: " + "; ".join(skipped), "dim", 0, 4)
    if c["truncated"]:
        P("ΓÜá Pemindaian dipotong oleh batas ukuran/jumlah/waktu; hasil bisa tidak lengkap.", "med")

    if rep.get("repo"):
        r = rep["repo"]
        H("INFO REPOSITORI (GitHub API)")
        if r.get("description"):
            P(r["description"], "txt")
        L(f"Bintang {r.get('stars', 0)} ┬╖ Fork {r.get('forks', 0)} ┬╖ Isu terbuka {r.get('issues', 0)} ┬╖ Bahasa utama {r.get('language') or '-'}")
        L(f"Lisensi {r.get('license') or '-'} ┬╖ Dibuat {(r.get('created') or '-')[:10]} ┬╖ Push terakhir {(r.get('pushed') or '-')[:10]}")
        L(f"Branch utama {r.get('default_branch') or '-'} ┬╖ Pemilik {r.get('owner_type') or '-'}" +
          (" ┬╖ ARSIP" if r.get("archived") else "") + (" ┬╖ FORK" if r.get("fork") else ""))

    H("CATATAN & BATASAN")
    for t in (
        "Analisa bersifat statis & heuristik: kode repo TIDAK pernah dijalankan.",
        "Persentase bahaya = indikator risiko, bukan vonis. Temuan di folder tes/dokumen diberi bobot rendah.",
        "Tool sah bisa memicu temuan (mis. downloader memakai subprocess); tinjau konteks tiap temuan.",
        "Repo bersih dari pola bukan jaminan aman: tetap tinjau manual & jalankan di lingkungan terisolasi.",
        "Nilai rahasia yang terdeteksi disamarkan di laporan ini.",
    ):
        P("ΓÇó " + t, "dim", 0, 2)
    L()
    L("ΓÇö akhir laporan ΓÇö".center(width), "dim")
    return out_lines


# ============================================================
# PENGIRIMAN HASIL (berkas .txt & .json)
# ============================================================

def download_dir():
    for c in ("~/storage/downloads", "~/storage/shared/Download", "~/Downloads", "~/Download"):
        p = os.path.expanduser(c)
        if os.path.isdir(p) and os.access(p, os.W_OK):
            return p
    return None


def deliver(rep):
    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", rep["meta"]["name"]).strip("._")[:40] or "repo"
    base = f"scan_{slug}_{stamp}"
    paths = {"txt": os.path.join(REPORT_DIR, base + ".txt"), "json": os.path.join(REPORT_DIR, base + ".json")}
    with open(paths["txt"], "w", encoding="utf-8") as fh:
        fh.write("\n".join(t for t, _ in render_lines(rep, 100)) + "\n")
    with open(paths["json"], "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2)
    copies = []
    dd = download_dir()
    if dd:
        for p in paths.values():
            try:
                shutil.copy2(p, dd)
                copies.append(os.path.join(dd, os.path.basename(p)))
            except OSError:
                pass
    return {"txt": paths["txt"], "json": paths["json"], "copies": copies, "download_dir": dd}


def copy_clipboard(text):
    """Salin ke clipboard. Kembalikan nama metode, atau None bila tidak ada yang tersedia."""
    tools = [["termux-clipboard-set"], ["wl-copy"], ["xclip", "-selection", "clipboard"],
             ["xsel", "--clipboard", "--input"], ["pbcopy"]]
    for cmd in tools:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=10,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return cmd[0]
            except (OSError, subprocess.SubprocessError):
                continue
    if os.name == "nt" and shutil.which("clip"):
        try:
            subprocess.run(["clip"], input=text.encode("utf-16le"), check=True, timeout=10)
            return "clip"
        except (OSError, subprocess.SubprocessError):
            pass
    if len(text) <= 90000:   # cadangan: OSC 52 (didukung banyak terminal modern)
        import base64
        out("\033]52;c;" + base64.b64encode(text.encode("utf-8")).decode() + "\a")
        return "OSC52"
    return None


# ============================================================
# ALUR SCAN
# ============================================================

def run_scan(raw, prog):
    t0 = time.time()
    prog.begin(0, "Memeriksa input")
    target = parse_target(raw)
    meta = None
    if target["kind"] == "git" and target["host"] == "github.com":
        prog.set(0.4, "Membaca metadata GitHub")
        meta = github_meta(target)
    prog.set(1.0)
    work = tempfile.mkdtemp(prefix="gtscan_")
    try:
        ws = acquire(target, work, prog)
        S, F = analyze(ws, prog)
        prog.begin(6, "Menghitung persentase bahaya")
        rep = build_report(target, ws, S, F, meta, time.time() - t0)
        prog.set(1.0)
        prog.begin(7, "Menyusun berkas laporan")
        paths = deliver(rep)
        prog.set(1.0)
        prog.finish()
        return rep, paths
    finally:
        _rm(work)


class ScanJob:
    def __init__(self, raw):
        self.raw = raw
        self.prog = Progress()
        self.report = None
        self.paths = None
        self.error = None
        self.cancelled = False
        self.done = False
        self.finished_at = None
        self.disp = 0.0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            self.report, self.paths = run_scan(self.raw, self.prog)
        except ScanCancelled:
            self.cancelled = True
            self.error = "Scan dibatalkan."
        except ScanError as exc:
            self.error = str(exc)
        except Exception as exc:  # jaring pengaman terakhir
            self.error = f"Kesalahan tak terduga: {type(exc).__name__}: {clean(exc)}"
        self.done = True


# ============================================================
# APPLICATION
# ============================================================

class App:
    PAGES = ("tools", "about", "info")

    def __init__(self):
        self.keys = Keys()
        self.page = "menu"
        self.sel_menu = 0
        self.tick = 0.0
        self.started = time.time()
        self.msg = ("Sistem siap. Pilih TOOLS untuk scan repo.", NEON_S)
        self.has_git = bool(shutil.which("git"))
        self.url = ""
        self.example_idx = -1
        self.job = None
        self.report = None
        self.paths = None
        self.scroll = 0
        self.view_cache = (None, None)
        self.report_count = 0
        self.refresh_status()
        self.bg_rain = Rain(1.3, 0.6)
        self.boot_rain = Rain(2.6, 1.0)

    # ---------- status ----------
    def say(self, text, style=None):
        self.msg = (text, style or WHITE)

    def refresh_status(self):
        try:
            self.report_count = sum(1 for f in os.listdir(REPORT_DIR) if f.endswith(".txt"))
        except OSError:
            self.report_count = 0

    # ---------- scan control ----------
    def start_scan(self):
        raw = self.url.strip()
        try:
            parse_target(raw)
        except ScanError as exc:
            self.say(str(exc), RED_S)
            return
        self.job = ScanJob(raw)
        self.page = "scanning"
        self.say("Scanning dimulai... tekan ESC untuk membatalkan.", NEON_S)

    def cancel_job(self):
        if self.job and not self.job.done:
            self.job.prog.cancel = True

    def back_to_input(self, clear=True):
        self.cancel_job()
        self.job = None
        self.report = None
        self.view_cache = (None, None)
        if clear:
            self.url = ""
            self.example_idx = -1
        self.page = "tools"
        self.refresh_status()

    def update_scan(self, dt):
        job = self.job
        if not job:
            return
        target = 1.0 if (job.done and not job.error) else job.prog.ratio
        job.disp += (target - job.disp) * min(1.0, dt * 4.5)
        if abs(target - job.disp) < 0.004:
            job.disp = target
        if job.done and not job.error and job.disp >= 1.0:
            if job.finished_at is None:
                job.finished_at = time.time()
            elif time.time() - job.finished_at > 1.7:
                self.report, self.paths = job.report, job.paths
                self.scroll = 0
                self.view_cache = (None, None)
                self.page = "result"
                self.refresh_status()
                where = self.paths["copies"][0] if self.paths["copies"] else self.paths["txt"]
                self.say("Hasil terkirim: " + where, NEON_S)

    # ---------- loop ----------
    def boot(self):
        start = last = time.time()
        while True:
            now = time.time()
            dt = now - last
            last = now
            prog = min(1.0, (now - start) / BOOT_SECONDS)
            self.tick += dt * 2.0
            w, h = term_size()
            cv = Canvas(w, h)
            self.boot_rain.update(dt, w, h)
            self.boot_rain.draw(cv)
            draw_boot(cv, prog, self.tick)
            out(cv.frame())
            if self.keys.read(FRAME) is not None or now - start > BOOT_SECONDS + 0.6:
                break

    def run(self):
        with self.keys:
            out(ALT_ON + HIDE_CURSOR + CLEAR_ALL)
            try:
                self.boot()
                last = time.time()
                while True:
                    now = time.time()
                    dt = min(0.2, now - last)
                    last = now
                    self.tick += dt * 1.6
                    if self.page == "scanning":
                        self.update_scan(dt)
                    w, h = term_size()
                    cv = Canvas(w, h)
                    if w < MIN_W or h < MIN_H:
                        cv.center(h // 2, f"Perbesar terminal ke minimal {MIN_W}x{MIN_H}", RED_S)
                    else:
                        self.bg_rain.update(dt, w, h)
                        self.bg_rain.draw(cv)
                        self.draw_page(cv)
                    out(cv.frame())
                    key = self.keys.read(FRAME)
                    if key is not None and self.on_key(key):
                        break
            except KeyboardInterrupt:
                pass
            finally:
                self.cancel_job()
                out(RESET + SHOW_CURSOR + ALT_OFF)
        print(f"  Γùå {APP_NAME} ΓÇö sesi ditutup. Sampai jumpa!")

    def draw_page(self, cv):
        pages = {
            "menu": self.draw_menu,
            "tools": self.draw_input,
            "scanning": self.draw_scanning,
            "result": self.draw_result,
            "about": self.draw_about,
            "info": self.draw_info,
        }
        pages[self.page](cv)

    # ---------- menu ----------
    def draw_status(self, cv, x, y, w):
        panel(cv, x, y, w, 12, "SYSTEM STATUS", self.tick, CYAN_S)
        rows = [
            ("Platform", f"{platform.system()} {platform.machine()}", True),
            ("Python", platform.python_version(), True),
            ("Git", "tersedia" if self.has_git else "belum ada (opsional)", True),
            ("Pola", f"{len(RULES) + len(META)} aturan deteksi", True),
            ("Laporan", f"{self.report_count} tersimpan", True),
            ("Uptime", fmt_uptime(time.time() - self.started), True),
        ]
        for i, (label, value, ok) in enumerate(rows):
            cv.put(x + 3, y + 2 + i, f"{label:<10}", GREY)
            cv.put(x + 13, y + 2 + i, value[: w - 16], NEON_S if ok else RED_S)
        cv.put(x + 3, y + 9, "Folder laporan:", GREY)
        cv.put(x + 3, y + 10, REPORT_DIR[-(w - 6):], WHITE)

    def draw_menu(self, cv):
        draw_header(cv, f" Γùå {APP_NAME} v{VERSION} ",
                    f" ΓùÅ ONLINE  {datetime.datetime.now():%H:%M:%S} ", self.tick)
        two_col = cv.w >= 96
        cw = 50 if two_col else min(54, cv.w - 6)
        x = 5 if two_col else (cv.w - cw) // 2
        gap = 1 if cv.h >= 24 else 0

        y = 2
        if cv.h >= 26 and cv.w >= 60:
            draw_logo(cv, (cv.w - logo_width("GENETIC")) // 2, y, "GENETIC", self.tick)
            y += 6
        else:
            title = "G E N E T I C   T O O L S"
            cv.gradient((cv.w - len(title)) // 2, y, title, self.tick, BOLD)
            y += 2
        if cv.h >= 22:
            cv.center(y, "Repo scanner ┬╖ analisa bahaya, risiko & isi", GREY)
            y += 2

        cards_top = y
        for i, item in enumerate(MENU_ITEMS):
            draw_card(cv, x, y, cw, item, i + 1, i == self.sel_menu, self.tick)
            y += 3 + gap

        exit_sel = self.sel_menu == 3
        cv.put(x - 2, y, "Γû╢" if exit_sel else " ", mix(self.tick * 2.0))
        cv.put(x, y, "├ù  EXIT", RED_S if exit_sel else GREY)
        cv.put(x + 10, y, "(tekan 4 atau Q)", GREY)

        if two_col:
            sx = x + cw + 5
            self.draw_status(cv, sx, cards_top, cv.w - sx - 4)

        draw_msg(cv, self.msg)
        draw_hints(cv, cv.h - 1, [("ΓåæΓåô", "PILIH"), ("ENTER", "BUKA"),
                                  ("1-4", "PINTAS"), ("Q", "KELUAR")])

    # ---------- halaman input URL ----------
    def draw_input(self, cv):
        draw_header(cv, f" Γùå {APP_NAME}  ΓÇ║  TOOLS  ΓÇ║  SCAN REPO ", " MODE: SCAN REPO ", self.tick)
        pw = min(86, cv.w - 4)
        px = (cv.w - pw) // 2
        y = 2
        cv.gradient(px, y, "Γùå SCAN REPO", self.tick, BOLD)
        cv.put(px + 14, y, "analisa bahaya ┬╖ risiko ┬╖ isi repo", GREY)
        y += 2

        # kolom input
        edge = mix(self.tick * 2.0)
        cv.put(px, y, "Γò¡" + "ΓöÇ" * (pw - 2) + "Γò«", edge)
        cv.put(px, y + 2, "Γò░" + "ΓöÇ" * (pw - 2) + "Γò»", edge)
        cv.put(px, y + 1, "Γöé", edge)
        cv.put(px + pw - 1, y + 1, "Γöé", edge)
        cv.put(px + 2, y, " URL / PATH REPO ", YELLOW)
        label = "Γ₧£ "
        inner = pw - 6 - len(label)
        shown = self.url[-inner:] if len(self.url) > inner else self.url
        cv.put(px + 2, y + 1, label, NEON_S)
        if self.url:
            cv.put(px + 2 + len(label), y + 1, shown, WHITE)
        else:
            cv.put(px + 2 + len(label), y + 1, "tempel URL repo di sini..."[:inner], GREY)
        cursor = "Γûê" if int(time.time() * 2) % 2 == 0 else " "
        cv.put(px + 2 + len(label) + (len(shown) if self.url else 0), y + 1, cursor, NEON_S)
        y += 3

        # deteksi langsung
        if self.url.strip():
            try:
                t = parse_target(self.url)
                info = f"Γ£ö {t['provider']} ┬╖ {t['display']}"
                cv.put(px + 1, y, info[: pw - 2], NEON_C)
            except ScanError as exc:
                cv.put(px + 1, y, ("Γ£ÿ " + str(exc))[: pw - 2], RED)
        else:
            cv.put(px + 1, y, "Belum ada input. Tempel URL lalu tekan ENTER.", GREY)
        y += 2

        # panel arahan
        gh = cv.h - y - 3
        if gh >= 5:
            panel(cv, px, y, pw, gh, "ARAHAN INPUT URL REPO", self.tick, CYAN_S)
            cv.put(px + 3, y + 1, "Tempel (Ctrl+V / klik-kanan / tahan lalu Paste) ΓåÆ ENTER", WHITE)
            rows = gh - 3
            for i, (lab, ex) in enumerate(GUIDE[: max(0, rows - 1)]):
                cv.put(px + 3, y + 2 + i, f"{lab:<10}", NEON_S)
                cv.put(px + 13, y + 2 + i, ex[: pw - 16], WHITE)
            if rows >= 2:
                cv.put(px + 3, y + gh - 2, "ΓåæΓåô pilih contoh cepat ┬╖ CTRL+U hapus semua", GREY)

        draw_msg(cv, self.msg)
        draw_hints(cv, cv.h - 1, [("ENTER", "SCAN"), ("ΓåæΓåô", "CONTOH"), ("CTRL+U", "HAPUS"), ("ESC", "KEMBALI")])

    # ---------- halaman scanning ----------
    def draw_scanning(self, cv):
        job = self.job
        draw_header(cv, f" Γùå {APP_NAME}  ΓÇ║  SCANNING ", f" {int(job.disp * 100):3d}% ", self.tick)
        pw = min(72, cv.w - 4)
        ph = min(cv.h - 3, 19)
        px = (cv.w - pw) // 2
        py = max(1, (cv.h - ph) // 2)
        finished = job.done and not job.error and job.disp >= 1.0
        title = "SCAN SELESAI" if finished else ("SCAN GAGAL" if job.error else "SCANNING REPO")
        panel(cv, px, py, pw, ph, title, self.tick, RED_S if job.error else NEON_S)
        inner = pw - 8

        try:
            t = parse_target(job.raw)
            line1 = f"{t['provider']} ┬╖ {t['display']}"
        except ScanError:
            line1 = job.raw
        cv.put(px + 4, py + 2, "Target ", GREY)
        cv.put(px + 11, py + 2, clean(line1)[: inner - 7], WHITE)

        bw = pw - 14
        by = py + 4
        draw_scan_bar(cv, px + 4, by, bw, job.disp, self.tick, finished)
        pct = int(job.disp * 100)
        if finished:
            style = NEON_S if int(self.tick * 3) % 2 == 0 else WHITE + BOLD
        elif job.error:
            style = RED_S
        else:
            style = fg(*heat(job.disp)) + BOLD
        cv.put(px + 6 + bw, by, f"{pct:3d}%", style)

        prog = job.prog
        if job.error:
            cv.put(px + 4, py + 6, ("Γ£ÿ " + job.error)[:inner], RED_S)
            for i, ln in enumerate(textwrap.wrap(job.error, inner)[1:3]):
                cv.put(px + 6, py + 7 + i, ln, RED)
        elif finished:
            cv.put(px + 4, py + 6, "Γ£ö 100%  ┬╖  HASIL TERKIRIM", NEON_S)
            cv.put(px + 4, py + 7, os.path.basename(job.paths["txt"])[:inner], WHITE)
        else:
            cv.put(px + 4, py + 6, clean(prog.detail)[:inner], WHITE)
            cv.put(px + 4, py + 7, f"Berkas {prog.files} ┬╖ Temuan {prog.findings} ┬╖ {prog.mb:.1f} MB"[:inner], GREY)

        rows = max(0, ph - 11)
        if rows:
            cur = len(STAGES) if (finished or prog.complete) else prog.stage
            start = max(0, min(cur - 1, len(STAGES) - rows))
            spin = "|/-\\"[int(self.tick * 6) % 4]
            for r, idx in enumerate(range(start, min(len(STAGES), start + rows))):
                yy = py + 9 + r
                name = STAGES[idx][0]
                if idx < cur:
                    cv.put(px + 4, yy, "Γ£ö " + name, NEON_C)
                elif idx == cur and job.error:
                    cv.put(px + 4, yy, "Γ£ÿ " + name, RED_S)
                elif idx == cur:
                    cv.put(px + 4, yy, f"{spin} {name}...", WHITE)
                else:
                    cv.put(px + 4, yy, "Γùï " + name, GREY)

        if job.error:
            draw_hints(cv, cv.h - 1, [("ENTER", "KEMBALI KE INPUT"), ("Q", "KELUAR")])
        elif finished:
            cv.center(cv.h - 2, "membuka hasil...", GREY)
        else:
            draw_hints(cv, cv.h - 1, [("ESC", "BATALKAN"), ("Q", "KELUAR")])

    # ---------- halaman hasil ----------
    def result_lines(self, width):
        if self.view_cache[0] != width:
            self.view_cache = (width, render_lines(self.report, width))
        return self.view_cache[1]

    def draw_result(self, cv):
        rep = self.report
        v = rep["verdict"]
        lvl = v["level"]
        draw_header(cv, f" Γùå {APP_NAME}  ΓÇ║  HASIL SCAN ", f" {lvl} ┬╖ {v['danger']}% ", self.tick)

        # gauge tetap di atas
        cv.put(2, 2, "BAHAYA", GREY)
        cv.put(9, 2, f"{v['danger']:>3}%", LEVEL_STYLE[lvl])
        gw = max(10, min(40, cv.w - 40))
        draw_gauge(cv, 15, 2, gw, v["danger"], lvl)
        cv.put(16 + gw, 2, f"{lvl}", LEVEL_STYLE[lvl])
        tail = f"aman {v['safe']}/100 ┬╖ malware {v['malware']}"
        if 16 + gw + len(lvl) + len(tail) + 4 < cv.w:
            cv.put(cv.w - len(tail) - 2, 2, tail, GREY)
        cv.put(2, 3, clean(rep["meta"]["display"])[: cv.w - 4], WHITE)
        cv.put(2, 4, "ΓöÇ" * (cv.w - 4), GREEN_DARK)

        width = max(40, min(110, cv.w - 6))
        lines = self.result_lines(width)
        top, vh = 5, cv.h - 8
        self.scroll = max(0, min(self.scroll, max(0, len(lines) - vh)))
        cv.fill(0, top, cv.w, vh)
        for i in range(vh):
            idx = self.scroll + i
            if idx >= len(lines):
                break
            text, kind = lines[idx]
            cv.put(3, top + i, text[: cv.w - 6], style_for(kind))
        if len(lines) > vh:
            thumb = int(self.scroll / max(1, len(lines) - vh) * (vh - 1))
            for i in range(vh):
                cv.put(cv.w - 2, top + i, "Γöâ" if i == thumb else "Γöé", NEON_C if i == thumb else GREEN_DARK)
        cv.put(cv.w - 22, cv.h - 3, f"baris {min(len(lines), self.scroll + vh)}/{len(lines)}"[:20], GREY)

        draw_msg(cv, self.msg)
        draw_hints(cv, cv.h - 1, [("ΓåæΓåô", "GULIR"), ("PGUP/DN", "HALAMAN"), ("C", "SALIN"),
                                  ("ENTER", "SCAN LAGI"), ("Q", "KELUAR")])

    # ---------- about ----------
    def draw_about(self, cv):
        draw_header(cv, f" Γùå {APP_NAME}  ΓÇ║  ABOUT ", "", self.tick)
        pw = min(74, cv.w - 4)
        px = (cv.w - pw) // 2
        text = ("Genetic Tools adalah pemindai keamanan repository. Tempel URL repo, tekan ENTER, "
                "dan dalam hitungan detik Anda mendapat persentase bahaya, analisa risiko, serta "
                "rincian isi repo sebelum memasang atau menjalankannya. Cepat, ringan, tanpa "
                "dependency eksternal, dan kode repo tidak pernah dijalankan.")
        features = [
            "Scan GitHub, GitLab, Bitbucket, Codeberg, arsip & folder lokal",
            "Persentase bahaya + level risiko (Aman sampai Kritis)",
            f"{len(RULES) + len(META)} aturan deteksi: secret bocor, malware, obfuscation",
            "Analisa dependensi, hook instalasi, typosquatting & workflow CI",
            "Isi repo: bahasa, ukuran, biner, lisensi, domain eksternal",
            "Laporan .txt & .json siap salin atau unduh",
            "Kompatibel: Windows ┬╖ Linux ┬╖ Termux",
        ]
        body = textwrap.wrap(text, pw - 8)
        ph = min(cv.h - 4, len(body) + len(features) + 7)
        panel(cv, px, 2, pw, ph, "ABOUT GENETIC TOOLS", self.tick, YELLOW)
        y = 4
        for line in body:
            cv.put(px + 4, y, line, WHITE)
            y += 1
        y += 1
        cv.put(px + 4, y, "FITUR UTAMA", NEON_S)
        y += 1
        for feature in features:
            if y >= 2 + ph - 1:
                break
            cv.put(px + 4, y, "Γùå", NEON_S)
            cv.put(px + 6, y, feature[: pw - 10], WHITE)
            y += 1
        draw_hints(cv, cv.h - 1, [("B", "KEMBALI"), ("Q", "KELUAR")])

    # ---------- information ----------
    def draw_info(self, cv):
        draw_header(cv, f" Γùå {APP_NAME}  ΓÇ║  INFORMATION ", "", self.tick)
        pw = min(78, cv.w - 4)
        px = (cv.w - pw) // 2
        ph = min(cv.h - 4, 30)
        panel(cv, px, 2, pw, ph, "INFORMATION", self.tick, YELLOW)
        dd = download_dir()
        rows = [
            ("Versi", VERSION),
            ("Platform", f"{platform.system()} {platform.release()} ┬╖ {platform.machine()}"),
            ("Python", platform.python_version()),
            ("Git", "Γ£ö tersedia (cadangan clone)" if self.has_git else "Γ£ÿ belum ada (opsional)"),
            ("Aturan", f"{len(RULES)} pola regex + {len(META)} pemeriksaan meta"),
            ("Laporan", REPORT_DIR),
            ("Unduhan", dd or "belum ada (Termux: jalankan termux-setup-storage)"),
            ("Batas", f"arsip Γëñ {fmt_size(MAX_DOWNLOAD)} ┬╖ berkas Γëñ {fmt_size(MAX_FILE_EXTRACT)} ┬╖ {MAX_FILES} berkas"),
            ("Token", "GITHUB_TOKEN terdeteksi" if os.environ.get("GITHUB_TOKEN") else "GITHUB_TOKEN (opsional) untuk repo privat/limit"),
        ]
        lines = []
        for label, value in rows:
            lines.append((f"{label:<10}", value, GREY, WHITE))
        y = 4
        limit = 2 + ph - 1
        for label, value, ls, vs in lines:
            if y >= limit:
                break
            cv.put(px + 4, y, label, ls)
            cv.put(px + 15, y, value[: pw - 20], vs)
            y += 1

        y += 1
        blocks = [
            ("PINTASAN", [("ENTER", "scan repo / buka halaman"), ("Γåæ Γåô", "pilih contoh / gulir hasil"),
                          ("C", "salin laporan ke clipboard"), ("ESC", "kembali"), ("Q", "keluar")], True),
        ]
        for head, items, keyed in blocks:
            if y < limit:
                cv.put(px + 4, y, head, NEON_S)
                y += 1
            for key, txt in items:
                if y >= limit:
                    break
                cv.put(px + 4, y, f"{key:<8}", NEON_S)
                cv.put(px + 13, y, txt, WHITE)
                y += 1
        y += 1
        if y < limit:
            cv.put(px + 4, y, "CATATAN", NEON_S)
            y += 1
        notes = ("Analisa statis & heuristik: kode repo tidak dijalankan, diekstrak ke folder sementara "
                 "yang dihapus setelah scan. Persentase bahaya adalah indikator, bukan vonis; "
                 "tinjau juga secara manual.")
        for line in textwrap.wrap(notes, pw - 8):
            if y >= limit:
                break
            cv.put(px + 4, y, line, GREY)
            y += 1
        draw_hints(cv, cv.h - 1, [("B", "KEMBALI"), ("Q", "KELUAR")])

    # ---------- input ----------
    def open_page(self, idx):
        self.page = self.PAGES[idx]
        self.refresh_status()
        if self.page == "tools":
            self.say("Tempel URL repo lalu tekan ENTER.", NEON_S)

    def on_key(self, key):
        """Proses satu tombol. Mengembalikan True bila aplikasi harus keluar."""
        if self.page == "tools":
            return self.on_key_input(key)
        k = str(key).lower() if isinstance(key, Text) else key
        if k == "q":
            return True

        if self.page == "menu":
            if k in ("UP", "k"):
                self.sel_menu = (self.sel_menu - 1) % 4
            elif k in ("DOWN", "j"):
                self.sel_menu = (self.sel_menu + 1) % 4
            elif k in ("1", "2", "3"):
                self.sel_menu = int(k) - 1
                self.open_page(self.sel_menu)
            elif k == "4":
                return True
            elif k == "ENTER":
                if self.sel_menu == 3:
                    return True
                self.open_page(self.sel_menu)
        elif self.page == "scanning":
            job = self.job
            if job and job.error and k in ("ENTER", "ESC", "b", "LEFT"):
                self.back_to_input(clear=False)
                self.say(job.error if not job.cancelled else "Scan dibatalkan.", RED_S if not job.cancelled else WHITE)
            elif job and not job.done and k == "ESC":
                self.cancel_job()
        elif self.page == "result":
            lines_h = max(1, term_size()[1] - 8)
            if k == "UP":
                self.scroll -= 1
            elif k == "DOWN":
                self.scroll += 1
            elif k == "PGUP":
                self.scroll -= lines_h - 1
            elif k == "PGDN":
                self.scroll += lines_h - 1
            elif k == "HOME":
                self.scroll = 0
            elif k == "END":
                self.scroll = 10 ** 6
            elif k == "c":
                try:
                    with open(self.paths["txt"], "r", encoding="utf-8") as fh:
                        content = fh.read()
                    method = copy_clipboard(content)
                except OSError:
                    method = None
                if method == "OSC52":
                    self.say("Laporan dikirim ke clipboard terminal (jika didukung). File: " + self.paths["txt"], NEON_S)
                elif method:
                    self.say(f"Laporan tersalin ke clipboard ({method}).", NEON_S)
                else:
                    self.say("Clipboard tak tersedia. Salin dari file: " + self.paths["txt"], YELLOW)
            elif k in ("ENTER", "b", "ESC", "LEFT"):
                self.back_to_input(clear=True)
                self.say("Siap scan repo berikutnya. Tempel URL lalu ENTER.", NEON_S)
        elif k in ("b", "ESC", "LEFT", "BACK"):
            self.page = "menu"
        return False

    def on_key_input(self, key):
        if isinstance(key, Text):
            self.url = (self.url + str(key))[:300]
            self.example_idx = -1
            return False
        if key == "BACK":
            self.url = self.url[:-1]
        elif key == "CLEAR":
            self.url = ""
        elif key == "ESC":
            self.page = "menu"
        elif key in ("UP", "DOWN"):
            step = -1 if key == "UP" else 1
            self.example_idx = (self.example_idx + step) % len(EXAMPLES)
            self.url = EXAMPLES[self.example_idx]
            self.say("Contoh dimuat. Tekan ENTER untuk scan.", NEON_S)
        elif key == "ENTER":
            self.start_scan()
        return False


# ============================================================
# MODE LANGSUNG (tanpa antarmuka)
# ============================================================

def headless(raw):
    print(f"\n  {APP_NAME} v{VERSION} ΓÇö scan: {raw}\n")
    prog = Progress(echo=True)
    try:
        rep, paths = run_scan(raw, prog)
    except ScanError as exc:
        print(f"\n  Γ£ÿ {exc}")
        sys.exit(1)
    print()
    for text, _ in render_lines(rep, min(110, shutil.get_terminal_size((100, 24)).columns)):
        print(text)
    print(f"\n  Γ£ö 100%  ┬╖  hasil terkirim:\n    {paths['txt']}\n    {paths['json']}")
    for c in paths["copies"]:
        print(f"    (salinan) {c}")


# ============================================================
# MAIN
# ============================================================

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        headless(args[0])
        return
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print(f"{APP_NAME} harus dijalankan di terminal interaktif.")
        print(f"Atau pakai mode langsung:  python {os.path.basename(__file__)} <url-repo>")
        return
    os.makedirs(REPORT_DIR, exist_ok=True)
    App().run()


if __name__ == "__main__":
    main()
