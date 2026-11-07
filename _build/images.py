#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Επεξεργασία εικόνων για το pearlspa.gr.

Οι πηγαίες εικόνες (_build/src-img/) προέρχονται από διαφορετικές εποχές και
πηγές, οπότε περνούν όλες από το ίδιο φίλτρο ώστε να δένουν μεταξύ τους:

  1. ίσιωμα σε L (φωτεινότητα)
  2. απαλή S-καμπύλη αντίθεσης
  3. duotone στην παλέτα του site (μαύρο -> nacre, με ζεστό ροζ στους μεσαίους)
  4. επαναφορά ενός μικρού ποσοστού του αρχικού χρώματος, ώστε οι επιδερμίδες
     να μη μοιάζουν νεκρές

Τρέξιμο:  python3 _build/images.py
"""
import os
from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_build", "src-img")
OUT = os.path.join(ROOT, "assets", "img")

# ---------------------------------------------------------------- duotone ---
SHADOW = (10, 9, 8)          # σχεδόν μαύρο, ουδέτερο-ζεστό
MIDTONE = (128, 121, 113)    # ζεστό γκρι, χωρίς ροζ
HIGHLIGHT = (250, 248, 244)  # σχεδόν λευκό
COLOR_KEEP = 0.22            # πόσο από το αρχικό χρώμα επιστρέφει


def _ramp():
    """256 χρώματα από SHADOW -> MIDTONE -> HIGHLIGHT."""
    out = []
    for i in range(256):
        t = i / 255.0
        if t < 0.5:
            k = t / 0.5
            a, b = SHADOW, MIDTONE
        else:
            k = (t - 0.5) / 0.5
            a, b = MIDTONE, HIGHLIGHT
        out.append(tuple(round(a[c] + (b[c] - a[c]) * k) for c in range(3)))
    return out


RAMP = _ramp()
LUT_R = [c[0] for c in RAMP]
LUT_G = [c[1] for c in RAMP]
LUT_B = [c[2] for c in RAMP]


def _scurve(v):
    """Απαλή S-καμπύλη: ανοίγει τα highlights, κρατά βάθος στις σκιές."""
    t = v / 255.0
    t = t * t * (3 - 2 * t)          # smoothstep
    t = 0.04 + t * 0.94              # ελάχιστο lift — το βάθος μένει
    return max(0, min(255, round(t * 255)))


SCURVE = [_scurve(v) for v in range(256)]


def duotone(im):
    im = im.convert("RGB")
    grey = im.convert("L").point(SCURVE)
    toned = Image.merge("RGB", (
        grey.point(LUT_R), grey.point(LUT_G), grey.point(LUT_B)))
    if COLOR_KEEP > 0:
        soft = ImageEnhance.Color(im).enhance(0.45)
        toned = Image.blend(toned, soft, COLOR_KEEP)
    return toned


# ------------------------------------------------------------------ crops ---
def cover(im, ratio):
    """Κόβει στο ζητούμενο aspect ratio κρατώντας το κέντρο (ελαφρώς ψηλότερα,
    γιατί στις περισσότερες εικόνες το ενδιαφέρον είναι στο πάνω μισό)."""
    w, h = im.size
    target = ratio
    if w / h > target:
        nw = round(h * target)
        left = (w - nw) // 2
        box = (left, 0, left + nw, h)
    else:
        nh = round(w / target)
        top = round((h - nh) * 0.38)
        box = (0, top, w, top + nh)
    return im.crop(box)


# --------------------------------------------------------------- manifest ---
# name -> (source file, aspect ratio ή None για ό,τι είναι, [πλάτη])
WIDE = 16 / 9
PORTRAIT = 3 / 4
SQUARE = 1.0
LANDSCAPE = 4 / 3
CINEMA = 21 / 9        # ζώνες πλήρους πλάτους (hero, banners)
CARD = 4 / 5           # κάρτες θεραπειών στην αρχική

ASSETS = {
    # αρχική
    "hero-portrait":   ("prp.jpeg",             PORTRAIT,  [760, 1140]),
    "door-beauty":     ("therapies-prosopou.jpg", LANDSCAPE, [640, 1100]),
    "door-spa":        ("pearl6.jpg",           LANDSCAPE, [640, 1100]),
    "profil":          ("DSC_0226.jpg",         LANDSCAPE, [640, 1100]),

    # αρχική — ζώνες πλήρους πλάτους
    "hero-wide":       ("DSC_0226.jpg",         CINEMA, [700, 1000]),
    "band-offer":      ("slide_one.jpg",        CINEMA, [700, 1400]),
    "band-team":       ("3_Sisfiksi.jpg",       CINEMA, [700, 1400]),
    "band-cta":        ("DSC_0108.jpg",         CINEMA, [700, 1000]),

    # αρχική — κάρτες θεραπειών (κάθετες, σαν του προτύπου)
    "card-hifu":               ("13836740541784.jpg",  CARD, [560, 900]),
    "card-hydrafacial":        ("3_Sisfiksi.jpg",      CARD, [560, 900]),
    "card-kryolipolysi":       ("lipolaser.jpg",       CARD, [560, 900]),
    "card-laser-apotrixosi":   ("diodiko-laser.jpeg",  CARD, [560, 900]),
    "card-rf":                 ("beauty_face_a_01.jpg", CARD, [560, 900]),
    "card-aisthitiki-prosopou": ("therapies-prosopou.jpg", CARD, [560, 900]),

    # θεραπείες — πρόσωπο
    "aisthitiki-prosopou": ("therapies-prosopou.jpg", WIDE, [720, 1440]),
    "hydrafacial":     ("3_Sisfiksi.jpg",       WIDE, [720, 1440]),
    "peeling":         ("ximiko-peeling.jpeg",  WIDE, [720, 1440]),
    "rf":              ("beauty_face_a_01.jpg", WIDE, [720, 1440]),
    "hifu":            ("13836740541784.jpg",   WIDE, [720, 1440]),
    "btl":             ("pearl2.jpg",           WIDE, [720, 1440]),

    # θεραπείες — σώμα και αποτρίχωση
    "aisthitiki-somatos":  ("3_Sisfiksi.jpg",   WIDE, [720, 1440]),
    "kryolipolysi":    ("lipolaser.jpg",        WIDE, [720, 1440]),
    "lipolaser":       ("lipolaser.jpg",        WIDE, [720, 1440]),
    "laser":           ("diodiko-laser.jpeg",   WIDE, [720, 1440]),
    "apotrixosi":      ("laser.jpg",            WIDE, [720, 1440]),

    # θεραπείες — spa και ευεξία
    "spa":             ("pearl6.jpg",           WIDE, [720, 1440]),
    "diatrofi":        ("pearl3.jpg",           WIDE, [720, 1440]),

    # ο χώρος
    "choros-1":        ("DSC_0226.jpg",         LANDSCAPE, [560, 1000]),
    "choros-2":        ("DSC_0108.jpg",         LANDSCAPE, [560, 1000]),
    "choros-3":        ("DSC_0002.jpg",         LANDSCAPE, [560, 1000]),
    "choros-4":        ("pearl-spa4.jpg",       LANDSCAPE, [560, 1000]),
    "choros-5":        ("pearl6.jpg",           LANDSCAPE, [560, 1000]),
    "choros-6":        ("pearl1.jpg",           LANDSCAPE, [560, 1000]),

    # og image
    "og":              ("prp.jpeg",             1.91,      [1200]),
}


def build():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for name, (src, ratio, widths) in ASSETS.items():
        path = os.path.join(SRC, src)
        if not os.path.exists(path):
            print("  ! λείπει:", src)
            continue
        im = Image.open(path)
        im = duotone(im)
        if ratio:
            im = cover(im, ratio)
        for w in widths:
            if w > im.size[0]:
                r = im.copy()          # δεν μεγεθύνουμε πέρα από το πρωτότυπο
            else:
                h = round(im.size[1] * w / im.size[0])
                r = im.resize((w, h), Image.LANCZOS)
            r.save(os.path.join(OUT, f"{name}-{w}.webp"), "WEBP",
                   quality=80, method=6)
            r.save(os.path.join(OUT, f"{name}-{w}.jpg"), "JPEG",
                   quality=78, optimize=True, progressive=True)
            made += 2
    # καθάρισε ό,τι δεν ανήκει πια στο manifest
    keep = {f"{n}-{w}.{ext}"
            for n, (_, _, ws) in ASSETS.items() for w in ws
            for ext in ("webp", "jpg")}
    gone = 0
    for f in os.listdir(OUT):
        if f not in keep and f.rsplit(".", 1)[-1] in ("webp", "jpg"):
            os.remove(os.path.join(OUT, f))
            gone += 1
    print(f"  {made} αρχεία εικόνας -> assets/img/"
          + (f" ({gone} παλιά διαγράφηκαν)" if gone else ""))


if __name__ == "__main__":
    build()
