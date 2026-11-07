#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Στατικός generator για το pearlspa.gr.

    python3 _build/images.py     # μία φορά, ή όποτε αλλάξουν οι φωτογραφίες
    python3 _build/build.py      # κάθε φορά που αλλάζει κείμενο ή δομή

Γράφει HTML στη ρίζα του repo. Μην επεξεργάζεσαι τα παραγόμενα αρχεία —
άλλαξε το content.py (κείμενα), το pearl.css / pearl.js (μορφή) ή αυτό εδώ
(δομή) και ξανατρέξε.
"""
import os
import re
import json
import html
import shutil
import hashlib
from datetime import date

import content as C
try:
    from images import ASSETS as IMG_ASSETS
except Exception:                       # χωρίς Pillow το build τρέχει κανονικά
    IMG_ASSETS = {}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "_build")
TODAY = date.today().isoformat()

PAGES = []          # (path, lastmod_priority) για το sitemap


# ------------------------------------------------------------- βοηθητικά ---
def e(s):
    return html.escape(str(s), quote=True)


def write(path, text):
    full = os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def fingerprint(src_name, out_dir):
    """Αντιγράφει _build/<src> σε assets/<dir>/<name>.<hash>.<ext>."""
    src = os.path.join(BUILD, src_name)
    with open(src, "rb") as f:
        data = f.read()
    h = hashlib.sha1(data).hexdigest()[:10]
    stem, ext = os.path.splitext(src_name)
    out_rel = f"/assets/{out_dir}/{stem}.{h}{ext}"
    out_abs = os.path.join(ROOT, out_rel.lstrip("/"))
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    # καθάρισε παλιές εκδόσεις
    for old in os.listdir(os.path.dirname(out_abs)):
        if old.startswith(stem + ".") and old.endswith(ext) and old != os.path.basename(out_abs):
            os.remove(os.path.join(os.path.dirname(out_abs), old))
    shutil.copyfile(src, out_abs)
    return out_rel


def pic(name, widths, alt, sizes, cls="", eager=False):
    """<picture> με webp + jpg. Τα widths πρέπει να υπάρχουν στο images.py."""
    ws = sorted(widths)
    webp = ", ".join(f"/assets/img/{name}-{w}.webp {w}w" for w in ws)
    jpg = ", ".join(f"/assets/img/{name}-{w}.jpg {w}w" for w in ws)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (
        f'<picture{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>'
        f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">'
        f'<img src="/assets/img/{name}-{ws[-1]}.jpg" srcset="{jpg}" sizes="{sizes}" '
        f'alt="{e(alt)}" {load} decoding="async">'
        f'</picture>'
    )


def og_url(name):
    """Η μεγαλύτερη διαθέσιμη έκδοση της εικόνας, για το og:image."""
    widths = IMG_ASSETS.get(name, (None, None, [1200]))[2]
    return f"{C.SITE_URL}/assets/img/{name}-{max(widths)}.jpg"


def phone_link(cls="", label=None):
    return (f'<a class="{cls}" href="tel:{C.PHONE_TEL}">'
            f'<span>{e(label or "Ραντεβού " + C.PHONE_TXT)}</span></a>')


# ------------------------------------------------------------- κέλυφος -----
NAV = [
    ("/therapeies/", "Θεραπείες"),
    ("/prosfores/", "Προσφορές"),
    ("/o-choros/", "Ο χώρος"),
    ("/profil/", "Προφίλ"),
    ("/epikoinonia/", "Επικοινωνία"),
]


ICON_PHONE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 '
              '15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.58 1 1 '
              '0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 '
              '1 1 11.4 11.4 0 0 0 .57 3.6 1 1 0 0 1-.25 1z"/></svg>')

ICON_PIN = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M12 21s7-6.1 7-11a7 7 0 1 0-14 0c0 4.9 7 11 7 11z"/>'
            '<circle cx="12" cy="10" r="2.5"/></svg>')

ICON_LIST = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/></svg>')

with open(os.path.join(BUILD, "pearl-logo.svg"), encoding="utf-8") as _f:
    # Το λογότυπο ως inline SVG (από το _build/pearl-logo.svg, εξαγωγή από το
    # pearl_finalOUT.pdf). Το «Beauty 'n' Spa» παίρνει currentColor από το CSS.
    MARK = _f.read().strip()


def header(path, over=False):
    """Η κεφαλίδα: λογότυπο στο κέντρο, πλοήγηση δεξιά κι αριστερά.
    `over` = στέκεται πάνω σε σκούρα φωτογραφία, οπότε ξεκινά διάφανη."""
    nav = [x for x in NAV if x[0] != "/prosfores/" or C.OFFERS]
    half = (len(nav) + 1) // 2

    def links(items):
        out = []
        for href, label in items:
            cur = ' aria-current="page"' if path.startswith(href) else ""
            out.append(f'<a href="{href}"{cur}>{e(label)}</a>')
        return "".join(out)

    return f"""
<a class="skip" href="#main">Μετάβαση στο περιεχόμενο</a>
<header class="head{' head--over' if over else ''}">
  <div class="head__in">
    <div class="navwrap" id="nav">
      <nav class="nav nav--l" aria-label="Κύρια πλοήγηση">{links(nav[:half])}</nav>
      <nav class="nav nav--r" aria-label="Πλοήγηση, συνέχεια">{links(nav[half:])}</nav>
    </div>
    <a class="mark" href="/" aria-label="{e(C.BRAND)} — αρχική">{MARK}</a>
    <a class="btn btn--sm head__cta" href="tel:{C.PHONE_TEL}">
      {ICON_PHONE}<span>{e(C.PHONE_TXT)}</span></a>
    <button class="burger" type="button" aria-expanded="false"
            aria-controls="nav" aria-label="Άνοιγμα μενού">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<div class="bar">
  <a href="tel:{C.PHONE_TEL}">Τηλέφωνο</a>
  <a href="/epikoinonia/">Ραντεβού</a>
</div>"""


def footer():
    """Λευκό υποσέλιδο με στήλες συνδέσμων, όπως στο πρότυπο."""
    face = C.group_services("prosopo")
    rest = (C.group_services("soma") + C.group_services("apotrixosi")
            + C.group_services("eyexia"))
    cols = [
        ("Πρόσωπο", [(C.service_url(x), x["title"]) for x in face]
                    + [("/therapeies/", "Όλες οι θεραπείες")]),
        ("Σώμα & spa", [(C.service_url(x), x["title"]) for x in rest]),
        ("Ο χώρος", ([("/prosfores/", "Προσφορές")] if C.OFFERS else [])
                    + [("/profil/", "Προφίλ"), ("/o-choros/", "Ο χώρος"),
                       ("/epikoinonia/", "Ραντεβού"),
                       (C.FACEBOOK, "Facebook"), (C.INSTAGRAM, "Instagram")]),
    ]
    col_html = ""
    for title, items in cols:
        li = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for h, t in items)
        col_html += f"<div><h4>{e(title)}</h4><ul>{li}</ul></div>"

    hours = ""
    if C.HOURS:
        rows = "".join(f"<b>{e(lbl)}</b> {e(rng)}<br>" for lbl, rng, *_ in C.HOURS)
        hours = f"<br>{rows}"

    return f"""
<footer class="foot">
  <div class="wrap">
    <div class="foot__top">
      <div>
        <span class="mark">{MARK}</span>
        <address>
          <b>{e(C.STREET)}</b>
          {e(C.AREA)} {e(C.POSTAL)}<br>
          <a href="tel:{C.PHONE_TEL}">{e(C.PHONE_TXT)}</a><br>
          <a href="mailto:{C.EMAIL}">{e(C.EMAIL)}</a>{hours}
        </address>
        <div class="btns foot__cta">
          <a class="btn btn--sm" href="tel:{C.PHONE_TEL}">
            {ICON_PHONE}<span>Κλείστε ραντεβού</span></a>
        </div>
      </div>
      {col_html}
    </div>
    <div class="foot__bot">
      <span>© {date.today().year} {e(C.LEGAL)}</span>
      <span class="foot__legal">
        <a href="/cookies/">Cookies</a>
        <a href="/prosopika-dedomena/">Προσωπικά δεδομένα</a>
      </span>
      <span class="cb-credit">Made by <a
        href="https://clinicbrain.gr/?utm_source=client-site&amp;utm_medium=footer&amp;utm_campaign=made-by"
        target="_blank" rel="noopener noreferrer">CLINICBRAIN</a></span>
    </div>
  </div>
