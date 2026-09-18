#!/usr/bin/env python3
"""
sync-tokens.py — pushes token values from a ht-article-tokens-<slug>.md
file into its matching HTML previews (ht-article-mobile-<slug>.html and
the -preview.html variant).

Usage:
    python3 sync-tokens.py archivo
    python3 sync-tokens.py jakarta
    python3 sync-tokens.py switzer
    python3 sync-tokens.py all          # does all three

How it works
-------------
The .md file is treated as the source of truth. This script:
  1. Parses the "All text tokens" fenced table in the .md file.
  2. For each token, updates the matching CSS rule in the HTML file(s)
     (font-family, font-size, line-height, font-weight, font-style,
     letter-spacing). Font-family is only touched for tokens whose
     selector doesn't already use var(--font-head) (i.e. label, byline,
     caption, b1, b2) — h1/h2/pull-quote keep using the --font-head
     variable set at the top of the file.
  3. Adds the token's font to the page's Google Fonts <link> if it
     isn't already linked, so a changed font actually renders instead
     of silently falling back to a system font.
  4. In the annotated HTML (non -preview file), also rewrites the
     matching <div class="spec">...</div> badge text to match.

Limitations
-----------
This is a one-way, run-it-yourself sync (.md -> .html). It does NOT run
automatically when you save the .md file — there's no live process
watching these files. Run this script after you edit a token table and
the HTML will catch up to match it.

It only understands the 8 known tokens below. If you rename a token or
add a new one, update TOKEN_MAP accordingly.
"""

import re
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent

# token -> (css selector regex, badge label used in the annotated HTML)
# 'kind' controls which properties this selector supports.
TOKEN_MAP = {
    "label":      {"selector": r"(\.kicker\s*\{)(.*?)(\})", "badge": "label",      "has_family": False},
    "byline":     {"selector": r"(\.byline\s*\{)(.*?)(\})", "badge": "byline",     "has_family": False},
    "caption":    {"selector": r"(figcaption\s*\{)(.*?)(\})", "badge": "caption",  "has_family": False},
    "b2":         {"selector": r"(\.b2\s*\{)(.*?)(\})", "badge": "b2",            "has_family": False},
    "b1":         {"selector": r"(p\.b1\s*\{)(.*?)(\})", "badge": "b1",           "has_family": False},
    "h1":         {"selector": r"(\bh1\s*\{)(.*?)(\})", "badge": "h1",            "has_family": True},
    "h2":         {"selector": r"(h2\.h2\s*\{)(.*?)(\})", "badge": "h2",          "has_family": True},
    "pull-quote": {"selector": r"(blockquote p\s*\{)(.*?)(\})", "badge": "pull-quote", "has_family": False},
}

# Fonts that don't come from Google Fonts need their own <link> tag instead of
# an addition to the css2?family=... URL. Add an entry here if a token's Name
# column ever names one of these.
NON_GOOGLE_FONTS = {
    "Switzer": '<link href="https://api.fontshare.com/v2/css?f[]=switzer@400,500,600,700&display=swap" rel="stylesheet">',
}


def parse_md_table(md_path: Path):
    """Extract {token: {size, lh_px, lh_ratio, spacing, name, weight, style}} from the fenced table."""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## All text tokens\s*```(.*?)```", text, re.DOTALL)
    if not m:
        raise ValueError(f"Couldn't find 'All text tokens' table in {md_path}")
    block = m.group(1).strip("\n")
    lines = block.split("\n")
    data_lines = lines[2:]  # skip header + dashed separator

    tokens = {}
    for line in data_lines:
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) < 3:
            continue
        token, size_lh, spacing, name_weight_style = parts[0], parts[1], parts[2], parts[3]

        size_str, lh_str = [p.strip() for p in size_lh.split(" / ", 1)]
        size_px = size_str.replace("px", "")

        lh_ratio = None
        if lh_str == "normal":
            lh_px = None
        else:
            rm = re.match(r"([\d.]+)px(?:\s*\(([\d.]+)\))?", lh_str)
            if rm:
                lh_px = rm.group(1)
                lh_ratio = rm.group(2)
            else:
                lh_px = lh_str

        nws = [p.strip() for p in name_weight_style.split(" / ")]
        name, weight, style = nws[0], nws[1], nws[2]

        tokens[token] = {
            "size": size_px,
            "lh_px": lh_px,
            "lh_ratio": lh_ratio,
            "spacing": spacing,
            "name": name,
            "weight": weight,
            "style": style,
        }
    return tokens


def set_prop(body, prop, value, unit=""):
    pattern = rf"{prop}\s*:\s*[^;]+;"
    replacement = f"{prop}: {value}{unit};"
    if re.search(pattern, body):
        return re.sub(pattern, replacement, body, count=1)
    return body  # don't add properties that weren't already declared


def set_or_add_prop(body, prop, value):
    """Like set_prop, but inserts the declaration (right after the opening brace)
    if it isn't already present, instead of leaving the rule untouched."""
    pattern = rf"{prop}\s*:\s*[^;]+;"
    replacement = f"{prop}: {value};"
    if re.search(pattern, body):
        return re.sub(pattern, replacement, body, count=1)
    # No existing declaration: insert one at the very start of the rule body.
    return f" {replacement}" + body


