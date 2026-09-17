# Text Tokens — Switzer Preview

Preview file: `ht-article-mobile-switzer.html`

---

## All text tokens

```
Token         Size / Line-Height       Spacing    Name / Weight / Style
-----------   ----------------------   --------   -------------------------
h1            30px / 42px (1.4)        normal     Switzer / 700 / normal
h2            22px / 30.8px (1.4)      normal     Switzer / 700 / normal
b1            17px / 28.05px (1.65)    normal     Noto Sans / 400 / normal
b2            15px / 23.25px (1.55)    normal     Noto Sans / 400 / normal
pull-quote    18px / 27.9px (1.55)     normal     Switzer / 700 / italic
caption       13px / 18.2px (1.4)      normal     Inter / 400 / normal
byline        13px / normal            normal     Inter / 400 / normal
label         13px / 20px              0.02em     Inter / 700 / normal
```

---

## Token usage

- **h1** — Article headline
- **h2** — In-article section break
- **b1** — Standard body paragraph
- **b2** — Lede / opening paragraph
- **pull-quote** — Blockquote
- **caption** — Image caption
- **byline** — Author name + location / date / read time
- **label** — Section kicker (e.g. "India News")

---

## Quick copy-paste CSS

```css
:root {
  --font-head: 'Switzer';
  --font-body: 'Inter';
}

/* Common (Inter) */
.label      { font-size: 13px; line-height: 20px;   font-weight: 700; letter-spacing: 0.02em; }
.byline     { font-size: 13px; font-weight: 400; }
.caption    { font-size: 13px; line-height: 1.4;  font-weight: 400; }
.b2         { font-size: 15px; line-height: 1.55; font-weight: 400; }
.b1         { font-size: 17px; line-height: 1.65; font-weight: 400; }

/* Headline-role (Switzer) */
.h1         { font-size: 30px; line-height: 1.4;  font-weight: 700; }
.h2         { font-size: 22px; line-height: 1.4;  font-weight: 700; }
.pull-quote { font-size: 18px; line-height: 1.55; font-weight: 700; font-style: italic; }
```