</footer>"""


FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Noto+Sans+Display:wdth,wght@62.5..100,300..600&"
         "family=Noto+Serif+Display:ital,wdth,wght@0,75..100,300..500;"
         "1,75..100,300..500&display=swap")


def render(path, title, desc, body, jsonld=None, og_img="og", priority="0.7",
           css="", js="", over_head=True):
    canonical = C.SITE_URL + path
    ld = ""
    if jsonld:
        ld = ('<script type="application/ld+json">'
              + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
              + "</script>")
    doc = f"""<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="website">
<meta property="og:locale" content="el_GR">
<meta property="og:site_name" content="{e(C.BRAND)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_url(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{css}">
{ld}
</head>
<body>
{header(path, over_head)}
<main id="main">
{body}
</main>
{footer()}
<script src="{js}" defer></script>
</body>
</html>"""
    write(os.path.join(path.strip("/"), "index.html") if path != "/" else "index.html", doc)
    PAGES.append((path, priority))


# --------------------------------------------------------------- JSON-LD ---
def business_ld():
    d = {
        "@context": "https://schema.org",
        "@type": ["HealthAndBeautyBusiness", "BeautySalon"],
        "@id": C.SITE_URL + "/#business",
        "name": C.BRAND,
        "legalName": C.LEGAL,
        "url": C.SITE_URL + "/",
        "telephone": C.PHONE_TEL,
        "email": C.EMAIL,
        "image": og_url("og"),
        "priceRange": "€€",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": C.STREET,
            "addressLocality": C.AREA,
            "postalCode": C.POSTAL,
            "addressRegion": C.REGION,
            "addressCountry": "GR",
        },
        "geo": {"@type": "GeoCoordinates",
                "latitude": C.GEO[0], "longitude": C.GEO[1]},
        "sameAs": [C.FACEBOOK, C.INSTAGRAM],
        **({"makesOffer": [
            {"@type": "Offer", "name": o["title"],
             "price": o["price"].replace("€", "").strip(),
             "priceCurrency": "EUR",
             "url": C.SITE_URL + "/prosfores/"} for o in C.OFFERS]}
           if C.OFFERS else {}),
        "availableService": [
            {"@type": "Service",
             "name": s["title"],
             "url": f"{C.SITE_URL}/{C.SECTIONS[s['section']]['slug']}/{s['slug']}/"}
            for s in C.SERVICES
        ],
    }
    if C.HOURS:
        d["openingHoursSpecification"] = [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": days,
             "opens": o, "closes": c}
            for _, _, days, o, c in C.HOURS
        ]
    return d


def crumbs_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             "item": C.SITE_URL + u}
            for i, (u, n) in enumerate(items)
        ],
    }


def graph(*nodes):
    return {"@context": "https://schema.org", "@graph": list(nodes)}


# ------------------------------------------------------------ κοινά μέρη ---
def offer_rows(limit=None):
    """Οι προσφορές ως κατάλογος: θεραπεία αριστερά, τιμή δεξιά."""
    rows = ""
    for o in (C.OFFERS[:limit] if limit else C.OFFERS):
        svc = C.offer_service(o)
        href = f"/{C.SECTIONS[svc['section']]['slug']}/{svc['slug']}/"
        rows += f"""
<article class="offer">
  <div class="offer__main">
    <h3 class="display d-s">{e(o["title"])}</h3>
    <p class="offer__short">{e(o["short"])}</p>
    <p class="offer__who">{e(C.OFFERS_WHO)}</p>
  </div>
  <p class="offer__price"><b>{e(o["price"])}</b><span>{e(o["unit"])}</span></p>
  <div class="offer__more">
    <ul>{''.join(f'<li>{e(i)}</li>' for i in o["includes"])}</ul>
    <div class="btns">
      <a class="btn" href="tel:{C.PHONE_TEL}"><span>Ραντεβού {e(C.PHONE_TXT)}</span></a>
      <a class="btn btn--ghost" href="{href}"><span>Η θεραπεία αναλυτικά</span></a>
    </div>
  </div>
</article>"""
    return rows


def cta_block(title, text, dark=True):
    """Η ζώνη κλεισίματος: φωτογραφία πλήρους πλάτους, σερίφ φράση, δύο χάπια."""
    return f"""
<section class="band cta">
  <div class="band__bg">
    {pic("band-cta", [700, 1000], "Ο χώρος του Pearl Beauty ’n’ Spa", "100vw")}
  </div>
  <div class="wrap">
    <p class="band__kicker">Ραντεβού</p>
    <h2 class="serif s-l">{title}</h2>
    <p class="lede">{text}</p>
    <div class="btns">
      <a class="btn btn--light" href="tel:{C.PHONE_TEL}">
        {ICON_PHONE}<span>{e(C.PHONE_TXT)}</span></a>
      <a class="btn btn--wire" href="/epikoinonia/">
        {ICON_PIN}<span>Πού θα μας βρείτε</span></a>
  </div>
  </div>
</section>"""


def index_block(services):
    """Το ευρετήριο θεραπειών: γραμμές με λεπτή γραμμή, και προεπισκόπηση."""
    groups = []
    for _, key, title in C.GROUPS:
        items = [s for s in services if s["group"] == key]
        if items:
            groups.append((key, title, items))

    rows_html = ""
    slides = ""
    first = True
    for key, title, items in groups:
        rows = ""
        for s in items:
            href = f"/{C.SECTIONS[s['section']]['slug']}/{s['slug']}/"
            thumb = pic(s["img"], [720], s["alt"], "104px", cls="row__thumb")
            rows += (
                f'<a class="row" href="{href}" data-key="{s["slug"]}">'
                f'<h3>{e(s["title"])}</h3>{thumb}'
                f'<p>{e(s["short"])}</p></a>'
            )
            slides += (f'<img data-key="{s["slug"]}" '
                       f'class="{"is-on" if first else ""}" '
                       f'src="/assets/img/{s["img"]}-720.jpg" alt="" '
                       f'loading="lazy" decoding="async">')
            first = False
        rows_html += (f'<div class="idx__group" id="{key}"><p class="idx__title">'
                      f'{e(title)}</p>{rows}</div>')

    return f"""
<div class="index">
  <div>{rows_html}</div>
  <div class="idx__col"><div class="idx__preview" aria-hidden="true">{slides}</div></div>
</div>"""


# ---------------------------------------------------------------- σελίδες --
def build_home(css, js):
    # οι κάρτες θεραπειών — τίτλος πάνω στη φωτογραφία, όπως στο πρότυπο
    cards = ""
    for slug in C.FEATURED:
        x = C.by_slug(slug)
        href = f"/{C.SECTIONS[x['section']]['slug']}/{x['slug']}/"
        cards += f"""
<a class="card2" href="{href}">
  {pic("card-" + slug, [560, 900], x["alt"],
       "(max-width:560px) 100vw, (max-width:1080px) 50vw, 33vw")}
  <div class="card2__txt">
    <h3>{e(x["title"])}</h3>
    <p>{e(x["short"])}</p>
  </div>
</a>"""

    doors = ""
    for d in C.DOORS:
        doors += f"""
      <a class="door" href="{d['href']}">
        <div class="door__img">{pic(d['img'], [640, 1100], d['alt'],
                                    "(max-width:900px) 100vw, 50vw")}</div>
        <p class="door__tag">{e(d['tag'])}</p>
        <h3>{e(d['title'])}</h3>
        <p>{e(d['lede'])}</p>
        <span class="door__go">{e(d['go'])}</span>
      </a>"""

    # η ζώνη προσφοράς — μόνο αν υπάρχει τρέχουσα προσφορά
    band_offer = ""
    if C.OFFERS:
        o = C.OFFERS[0]
        svc = C.offer_service(o)
        href = f"/{C.SECTIONS[svc['section']]['slug']}/{svc['slug']}/"
        more = ('<a class="btn btn--wire" href="/prosfores/">'
                '<span>Όλες οι προσφορές</span></a>' if len(C.OFFERS) > 1 else
                f'<a class="btn btn--wire" href="{href}">'
                f'<span>Η θεραπεία αναλυτικά</span></a>')
        band_offer = f"""