def rebuild_rule_body(old_body: str, vals: dict, has_family: bool) -> str:
    """Rewrite font-family / font-size / line-height / font-weight / font-style /
    letter-spacing inside a CSS rule."""
    body = old_body

    if not has_family:
        # These selectors don't use var(--font-head); the token's Name column
        # is the actual font to render in, so make sure the rule says so.
        body = set_or_add_prop(body, "font-family", f"'{vals['name']}', sans-serif")

    body = set_prop(body, "font-size", vals["size"], "px")

    if vals["lh_ratio"]:
        body = set_prop(body, "line-height", vals["lh_ratio"])
    elif vals["lh_px"]:
        body = set_prop(body, "line-height", vals["lh_px"], "px")
    # if lh_px is None ("normal"), leave line-height untouched

    body = set_prop(body, "font-weight", vals["weight"])

    if vals["style"] == "italic":
        body = set_prop(body, "font-style", "italic")
    elif "font-style" in body:
        body = set_prop(body, "font-style", "normal")

    if vals["spacing"] not in ("normal", "\u2014", "-"):
        body = set_prop(body, "letter-spacing", vals["spacing"])

    return body


def ensure_google_font_linked(html: str, font_name: str) -> str:
    """Make sure `font_name` is present in the page's <head> font links so it
    actually renders instead of silently falling back to a system font."""
    if font_name in NON_GOOGLE_FONTS:
        link_tag = NON_GOOGLE_FONTS[font_name]
        if link_tag in html:
            return html  # already linked
        # Insert right after the last <link rel="preconnect" ...> tag, or
        # failing that, right before </head>.
        preconnects = list(re.finditer(r'<link rel="preconnect"[^>]*>\n?', html))
        if preconnects:
            insert_at = preconnects[-1].end()
            return html[:insert_at] + link_tag + "\n" + html[insert_at:]
        return html.replace("</head>", link_tag + "\n</head>", 1)

    if font_name == "Noto Sans" and "family=Noto+Sans" in html:
        return html  # already linked by default in every file
    family_param = font_name.replace(" ", "+")
    if f"family={family_param}" in html:
        return html  # already linked

    link_pattern = re.compile(
        r'(<link href="https://fonts\.googleapis\.com/css2\?)([^"]*)("[^>]*>)'
    )
    m = link_pattern.search(html)
    if not m:
        return html  # no Google Fonts link found to extend; leave as-is

    addition = f"&family={family_param}:wght@400;500;600;700"
    new_href = m.group(2) + addition
    return html[: m.start()] + m.group(1) + new_href + m.group(3) + html[m.end():]


def sync_html(html_path: Path, tokens: dict, has_badges: bool):
    if not html_path.exists():
        print(f"  (skip, not found: {html_path.name})")
        return
    html = html_path.read_text(encoding="utf-8")

    for token, info in TOKEN_MAP.items():
        if token not in tokens:
            continue
        vals = tokens[token]

        if not info["has_family"]:
            html = ensure_google_font_linked(html, vals["name"])

        pattern = re.compile(info["selector"], re.DOTALL)
        match = pattern.search(html)
        if not match:
            continue
        new_body = rebuild_rule_body(match.group(2), vals, info["has_family"])
        html = html[:match.start()] + match.group(1) + new_body + match.group(3) + html[match.end():]

        if has_badges:
            lh_display = vals["lh_px"] and f"{vals['lh_px']}px" or "normal"
            if vals["lh_ratio"]:
                lh_display += f" ({vals['lh_ratio']})"
            weight_display = vals["weight"] + (" italic" if vals["style"] == "italic" else "")
            new_badge = (
                f'{info["badge"]} &middot; size {vals["size"]}px &middot; '
                f'l-height {lh_display} &middot; weight {weight_display} &middot; '
                f'l-spacing {vals["spacing"]} &middot; {vals["name"]}'
            )
            badge_pattern = re.compile(
                rf'(<div class="spec">){re.escape(info["badge"])}\s*[\u00b7&middot;]+.*?(</div>)'
            )
            html = badge_pattern.sub(lambda m: m.group(1) + new_badge + m.group(2), html)

    html_path.write_text(html, encoding="utf-8")
    print(f"  synced: {html_path.name}")


def sync_font(slug: str):
    md_path = OUT_DIR / f"ht-article-tokens-{slug}.md"
    if not md_path.exists():
        print(f"No such file: {md_path.name}")
        return
    print(f"Reading {md_path.name} ...")
    tokens = parse_md_table(md_path)

    with_badges = OUT_DIR / f"ht-article-mobile-{slug}.html"
    preview_only = OUT_DIR / f"ht-article-mobile-{slug}-preview.html"

    sync_html(with_badges, tokens, has_badges=True)
    sync_html(preview_only, tokens, has_badges=False)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]
    slugs = ["archivo", "jakarta", "switzer"] if arg == "all" else [arg]
    for slug in slugs:
        sync_font(slug)