<section class="band">
  <div class="band__bg">
    {pic("band-offer", [700, 1400], "Θεραπεία προσώπου στο Pearl Beauty ’n’ Spa",
         "100vw")}
  </div>
  <div class="wrap">
    <p class="band__kicker">Προσφορά</p>
    <h2 class="display d-l">{e(o["title"])} <i>{e(o["price"])}</i></h2>
    <p class="lede">{e(o["short"])} {e(C.OFFERS_WHO)}</p>
    <div class="btns">
      <a class="btn btn--light" href="tel:{C.PHONE_TEL}">
        {ICON_PHONE}<span>{e(C.PHONE_TXT)}</span></a>
      {more}
  </div>
  </div>
</section>"""

    body = f"""
<section class="hero">
  <div class="hero__bg">
    {pic("hero-wide", [700, 1000], "Ο χώρος υποδοχής του Pearl Beauty ’n’ Spa",
         "100vw", eager=True)}
  </div>
  <div class="hero__in">
    <h1 class="serif s-xl rise">Η ομορφιά έχει βρει <em>τον χώρο της</em></h1>
    <p class="hero__by rise rise--2">Κέντρο αισθητικής &amp; spa — Γλυκά Νερά</p>
    <div class="btns btns--mid rise rise--2">
      <a class="btn btn--light" href="tel:{C.PHONE_TEL}">
        {ICON_PHONE}<span>Ραντεβού {e(C.PHONE_TXT)}</span></a>
      <a class="btn btn--wire" href="/therapeies/">
        {ICON_LIST}<span>Οι θεραπείες</span></a>
      <a class="btn btn--wire" href="/epikoinonia/">
        {ICON_PIN}<span>Πού θα μας βρείτε</span></a>
    </div>
    <p class="hero__where rise rise--3">{e(C.STREET)} · {e(C.AREA)} {e(C.POSTAL)}</p>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="sec__head">
      <h2 class="display d-l">αισθητική <i>προσώπου &amp; σώματος</i></h2>
      <p class="eyebrow">Οι θεραπείες που ζητούνται περισσότερο</p>
    </div>
    <div class="cards">{cards}</div>
    <div class="btns btns--mid" style="margin-top:clamp(2rem,3.5vw,3rem)">
      <a class="btn btn--ghost" href="/therapeies/"><span>Όλες οι θεραπείες</span></a>
    </div>
  </div>
</section>

{band_offer}

<section class="sec sec--shell">
  <div class="wrap">
    <div class="sec__head">
      <h2 class="display d-l">πρόσωπο, σώμα <i>και ευεξία</i></h2>
      <p class="lede">Ένα κέντρο αισθητικής και spa με μία ομάδα. Ό,τι γίνεται
      εδώ γίνεται χωρίς τομή, χωρίς βελόνα και χωρίς χρόνο αποκατάστασης — και
      κάθε πρόγραμμα σχεδιάζεται για εσάς, όχι από τον τιμοκατάλογο.</p>
    </div>
    <div class="doors">{doors}
    </div>
  </div>
</section>

<section class="band">
  <div class="band__bg">
    {pic("band-team", [700, 1400], "Θεραπεία προσώπου στο Pearl Beauty ’n’ Spa", "100vw")}
  </div>
  <div class="wrap">
    <p class="band__kicker">Η ομάδα</p>
    <h2 class="display d-l">μια ομάδα, <i>όχι ένα μηχάνημα</i></h2>
    <p class="lede">Κάθε πρόγραμμα σχεδιάζεται από ανθρώπους που μιλούν μεταξύ
    τους: αισθητικοί, φυσικοθεραπευτές, γυμναστές και διαιτολόγος, κάτω από την
    ίδια στέγη.</p>
    <dl class="stats">
      <div><dt>τέσσερις ειδικότητες</dt><dd>Στην ίδια ομάδα</dd></div>
      <div><dt>μία στέγη</dt><dd>Αισθητική, spa και διατροφή</dd></div>
      <div><dt>ένα πλάνο</dt><dd>Για κάθε πρόγραμμα, από την αρχή</dd></div>
    </dl>
    <div class="btns">
      <a class="btn btn--light" href="/profil/"><span>Το προφίλ μας</span></a>
  </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <div class="claim">
      <figure class="claim__fig" style="margin:0">
        {pic("profil", [640, 1100], "Ο χώρος υποδοχής του Pearl Beauty ’n’ Spa",
             "(max-width:1080px) 100vw, 36vw")}
      </figure>
      <div>
        <h2 class="display d-m">η ιστορία <i>του χώρου</i></h2>
        <div class="prose" style="margin-top:1.5rem">
          <p>Το Pearl Beauty ’n’ Spa είναι κέντρο αισθητικής και spa στα Γλυκά
          Νερά. Ο χώρος είναι εξοπλισμένος με μηχανήματα τελευταίας τεχνολογίας, αλλά αυτό
          δεν είναι το ενδιαφέρον κομμάτι: το ενδιαφέρον είναι ότι κάθε
          πρόγραμμα σχεδιάζεται από ανθρώπους που μιλούν μεταξύ τους.</p>
          <p>Η ομάδα αποτελείται από {e(C.TEAM)}. Και όταν μια θεραπεία σώματος
          χρειάζεται διατροφική υποστήριξη για να αποδώσει, δεν σας στέλνουμε
          αλλού.</p>
        </div>
        <dl class="facts">
          <div><dt>Διεύθυνση</dt><dd>{e(C.STREET)}, {e(C.AREA)} {e(C.POSTAL)}</dd></div>
          <div><dt>Ραντεβού</dt><dd><a href="tel:{C.PHONE_TEL}">{e(C.PHONE_TXT)}</a></dd></div>
          <div><dt>Η ομάδα</dt><dd>{e(C.TEAM_SHORT)}</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>

{cta_block("Κλείστε το <em>πρώτο σας ραντεβού</em>",
           "Το πρώτο ραντεβού είναι εκτίμηση και κουβέντα για το τι έχει νόημα "
           "να γίνει — όχι υποχρέωση για πακέτο.")}
"""
    render("/", f"{C.BRAND} | Κέντρο αισθητικής & spa στα Γλυκά Νερά",
           "Αισθητική προσώπου και σώματος, αποτρίχωση, θεραπείες spa και "
           "διατροφική υποστήριξη στα Γλυκά Νερά. HIFU, Hydrafacial, RF, laser "
           "αποτρίχωση, κρυολιπόλυση, ayurveda. Ραντεβού τηλεφωνικά.",
           body,
           jsonld=graph(
               business_ld(),
               {"@type": "WebSite", "@id": C.SITE_URL + "/#website",
                "url": C.SITE_URL + "/", "name": C.BRAND,
                "inLanguage": "el-GR",
                "publisher": {"@id": C.SITE_URL + "/#business"}},
           ),
           priority="1.0", css=css, js=js)


def build_section(key, css, js):
    sec = C.SECTIONS[key]
    services = C.section_services(key)
    intro = """
        <p>Όλες οι θεραπείες του χώρου, σε τέσσερις ομάδες: πρόσωπο, σώμα,
        αποτρίχωση και ευεξία. Καμία δεν χρειάζεται τομή, βελόνα ή χρόνο
        αποκατάστασης — και όλες εκτελούνται από την ομάδα του χώρου:
        αισθητικούς, φυσικοθεραπευτές και διαιτολόγο.</p>
        <p>Κάθε θεραπεία ξεκινά με εκτίμηση. Αν αυτό που ζητάτε δεν είναι το
        κατάλληλο για εσάς, θα σας το πούμε στο πρώτο ραντεβού — μαζί με το τι
        θα ήταν.</p>"""

    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>{e(sec["title"])}</p>
      <h1 class="display d-xl">{e(sec["title"])}</h1>
      <p class="lede">{e(sec["lede"])}</p>
  </div>
</section>

<section class="sec" style="padding-top:clamp(2.5rem,5vw,4rem)">
  <div class="wrap">
    <div class="prose" style="max-width:62ch;padding-bottom:clamp(2.5rem,5vw,4rem)">
      {intro}
    </div>
    {index_block(services)}
  </div>
</section>

{cta_block("Ρωτήστε πρώτα.",
           "Ένα τηλεφώνημα αρκεί για να καταλάβετε αν αυτό που ψάχνετε γίνεται "
           "εδώ και τι περιλαμβάνει.")}
"""
    render(f"/{sec['slug']}/",
           f"{sec['title']} | {C.BRAND}",
           sec["lede"][:155],
           body,
           jsonld=graph(
               crumbs_ld([("/", "Αρχική"), (f"/{sec['slug']}/", sec["title"])]),
               {"@type": "CollectionPage", "name": sec["title"],
                "url": f"{C.SITE_URL}/{sec['slug']}/",
                "isPartOf": {"@id": C.SITE_URL + "/#website"},
                "about": {"@id": C.SITE_URL + "/#business"}},
           ),
           og_img=sec["img"], priority="0.9", css=css, js=js)


def build_service(s, css, js):
    sec = C.SECTIONS[s["section"]]
    path = f"/{sec['slug']}/{s['slug']}/"

    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>"
                    for k, v in s["facts"])

    siblings = [x for x in C.section_services(s["section"])
                if x["group"] == s["group"] and x["slug"] != s["slug"]][:3]
    if len(siblings) < 3:
        extra = [x for x in C.section_services(s["section"])
                 if x["slug"] != s["slug"] and x not in siblings]
        siblings += extra[:3 - len(siblings)]
    rel = ""
    for x in siblings:
        xh = f"/{C.SECTIONS[x['section']]['slug']}/{x['slug']}/"
        rel += (f'<a href="{xh}"><h3>{e(x["title"])}</h3>'
                f'<p>{e(x["short"])}</p><span>Δείτε τη θεραπεία</span></a>')

    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb">
      <a href="/">Αρχική</a><span>/</span>
      <a href="/{sec['slug']}/">{e(sec['title'])}</a><span>/</span>{e(s['title'])}
    </p>
      <h1 class="display d-l">{e(s["title"])}</h1>
      <p class="lede">{e(s["lede"])}</p>
  </div>
</section>

<div class="wrap">
  <figure class="pfig" style="margin:0">
    {pic(s["img"], [720, 1440], s["alt"], "(max-width:1440px) 100vw, 1440px",
         eager=True)}
  </figure>
</div>

<section class="sec">
  <div class="wrap">
    <div class="pbody">
      <div class="prose">{s["body"]}</div>
      <aside class="pbody__side">
        <dl class="facts">{facts}</dl>
        <div class="callout">
          <strong>Κλείστε ραντεβού</strong>
          <p>Η εκτίμηση γίνεται πάντα από κοντά. Τηλεφωνήστε μας και θα βρούμε
          μαζί τι είναι το σωστό για εσάς.</p>
          <div class="btns">
            <a class="btn btn--light" href="tel:{C.PHONE_TEL}">
              <span>{e(C.PHONE_TXT)}</span></a>
          </div>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="sec sec--dark sec--tight">
  <div class="wrap">
    <div class="sec__head">
      <h2 class="display d-m">Σχετικές θεραπείες</h2>
      <p>Οι θεραπείες σπάνια δουλεύουν μόνες τους. Αυτές συνδυάζονται συχνά με
      την προηγούμενη, ή αποτελούν την εναλλακτική της.</p>
    </div>
    <div class="feat">{rel}</div>
  </div>
</section>
"""
    ld_type = "Service"
    render(path, f"{s['title']} | {sec['title']} — {C.BRAND}",
           s["short"][:155], body,
           jsonld=graph(
               crumbs_ld([("/", "Αρχική"), (f"/{sec['slug']}/", sec["title"]),
                          (path, s["title"])]),
               {"@type": ld_type, "name": s["title"],
                "url": C.SITE_URL + path,
                "description": s["short"],
                "image": og_url(s["img"]),
                "provider": {"@id": C.SITE_URL + "/#business"}},
           ),
           og_img=s["img"], priority="0.8", css=css, js=js)


def build_offers(css, js):
    if not C.OFFERS:
        return
    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>Προσφορές</p>
      <h1 class="display d-xl">Προσφορές</h1>
      <p class="lede">Τρέχουσες τιμές σε συγκεκριμένες θεραπείες. Ό,τι
      γράφεται εδώ ισχύει όπως γράφεται — χωρίς αστερίσκους.</p>
  </div>
</section>

<section class="sec" style="padding-top:clamp(2.5rem,5vw,4rem)">
  <div class="wrap">
    <div class="offers">{offer_rows()}</div>
    <p class="offers__note">{e(C.OFFERS_NOTE)}</p>
  </div>
</section>

<section class="sec sec--shell sec--tight">
  <div class="wrap">
    <div class="sec__head">
      <h2 class="display d-m">Πώς δουλεύει<br>μια προσφορά</h2>
      <p>Η τιμή είναι για τη συγκεκριμένη θεραπεία, όπως περιγράφεται — χωρίς
      κρυφές προϋποθέσεις.</p>
    </div>
    <div class="prose" style="max-width:62ch">
      <p>Κάθε προσφορά εφαρμόζεται από την ομάδα του χώρου, με την ίδια
      διαδικασία που ακολουθούμε σε κάθε ραντεβού: προηγείται εκτίμηση, και αν
      η θεραπεία δεν σας ταιριάζει, θα σας το πούμε πριν προχωρήσουμε.</p>
    </div>
  </div>
</section>

{cta_block("Κλείστε το ραντεβού σας.",
           "Οι θέσεις για τις θεραπείες με προσφορά είναι περιορισμένες ανά "
           "εβδομάδα, γιατί τις εκτελεί ιατρός.")}
"""
    offers_ld = [{
        "@type": "Offer",
        "name": o["title"],
        "description": o["short"],
        "price": o["price"].replace("€", "").strip(),
        "priceCurrency": "EUR",
        "url": f"{C.SITE_URL}/prosfores/",
        "availability": "https://schema.org/InStock",
        "seller": {"@id": C.SITE_URL + "/#business"},
        "itemOffered": {
            "@type": "Service",
            "name": C.offer_service(o)["title"],
            "url": (f"{C.SITE_URL}/"
                    f"{C.SECTIONS[C.offer_service(o)['section']]['slug']}/"
                    f"{C.offer_service(o)['slug']}/"),
        },
        **({"priceValidUntil": o["valid_until"]} if o.get("valid_until") else {}),
    } for o in C.OFFERS]

    render("/prosfores/", f"Προσφορές | {C.BRAND}",
           "Τρέχουσες προσφορές σε θεραπείες του Pearl Beauty ’n’ Spa στα Γλυκά "
           "Νερά.",
           body,
           jsonld=graph(
               crumbs_ld([("/", "Αρχική"), ("/prosfores/", "Προσφορές")]),
               {"@type": "CollectionPage", "name": "Προσφορές",
                "url": C.SITE_URL + "/prosfores/",
                "about": {"@id": C.SITE_URL + "/#business"}},
               *offers_ld,
           ),
           og_img=C.OFFERS[0]["img"], priority="0.9", css=css, js=js,
           )


def build_profil(css, js):
    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>Προφίλ</p>
      <h1 class="display d-xl">Προφίλ</h1>
      <p class="lede">Ένα κέντρο αισθητικής και spa στα Γλυκά Νερά, με μία
      ομάδα από τέσσερις ειδικότητες.</p>
  </div>
</section>

<section class="sec" style="padding-top:clamp(2rem,4vw,3rem)">
  <div class="wrap">
    <div class="claim">
      <div class="prose">
        <h2>Τι είναι ο χώρος</h2>
        <p>Στο Pearl Beauty ’n’ Spa η ομορφιά έχει βρει τον δικό της χώρο. Με
        υψηλής ποιότητας υπηρεσίες στην αισθητική προσώπου και σώματος, σας
        δίνει τη δυνατότητα να χαλαρώσετε και να νιώσετε ευεξία — με
        πρόγραμμα σχεδιασμένο για εσάς και όχι από τον τιμοκατάλογο.</p>
        <p>Ο χώρος είναι εξοπλισμένος με μηχανήματα τελευταίας τεχνολογίας,
        ώστε να ανταποκρίνεται με εξατομικευμένα προγράμματα στις προσωπικές σας
        ανάγκες.</p>

        <h2>Η ομάδα</h2>
        <p>Η εξειδικευμένη ομάδα του αποτελείται από {e(C.TEAM)}. Αυτό δεν
        είναι λίστα τίτλων· είναι ο λόγος που ένα πρόγραμμα σώματος μπορεί να
        συνδυάσει θεραπεία, άσκηση και διατροφή χωρίς να χρειαστεί να τρέξετε
        σε τρία διαφορετικά σημεία της Αττικής.</p>
        <p>Κάθε θεραπεία εκτελείται από τον άνθρωπο που την ξέρει καλύτερα:
        οι θεραπείες προσώπου και σώματος από αισθητικούς, οι θεραπείες spa από
        αισθητικούς και φυσικοθεραπευτές, η διατροφή από τη διαιτολόγο.</p>

        <h2>Πώς δουλεύουμε</h2>
        <ul>
          <li><strong>Πρώτα η εκτίμηση.</strong> Κάθε νέο ραντεβού ξεκινά με
          εκτίμηση και κουβέντα, όχι με τιμοκατάλογο.</li>
          <li><strong>Ένα σχέδιο, όχι μια θεραπεία.</strong> Σας λέμε πόσες
          συνεδρίες χρειάζονται ρεαλιστικά και τι θα φανεί σε ποιο διάστημα.</li>
          <li><strong>Ό,τι δεν ενδείκνυται, δεν γίνεται.</strong> Αν κάτι δεν
          ταιριάζει στην περίπτωσή σας, θα το ακούσετε πριν πληρώσετε.</li>
          <li><strong>Μετρήσεις, όχι εντυπώσεις.</strong> Στα προγράμματα
          σώματος επαναλαμβάνουμε τις μετρήσεις σε όλη τη διάρκεια.</li>
        </ul>

        <h2>Τι θα βρείτε εδώ</h2>
        <p>Οι <a href="/therapeies/">θεραπείες</a> καλύπτουν το πρόσωπο
        (καθαρισμός, Hydrafacial, peeling, RF, HIFU, μη ενέσιμη μεσοθεραπεία),
        το σώμα (αισθητική σώματος, κρυολιπόλυση, lipolaser), την αποτρίχωση
        (κερί, φωταποτρίχωση, διοδικό laser) και την ευεξία (θεραπείες spa και
        διαιτολογικό τμήμα).</p>
      </div>
      <figure class="claim__fig" style="margin:0">
        {pic("choros-1", [560, 1000], "Η υποδοχή του Pearl Beauty ’n’ Spa",
             "(max-width:900px) 100vw, 40vw")}
      </figure>
    </div>
  </div>
</section>

{cta_block("Ελάτε να γνωριστούμε.",
           "Το πρώτο ραντεβού είναι εκτίμηση και ενημέρωση. Χωρίς δέσμευση.")}
"""
    render("/profil/", f"Προφίλ | {C.BRAND}",
           "Το Pearl Beauty ’n’ Spa στα Γλυκά Νερά: κέντρο αισθητικής προσώπου "
           "και σώματος, αποτρίχωσης και spa, με ομάδα από αισθητικούς, "
           "φυσικοθεραπευτές, γυμναστές και διαιτολόγο.",
           body,
           jsonld=graph(crumbs_ld([("/", "Αρχική"), ("/profil/", "Προφίλ")]),
                        {"@type": "AboutPage", "url": C.SITE_URL + "/profil/",
                         "about": {"@id": C.SITE_URL + "/#business"}}),
           og_img="profil", priority="0.8", css=css, js=js)


CHOROS = [
    ("choros-1", "Η υποδοχή του Pearl Beauty ’n’ Spa"),
    ("choros-2", "Καμπίνα θεραπειών με ιδιωτικό ντους"),
    ("choros-3", "Χώρος θεραπειών σώματος"),
    ("choros-4", "Καμπίνα αισθητικής προσώπου"),
    ("choros-5", "Ο χώρος χαλάρωσης"),
    ("choros-6", "Λεπτομέρεια από τον χώρο των θεραπειών spa"),
]


def build_choros(css, js):
    figs = "".join(
        f'<figure>{pic(n, [560, 1000], a, "(max-width:900px) 100vw, 45vw")}'
        f'</figure>' for n, a in CHOROS)
    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>Ο χώρος</p>
      <h1 class="display d-xl">Ο χώρος</h1>
      <p class="lede">Υποδοχή, καμπίνες θεραπειών με ιδιωτικό ντους και
      αποδυτήριο, και ξεχωριστός, ήσυχος χώρος για τις θεραπείες spa.</p>
  </div>
</section>

<section class="sec" style="padding-top:clamp(1rem,3vw,2rem)">
  <div class="wrap"><div class="gal">{figs}</div></div>
</section>

<section class="sec sec--shell sec--tight">
  <div class="wrap">
    <div class="sec__head">
      <h2 class="display d-m">Πρακτικά</h2>
      <p>Τι καλό είναι να ξέρετε πριν από το πρώτο σας ραντεβού.</p>
    </div>
    <dl class="facts" style="max-width:62ch;margin:0">
      <div><dt>Διεύθυνση</dt><dd>{e(C.STREET)}, {e(C.AREA)} {e(C.POSTAL)}</dd></div>
      <div><dt>Στάθμευση</dt><dd>Ελεύθερη στάθμευση στον δρόμο, μπροστά από τον χώρο</dd></div>
      <div><dt>Πρόσβαση</dt><dd>Από την Αττική Οδό, έξοδος Παιανίας, και από τη Λεωφόρο Λαυρίου</dd></div>
      <div><dt>Ραντεβού</dt><dd><a href="tel:{C.PHONE_TEL}">{e(C.PHONE_TXT)}</a></dd></div>
      <div><dt>Πρώτη επίσκεψη</dt><dd>Υπολογίστε 15 λεπτά επιπλέον για τη γνωριμία και την εκτίμηση</dd></div>
    </dl>
  </div>
</section>

{cta_block("Περάστε να τον δείτε.",
           "Αν θέλετε να γνωρίσετε τον χώρο πριν κλείσετε θεραπεία, πείτε το "
           "στο τηλέφωνο και θα σας ξεναγήσουμε.")}
"""
    render("/o-choros/", f"Ο χώρος | {C.BRAND}",
           "Ο χώρος του Pearl Beauty ’n’ Spa στα Γλυκά Νερά: υποδοχή, καμπίνες "
           "θεραπειών με ιδιωτικό ντους και ξεχωριστό χώρο spa.",
           body,
           jsonld=graph(crumbs_ld([("/", "Αρχική"), ("/o-choros/", "Ο χώρος")])),
           og_img="choros-1", priority="0.7", css=css, js=js)


def build_contact(css, js):
    if C.HOURS:
        hours = ('<dl class="facts" style="margin:0">'
                 + "".join(f"<div><dt>{e(lbl)}</dt><dd>{e(rng)}</dd></div>"
                           for lbl, rng, *_ in C.HOURS)
                 + "</dl>")
    else:
        hours = ('<p class="hours" style="margin:0">Τα ραντεβού κλείνονται '
                 f'τηλεφωνικά στο <a href="tel:{C.PHONE_TEL}">{e(C.PHONE_TXT)}</a>. '
                 'Καλέστε μας και θα βρούμε μια ώρα που σας βολεύει.</p>')

    subject = "Ραντεβού%20-%20Pearl%20Beauty%20n%20Spa"

    body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>Επικοινωνία</p>
      <h1 class="display d-xl">Ραντεβού</h1>
      <p class="lede">Τα ραντεβού κλείνονται τηλεφωνικά. Έτσι μπορούμε να
      ρωτήσουμε τα δύο πράγματα που χρειάζεται να ξέρουμε πριν κλείσουμε ώρα.</p>
  </div>
</section>

<section class="sec" style="padding-top:clamp(1.5rem,3vw,2.5rem)">
  <div class="wrap">
    <div class="contact">
      <div>
        <a class="callnow" href="tel:{C.PHONE_TEL}">
          <span>Καλέστε μας</span>
          <b>{e(C.PHONE_TXT)}</b>
        </a>
        <p class="callnow__alt">Προτιμάτε γραπτά;
          <a href="mailto:{C.EMAIL}?subject={subject}">{C.EMAIL}</a>
        </p>

        <div class="card" style="margin-top:clamp(2rem,3.5vw,2.75rem);
             padding-top:clamp(2rem,3.5vw,2.75rem);border-top:1px solid var(--hair)">
          <h3>Ώρες</h3>
          {hours}
        </div>
        <div class="card">
          <h3>Πού θα έρθετε</h3>
          <p style="margin:0">
            {e(C.STREET)}<br>{e(C.AREA)}, ΤΚ {e(C.POSTAL)}
          </p>
          <p style="margin:.75rem 0 0">Ελεύθερη στάθμευση στον δρόμο. Από την
          Αττική Οδό, έξοδος Παιανίας.</p>
          <p style="margin:.75rem 0 0">
            <a href="https://www.google.com/maps/search/?api=1&amp;query={C.MAPS_Q}"
               target="_blank" rel="noopener">Οδηγίες στον χάρτη</a>
          </p>
        </div>
        <div class="card">
          <h3>Ακολουθήστε μας</h3>
          <p style="margin:0">
            <a href="{C.FACEBOOK}" target="_blank" rel="noopener">Facebook</a> ·
            <a href="{C.INSTAGRAM}" target="_blank" rel="noopener">Instagram</a>
          </p>
        </div>
      </div>

      <div class="prose">
        <h2>Τι θα σας ρωτήσουμε</h2>
        <ul>
          <li><strong>Τι σας απασχολεί.</strong> Όχι ποια θεραπεία θέλετε —
          αυτή την αποφασίζουμε μαζί στο ραντεβού.</li>
          <li><strong>Πότε σας βολεύει.</strong> Ώστε να μη σας δώσουμε ώρα
          που θα χρειαστεί να αλλάξετε.</li>
        </ul>

        <h2>Τι γίνεται στο πρώτο ραντεβού</h2>
        <p>Γίνεται εκτίμηση και μια κουβέντα για το τι σας απασχολεί. Από εκεί προκύπτει τι έχει
        νόημα να γίνει, με ποια σειρά και σε πόσες συνεδρίες. Αν αυτό που
        ζητήσατε δεν είναι το κατάλληλο για την περίπτωσή σας, θα το ακούσετε
        εκεί — πριν πληρώσετε οτιδήποτε.</p>
        <p>Υπολογίστε δεκαπέντε λεπτά παραπάνω από τη διάρκεια της θεραπείας,
        μόνο για αυτό το κομμάτι.</p>

        <h2>Ακύρωση ή αλλαγή</h2>
        <p>Αν κάτι προκύψει, ένα τηλεφώνημα αρκεί. Ενημερώστε μας όσο πιο νωρίς
        μπορείτε, ώστε η ώρα να δοθεί σε κάποιον άλλον.</p>

      </div>
    </div>

    <iframe class="map" title="Χάρτης — {e(C.STREET)}, {e(C.AREA)}"
      src="https://www.google.com/maps?q={C.MAPS_Q}&amp;output=embed"
      loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
  </div>
</section>
"""
    render("/epikoinonia/", f"Ραντεβού & επικοινωνία | {C.BRAND}",
           f"Κλείστε ραντεβού στο {C.PHONE_TXT}. Pearl Beauty ’n’ Spa, "
           f"{C.STREET}, {C.AREA} {C.POSTAL}.",
           body,
           jsonld=graph(
               crumbs_ld([("/", "Αρχική"), ("/epikoinonia/", "Επικοινωνία")]),
               {"@type": "ContactPage", "url": C.SITE_URL + "/epikoinonia/",
                "about": {"@id": C.SITE_URL + "/#business"}}),
           priority="0.9", css=css, js=js)


def build_legal(css, js):
    pages = [
        ("/cookies/", "Χρήση cookies", """
<h2>Τι είναι τα cookies</h2>
<p>Τα cookies είναι μικρά αρχεία κειμένου που αποθηκεύονται στη συσκευή σας όταν
επισκέπτεστε έναν ιστότοπο. Χρησιμοποιούνται για να λειτουργεί σωστά η
πλοήγηση και, σε ορισμένες περιπτώσεις, για τη μέτρηση της επισκεψιμότητας.</p>

<h2>Τι χρησιμοποιεί αυτός ο ιστότοπος</h2>
<p>Ο ιστότοπος pearlspa.gr είναι στατικός και δεν τοποθετεί cookies
παρακολούθησης ή διαφήμισης από μόνος του. Δεν χρησιμοποιούμε cookies
προφίλ, δεν διαμοιραζόμαστε δεδομένα πλοήγησης με τρίτους για διαφημιστικούς
σκοπούς και δεν απαιτείται συγκατάθεση για τη χρήση του.</p>

<h2>Υπηρεσίες τρίτων</h2>
<ul>
<li><strong>Google Fonts.</strong> Οι γραμματοσειρές φορτώνονται από τους
διακομιστές της Google, η οποία λαμβάνει τη διεύθυνση IP σας ως μέρος του
αιτήματος.</li>
<li><strong>Ενσωματωμένος χάρτης Google.</strong> Στη σελίδα επικοινωνίας
υπάρχει χάρτης της Google, ο οποίος ενδέχεται να τοποθετήσει cookies όταν
αλληλεπιδράσετε μαζί του.</li>
</ul>

<h2>Πώς τα ελέγχετε</h2>
<p>Μπορείτε ανά πάσα στιγμή να διαγράψετε ή να αποκλείσετε τα cookies από τις
ρυθμίσεις του προγράμματος περιήγησής σας. Η λειτουργία του ιστότοπου δεν
επηρεάζεται.</p>
"""),
        ("/prosopika-dedomena/", "Προσωπικά δεδομένα", """
<h2>Υπεύθυνος επεξεργασίας</h2>
<p>Υπεύθυνος επεξεργασίας των δεδομένων που συλλέγονται μέσω αυτού του ιστότοπου
είναι η {legal}, με έδρα {street}, {area} {postal}. Για κάθε θέμα σχετικό με τα
δεδομένα σας μπορείτε να επικοινωνείτε στο <a href="mailto:{email}">{email}</a>
ή στο <a href="tel:{tel}">{phone}</a>.</p>

<h2>Ποια δεδομένα συλλέγουμε</h2>
<p>Ο ιστότοπος <strong>δεν συλλέγει κανένα προσωπικό δεδομένο</strong>. Δεν
υπάρχει φόρμα, εγγραφή ή λογαριασμός χρήστη. Δεδομένα μάς δίνετε μόνο εσείς,
όταν επικοινωνείτε μαζί μας ή όταν έρχεστε στον χώρο:</p>
<ul>
<li><strong>Μέσω τηλεφώνου:</strong> τα στοιχεία που μας δίνετε εσείς για τον
προγραμματισμό του ραντεβού — συνήθως ονοματεπώνυμο και τηλέφωνο.</li>
<li><strong>Μέσω email:</strong> ό,τι περιλαμβάνει το μήνυμα που μας στέλνετε
εσείς, στη διεύθυνση που αναγράφεται στον ιστότοπο.</li>
<li><strong>Στον χώρο:</strong> τα στοιχεία που χρειάζονται για την κάρτα
πελάτη σας (π.χ. ευαισθησίες ή αλλεργίες που μας αναφέρετε), τα οποία δεν
συλλέγονται ποτέ μέσω του ιστότοπου.</li>
</ul>

<h2>Γιατί τα επεξεργαζόμαστε</h2>
<p>Αποκλειστικά για να απαντήσουμε στο αίτημά σας και να προγραμματίσουμε το
ραντεβού σας. Νομική βάση είναι η συγκατάθεσή σας, όπως τη δίνετε όταν
επικοινωνείτε μαζί μας με δική σας πρωτοβουλία, καθώς και η εκτέλεση της
μεταξύ μας σύμβασης παροχής υπηρεσιών. Δεν χρησιμοποιούμε τα στοιχεία σας για εμπορική προώθηση χωρίς
ξεχωριστή, ρητή συγκατάθεση.</p>

<h2>Πόσο τα κρατάμε</h2>
<p>Τα μηνύματα ηλεκτρονικού ταχυδρομείου και τα στοιχεία επικοινωνίας
διατηρούνται για όσο διάστημα απαιτείται για την εξυπηρέτηση του αιτήματος
και, σε κάθε περίπτωση, όχι περισσότερο από δώδεκα μήνες. Τα στοιχεία της κάρτας πελάτη τηρούνται για όσο διάστημα είστε πελάτης
του χώρου και διαγράφονται με αίτημά σας.</p>

<h2>Σε ποιους τα διαβιβάζουμε</h2>
<p>Δεν πωλούμε και δεν διαθέτουμε τα δεδομένα σας σε τρίτους. Πρόσβαση έχουν
μόνο τα μέλη της ομάδας που εμπλέκονται στην εξυπηρέτησή σας.</p>

<h2>Τα δικαιώματά σας</h2>
<p>Σύμφωνα με τον Γενικό Κανονισμό Προστασίας Δεδομένων (ΕΕ) 2016/679, έχετε
δικαίωμα πρόσβασης, διόρθωσης, διαγραφής, περιορισμού της επεξεργασίας,
φορητότητας και εναντίωσης, καθώς και δικαίωμα ανάκλησης της συγκατάθεσής σας
ανά πάσα στιγμή. Για την άσκησή τους επικοινωνήστε μαζί μας στο
<a href="mailto:{email}">{email}</a>.</p>

<p>Εφόσον θεωρείτε ότι η επεξεργασία των δεδομένων σας παραβιάζει τη νομοθεσία,
έχετε δικαίωμα καταγγελίας στην Αρχή Προστασίας Δεδομένων Προσωπικού Χαρακτήρα
(<a href="https://www.dpa.gr" target="_blank" rel="noopener">www.dpa.gr</a>).</p>

<h2>Ασφάλεια</h2>
<p>Ο ιστότοπος λειτουργεί αποκλειστικά μέσω κρυπτογραφημένης σύνδεσης (HTTPS).
Λαμβάνουμε εύλογα τεχνικά και οργανωτικά μέτρα για την προστασία των δεδομένων
σας από μη εξουσιοδοτημένη πρόσβαση, απώλεια ή αλλοίωση.</p>
""".format(legal=e(C.LEGAL), street=e(C.STREET), area=e(C.AREA),
           postal=e(C.POSTAL), email=C.EMAIL, tel=C.PHONE_TEL,
           phone=e(C.PHONE_TXT))),
    ]
    for path, title, prose in pages:
        body = f"""
<section class="phead">
  <div class="wrap">
    <p class="crumb"><a href="/">Αρχική</a><span>/</span>{e(title)}</p>
      <h1 class="display d-l">{e(title)}</h1>
      <p class="lede">Τελευταία ενημέρωση: {TODAY}</p>
  </div>
</section>
<section class="sec" style="padding-top:clamp(1.5rem,3vw,2.5rem)">
  <div class="wrap"><div class="prose">{prose}</div></div>
</section>"""
        render(path, f"{title} | {C.BRAND}",
               f"{title} — {C.BRAND}, {C.AREA}.", body,
               priority="0.3", css=css, js=js)


def build_404(css, js):
    body = f"""
<section class="phead notfound">
  <div class="wrap">
    <h1 class="display d-xl">Η σελίδα<br>δεν βρέθηκε.</h1>
    <p class="lede" style="margin-top:2rem">Ο σύνδεσμος μπορεί να άλλαξε ή να
    πληκτρολογήθηκε λάθος. Ξεκινήστε από τις θεραπείες ή καλέστε μας.</p>
    <div class="btns" style="margin-top:2rem">
      <a class="btn" href="/therapeies/"><span>Οι θεραπείες</span></a>
      <a class="btn btn--ghost" href="/epikoinonia/"><span>Ραντεβού</span></a>
      <a class="btn btn--ghost" href="tel:{C.PHONE_TEL}"><span>{e(C.PHONE_TXT)}</span></a>
  </div>
  </div>
</section>"""
    doc_path = "404.html"
    # ίδιο κέλυφος, αλλά χωρίς καταχώρηση στο sitemap
    before = len(PAGES)
    render("/__404__/", f"Η σελίδα δεν βρέθηκε | {C.BRAND}",
           "Η σελίδα που ζητήσατε δεν υπάρχει.", body, css=css, js=js)
    del PAGES[before:]
    src = os.path.join(ROOT, "__404__", "index.html")
    with open(src, encoding="utf-8") as f:
        doc = f.read()
    doc = doc.replace('<meta name="robots" content="index,follow,max-image-preview:large">',
                      '<meta name="robots" content="noindex,follow">')
    write(doc_path, doc)
    shutil.rmtree(os.path.join(ROOT, "__404__"))


# ---------------------------------------------------------- βοηθητικά αρχ. --
def build_sitemap():
    urls = ""
    for path, prio in PAGES:
        urls += (f"<url><loc>{C.SITE_URL}{path}</loc>"
                 f"<lastmod>{TODAY}</lastmod>"
                 f"<changefreq>monthly</changefreq>"
                 f"<priority>{prio}</priority></url>\n")
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          f"{urls}</urlset>\n")

    write("robots.txt",
          "User-agent: *\nAllow: /\n\n"
          f"Sitemap: {C.SITE_URL}/sitemap.xml\n")


def build_vercel():
    seen = set()
    redirects = []
    for src, dst in C.REDIRECTS:
        if src.rstrip("/") == dst.rstrip("/") or src in seen:
            continue
        seen.add(src)
        # Με trailingSlash: true το Vercel κάνει πρώτα 308 στη μορφή με «/»
        # και μετά ελέγχει τα redirects, οπότε η πηγή πρέπει να τελειώνει σε «/».
        redirects.append({"source": src.rstrip("/") + "/", "destination": dst,
                          "permanent": True})
    redirects.insert(0, {
        "source": "/(.*)",
        "has": [{"type": "host", "value": C.SITE_URL.replace("https://www.", "")}],
        "destination": f"{C.SITE_URL}/$1",
        "permanent": True,
    })
    cfg = {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "cleanUrls": True,
        "trailingSlash": True,
        "redirects": redirects,
        "headers": [
            {"source": "/assets/(.*)",
             "headers": [{"key": "Cache-Control",
                          "value": "public, max-age=31536000, immutable"}]},
            {"source": "/(.*)",
             "headers": [
                 {"key": "X-Content-Type-Options", "value": "nosniff"},
                 {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                 {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
                 {"key": "Permissions-Policy",
                  "value": "camera=(), microphone=(), geolocation=()"},
                 {"key": "Strict-Transport-Security",
                  "value": "max-age=31536000; includeSubDomains"},
             ]},
        ],
    }
    write("vercel.json", json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


def build_favicon():
    """Ένα μαργαριτάρι: κύκλος με φίλντισι κλίση, σε μαύρο πεδίο."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs>
<radialGradient id="p" cx="38%" cy="32%" r="72%">
<stop offset="0" stop-color="#FBF7F6"/>
<stop offset=".42" stop-color="#E6DDE0"/>
<stop offset=".72" stop-color="#C9D2CE"/>
<stop offset="1" stop-color="#BDB6C9"/>
</radialGradient>
</defs>
<rect width="64" height="64" fill="#000"/>
<circle cx="32" cy="32" r="19" fill="url(#p)"/>
<ellipse cx="25" cy="24" rx="6" ry="4" fill="#fff" opacity=".55"
 transform="rotate(-28 25 24)"/>
</svg>
"""
    write("favicon.svg", svg)


def build_apple_icon():
    """PNG 180×180 από το ίδιο μοτίβο με το favicon."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return
    n = 720
    im = Image.new("RGB", (n, n), (0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = n / 2
    r = n * 0.297
    # φίλντισι κλίση με ομόκεντρους κύκλους
    stops = [(0.00, (251, 247, 246)), (0.42, (230, 221, 224)),
             (0.72, (201, 210, 206)), (1.00, (189, 182, 201))]
    for i in range(int(r), 0, -1):
        t = 1 - i / r
        for k in range(len(stops) - 1):
            a, ca = stops[k]
            b, cb = stops[k + 1]
            if a <= t <= b:
                f = (t - a) / (b - a) if b > a else 0
                col = tuple(round(ca[j] + (cb[j] - ca[j]) * f) for j in range(3))
                break
        else:
            col = stops[-1][1]
        ox, oy = cx - r * 0.24 * (i / r), cy - r * 0.36 * (i / r)
        d.ellipse([ox - i, oy - i, ox + i, oy + i], fill=col)
    im.resize((180, 180), Image.LANCZOS).save(
        os.path.join(ROOT, "apple-touch-icon.png"), "PNG", optimize=True)


def build_readme(css, js):
    n_pages = len(PAGES)
    write("README.md", f"""# pearlspa.gr

Στατικό site για το **{C.BRAND}** ({C.LEGAL}), {C.STREET}, {C.AREA}.

## Πώς χτίζεται

```bash
python3 _build/images.py   # μόνο όταν αλλάζουν φωτογραφίες
python3 _build/build.py    # κάθε φορά
```

Το `build.py` γράφει HTML στη ρίζα του repo. **Μην επεξεργάζεσαι τα παραγόμενα
`index.html`** — χάνονται στο επόμενο build.

| Αρχείο | Τι κρατά |
| --- | --- |
| `_build/content.py` | ταυτότητα, στοιχεία επικοινωνίας, όλα τα κείμενα των θεραπειών, ανακατευθύνσεις |
| `_build/build.py` | δομή σελίδων, κεφαλίδα/υποσέλιδο, JSON-LD, sitemap, vercel.json |
| `_build/pearl.css` | όλη η μορφοποίηση |
| `_build/pearl.js` | μενού, sticky header, προεπισκόπηση ευρετηρίου |
| `_build/images.py` | duotone, κόψιμο και webp/jpg από το `_build/src-img/` |

Τα CSS/JS αντιγράφονται στο `assets/` με hash στο όνομα, οπότε το cache
καθαρίζει μόνο του σε κάθε αλλαγή.

## Σελίδες

{n_pages} σελίδες: αρχική, ευρετήριο θεραπειών,
{len(C.SERVICES)} σελίδες θεραπειών, προφίλ, ο χώρος, επικοινωνία και δύο
νομικές σελίδες, συν `404.html`. Δεν υπάρχει φόρμα πουθενά: τα ραντεβού
κλείνονται τηλεφωνικά, οπότε ο ιστότοπος δεν συλλέγει κανένα προσωπικό δεδομένο
και δεν εξαρτάται από υπηρεσία τρίτου.

## Εκκρεμότητες πριν το live

1. **Ώρες λειτουργίας.** Στο `content.py` η `HOURS` είναι `None`, οπότε το site
   λέει παντού «τηλεφωνικά ραντεβού» και δεν δηλώνει `openingHours` στο
   structured data. Μόλις τις επιβεβαιώσει ο πελάτης, συμπλήρωσέ τη με τη μορφή
   που περιγράφεται στο σχόλιο και ξανατρέξε το build.
2. **Επωνυμία εταιρείας.** Η `LEGAL` στο `content.py` είναι ακόμη η παλιά
   («ΙΔΙΩΤΙΚΟ ΙΑΤΡΕΙΟ ΙΑΤΡΙΚΗ Ι.Κ.Ε.») και εμφανίζεται στο © του υποσέλιδου και
   στη σελίδα προσωπικών δεδομένων. Αν άλλαξε με τη νέα λειτουργία, διόρθωσέ
   την.
3. **Συντεταγμένες.** Το `GEO` στο `content.py` είναι κατά προσέγγιση για τα
   Γλυκά Νερά. Πάρε τις ακριβείς από το Google Business Profile.
4. **Φωτογραφίες.** Το πιο αδύναμο σημείο. Οι τωρινές είναι παλιό stock και
   φωτογραφίες κινητού, 600–1000 px — στέκονται μόνο επειδή περνούν από duotone
   και βρίσκονται κάτω από σκούρο πέπλο. Οι ζώνες πλήρους πλάτους (`hero-wide`,
   `band-*`) θέλουν πηγές τουλάχιστον 2000 px. Μια φωτογράφιση του χώρου και της
   ομάδας ανεβάζει το αποτέλεσμα πιο πολύ από οποιαδήποτε αλλαγή κώδικα —
   ρίξ’ τες στο `_build/src-img/`, ενημέρωσε το `ASSETS` στο `images.py` και
   ξανατρέξε.
5. **Google Search Console.** Υπόβαλε το `sitemap.xml` και παρακολούθησε τις
   ανακατευθύνσεις από τα παλιά URL του WordPress (ορίζονται στο `REDIRECTS`).

## Η σχεδίαση

Πρότυπο, κατ’ απαίτηση του πελάτη, το `skinneymedspa.com`: λευκό χαρτί, αληθινό
μαύρο, χρυσή πινελιά (`#D3AF37`), φωτογραφίες πλήρους πλάτους με σκούρο πέπλο
και χάπια αντί για ορθογώνια κουμπιά.

Τρεις τυπογραφικές φωνές, όλες με ελληνικά από το Google Fonts:

| Φωνή | Πού | Γιατί |
| --- | --- | --- |
| `Noto Serif Display` | οι μεγάλες φράσεις (hero, κλείσιμο) | η σερίφ φωνή του προτύπου |
| `Noto Sans Display` @ `wdth 66` | τίτλοι ενοτήτων, κουμπιά, μικρά κεφαλαία | ο μόνος τρόπος να πιάσεις το «Helvetica Neue Ultra Light Condensed» στα ελληνικά |
| `Noto Sans Display` @ `wdth 100` | τρεχούμενο κείμενο | ίδια οικογένεια, άρα δένει |

Οι τίτλοι ενοτήτων είναι πάντα **κεντραρισμένοι, πεζοί και δίχρωμοι** — μαύρη η
πρώτη λέξη, γκρι η δεύτερη (`<h2 class="display">αισθητική <i>προσώπου</i></h2>`).
Αυτό είναι το πιο αναγνωρίσιμο στοιχείο του προτύπου· κράτα το σε κάθε νέα
ενότητα.

Η κεφαλίδα στέκεται διάφανη πάνω από το σκούρο πρώτο πλαίσιο κάθε σελίδας
(`head--over`) και γίνεται λευκή μόλις κυλήσεις (`head--stuck`, από το
`pearl.js`). Γι’ αυτό **κάθε σελίδα ξεκινά με σκούρο μπλοκ** — `.hero` στην
αρχική, `.phead` παντού αλλού. Αν βάλεις ανοιχτόχρωμο πρώτο μπλοκ, το λογότυπο
γίνεται αόρατο.

## Λογότυπο

Το λογότυπο είναι το `_build/pearl-logo.svg` (καθαρά vectors, εξαγωγή από το
`_build/src-img/pearl-logo-original.pdf`) και μπαίνει inline σε κεφαλίδα και
υποσέλιδο. Το «Pearl» είναι πάντα πράσινο (`#85CD26`), τα μαργαριτάρια έχουν
δική τους κλίση και το «Beauty 'n' Spa» παίρνει `currentColor`, ώστε να
γίνεται λευκό όταν η κεφαλίδα στέκεται πάνω σε φωτογραφία.

## Τι δεν υπάρχει πια

Από τον Νοέμβριο του 2026 ο χώρος είναι αποκλειστικά κέντρο αισθητικής και
spa. Αφαιρέθηκαν το τμήμα Medi Pearl και κάθε ιατρική θεραπεία (botox,
fillers, PRP, νήματα, τριχόπτωση, δερματολογία, ιατρικές θεραπείες προσώπου).
Τα παλιά URL τους κάνουν 301 στο `/therapeies/` (βλ. `REDIRECTS`).

## Deploy

Vercel, με ρίζα του repo ως output directory. Το `vercel.json` κάνει 301 από το
`pearlspa.gr` στο `www.pearlspa.gr` και από όλα τα παλιά URL του WordPress στα
νέα.
""")


# ------------------------------------------------------------------- main --
def main():
    css = fingerprint("pearl.css", "css")
    js = fingerprint("pearl.js", "js")

    build_home(css, js)
    for key in C.SECTIONS:
        build_section(key, css, js)
    for s in C.SERVICES:
        build_service(s, css, js)
    build_offers(css, js)
    build_profil(css, js)
    build_choros(css, js)
    build_contact(css, js)
    build_legal(css, js)
    build_404(css, js)

    build_sitemap()
    build_vercel()
    build_favicon()
    build_apple_icon()
    build_readme(css, js)

    write(".gitignore", ".DS_Store\n__pycache__/\n.vercel\n")

    print(f"  {len(PAGES)} σελίδες")
    print(f"  css {css}")
    print(f"  js  {js}")


if __name__ == "__main__":
    main()
