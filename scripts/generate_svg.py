#!/usr/bin/env python3
"""
Reads all JSON files in registry/ and generates SVGs into svg-out/
Each SVG uses CSS prefers-color-scheme for automatic dark/light switching.
"""
import json, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).parent.parent
REGISTRY = ROOT / "registry"
OUT = ROOT / "svg-out"
OUT.mkdir(exist_ok=True)

W = 420
PAD = 16
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

TIER_COLORS = {
    "full":        {"bg": "rgba(74,222,128,0.25)",  "text": "#a7f3d0", "label": "FULL"},
    "conditional": {"bg": "rgba(251,191,36,0.25)",  "text": "#fde68a", "label": "CONDITIONAL"},
    "fail":        {"bg": "rgba(248,113,113,0.25)", "text": "#fca5a5", "label": "FAIL"},
    "pending":     {"bg": "rgba(148,163,184,0.25)", "text": "#cbd5e1", "label": "PENDING"},
}

COLOR_DARK = {
    "green": {"bg": "rgba(74,222,128,0.12)",  "text": "#4ade80", "border": "rgba(74,222,128,0.25)"},
    "amber": {"bg": "rgba(251,191,36,0.12)",  "text": "#fbbf24", "border": "rgba(251,191,36,0.25)"},
    "red":   {"bg": "rgba(248,113,113,0.12)", "text": "#f87171", "border": "rgba(248,113,113,0.25)"},
}
COLOR_LIGHT = {
    "green": {"bg": "rgba(22,163,74,0.1)",    "text": "#15803d", "border": "rgba(22,163,74,0.25)"},
    "amber": {"bg": "rgba(180,83,9,0.08)",    "text": "#b45309", "border": "rgba(180,83,9,0.2)"},
    "red":   {"bg": "rgba(185,28,28,0.08)",   "text": "#b91c1c", "border": "rgba(185,28,28,0.2)"},
}

SECTIONS = [
    ("Licensing & Ownership", [
        ("License",          "licensing", "license"),
        ("Source available", "licensing", "source"),
        ("User owns data",   "licensing", "user_owns_data"),
        ("Right to modify",  "licensing", "right_to_modify"),
    ]),
    ("Monetization", [
        ("Base cost",      "monetization", "base_cost"),
        ("Revenue model",  "monetization", "model"),
        ("Ads",            "monetization", "ads"),
        ("In-app purchases","monetization","iap"),
    ]),
    ("Privacy & Transparency", [
        ("Telemetry",                     "privacy", "telemetry"),
        ("Network activity disclosure",   "privacy", "network_disclosure"),
        ("Abstraction layers inspectable","privacy", "layers_inspectable"),
    ]),
    ("Reproducibility", [
        ("Configuration portable",   "reproducibility", "config_portable"),
        ("Silent behavior changes",  "reproducibility", "silent_updates"),
        ("Rebuild from description", "reproducibility", "rebuild_from_desc"),
    ]),
    ("Ability & Modularity", [
        ("Configurability floor",  "ability", "configurability"),
        ("Modularity",             "ability", "component_replace"),
        ("Power user ceiling",     "ability", "power_user_ceiling"),
    ]),
]


def xml_escape(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")


def wrap_text(text, max_chars=52):
    return textwrap.wrap(str(text), max_chars) or [""]


def pill_svg(x, y, text, color, cls_prefix, idx):
    dark_c  = COLOR_DARK.get(color,  COLOR_DARK["green"])
    light_c = COLOR_LIGHT.get(color, COLOR_LIGHT["green"])
    w = max(40, len(text) * 7 + 20)
    h = 20
    rx = 5
    cid = f"{cls_prefix}_{idx}"
    return f"""
  <rect id="pill_bg_{cid}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"
    fill="{dark_c['bg']}" stroke="{dark_c['border']}" stroke-width="1"
    class="pill-bg-{cid}"/>
  <text x="{x + w//2}" y="{y + 14}" text-anchor="middle"
    font-family="{FONT}" font-size="11" font-weight="700" letter-spacing="0.5"
    fill="{dark_c['text']}" class="pill-text-{cid}">{xml_escape(text)}</text>
""", w, f"""
  .pill-bg-{cid}   {{ fill: {dark_c['bg']}; stroke: {dark_c['border']}; }}
  .pill-text-{cid} {{ fill: {dark_c['text']}; }}
  @media (prefers-color-scheme: light) {{
    .pill-bg-{cid}   {{ fill: {light_c['bg']}; stroke: {light_c['border']}; }}
    .pill-text-{cid} {{ fill: {light_c['text']}; }}
  }}
"""


def generate_svg(data):
    lines = []   # SVG elements
    styles = []  # CSS rules
    y = 0

    pid = data.get("id", "unknown")
    meta = data.get("meta", {})
    status = data.get("status", {})
    ux = data.get("ux", {})
    table = data.get("table", {})
    tier = status.get("tier", "pending")
    conditions = status.get("conditions", [])

    tier_c = TIER_COLORS.get(tier, TIER_COLORS["pending"])

    # ── HEADER ──────────────────────────────────────────────
    header_h = 64
    lines.append(f'<defs>')
    lines.append(f'  <linearGradient id="hdr_grad" x1="0%" y1="0%" x2="100%" y2="100%">')
    lines.append(f'    <stop offset="0%"   stop-color="#5b21b6"/>')
    lines.append(f'    <stop offset="60%"  stop-color="#7c3aed"/>')
    lines.append(f'    <stop offset="100%" stop-color="#8b5cf6"/>')
    lines.append(f'  </linearGradient>')
    lines.append(f'</defs>')

    lines.append(f'<rect x="0" y="0" width="{W}" height="{header_h}" fill="url(#hdr_grad)"/>')
    lines.append(f'<rect x="0" y="0" width="{W}" height="{header_h}" fill="rgba(30,10,60,0.45)"/>')

    # logo placeholder (simple -0 text)
    lines.append(f'<text x="20" y="38" font-family="{FONT}" font-size="18" font-weight="700" fill="white" opacity="0.9">-0</text>')

    # product name
    name = xml_escape(meta.get("name", ""))
    vendor = xml_escape(meta.get("vendor", ""))
    ptype  = xml_escape(meta.get("type", ""))
    lines.append(f'<text x="58" y="32" font-family="{FONT}" font-size="15" font-weight="700" fill="white">{name}</text>')
    lines.append(f'<text x="58" y="48" font-family="{FONT}" font-size="10" fill="rgba(255,255,255,0.55)">{vendor} · {ptype}</text>')

    # ID
    lines.append(f'<text x="{W-PAD}" y="22" text-anchor="end" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">{xml_escape(pid)}</text>')

    # tier badge
    tier_label = tier_c["label"]
    tw = len(tier_label) * 7 + 20
    lines.append(f'<rect x="{W-PAD-tw}" y="30" width="{tw}" height="20" rx="5" fill="{tier_c["bg"]}"/>')
    lines.append(f'<text x="{W-PAD-tw//2}" y="44" text-anchor="middle" font-family="{FONT}" font-size="9" font-weight="700" letter-spacing="0.8" fill="{tier_c["text"]}">{xml_escape(tier_label)}</text>')

    y = header_h

    # ── SECTION HELPER ──────────────────────────────────────
    def section_header(title):
        nonlocal y
        h = 28
        lines.append(f'<rect x="0" y="{y}" width="{W}" height="{h}" class="sec-bg"/>')
        lines.append(f'<text x="{PAD}" y="{y+19}" font-family="{FONT}" font-size="9" font-weight="700" letter-spacing="0.8" class="sec-label">{xml_escape(title.upper())}</text>')
        y += h

    def section_divider():
        nonlocal y
        lines.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" class="divider"/>')

    # ── BADGE SECTIONS ───────────────────────────────────────
    for sec_title, fields in SECTIONS:
        section_header(sec_title)

        n = len(fields)
        col_w = (W - PAD * 2) // n
        label_y = y + 16
        badge_y = y + 28

        for i, (label, section_key, field_key) in enumerate(fields):
            cx = PAD + i * col_w
            lines.append(f'<text x="{cx}" y="{label_y}" font-family="{FONT}" font-size="9" letter-spacing="0.3" class="field-label">{xml_escape(label)}</text>')

            field = table.get(section_key, {}).get(field_key, {})
            val   = field.get("value", "") if isinstance(field, dict) else str(field)
            color = field.get("color", "green") if isinstance(field, dict) else "green"

            p_svg, p_w, p_css = pill_svg(cx, badge_y, val, color, f"s{sec_title[:3].replace(' ','')}{i}", i)
            lines.append(p_svg)
            styles.append(p_css)

        y += 54

        # service note for monetization
        if sec_title == "Monetization":
            note = table.get("monetization", {}).get("service_note", "")
            if note:
                lines.append(f'<text x="{PAD}" y="{y+14}" font-family="{FONT}" font-size="9" class="field-label">1st party service</text>')
                y += 20
                for line in wrap_text(note, 60):
                    lines.append(f'<text x="{PAD}" y="{y+12}" font-family="{FONT}" font-size="10" class="note-text">{xml_escape(line)}</text>')
                    y += 15
                y += 6

        section_divider()

    # ── UX SECTION ───────────────────────────────────────────
    section_header("User Experience")
    ux_score = float(ux.get("score", 0))
    ux_note  = ux.get("note", "")

    lines.append(f'<text x="{PAD}" y="{y+15}" font-family="{FONT}" font-size="9" class="field-label">Tester score</text>')

    # dots
    dot_x = W - PAD - 5 * 16
    for i in range(1, 6):
        cx2 = dot_x + (i-1) * 16 + 6
        cy2 = y + 10
        full = ux_score >= i
        half = (not full) and ux_score >= i - 0.5
        if half:
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" fill="#3f3f46" class="dot-empty"/>')
            lines.append(f'<clipPath id="hc{i}"><rect x="{cx2-6}" y="{cy2-6}" width="6" height="12"/></clipPath>')
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" fill="#a78bfa" clip-path="url(#hc{i})" class="dot-active"/>')
        else:
            cl = "dot-active" if full else "dot-empty"
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" class="{cl}"/>')

    lines.append(f'<text x="{dot_x + 5*16 + 8}" y="{y+15}" font-family="{FONT}" font-size="10" font-weight="700" fill="#a78bfa" class="ux-score">{ux_score}/5</text>')
    y += 28

    if ux_note:
        for line in wrap_text(f'"{ux_note}"', 58):
            lines.append(f'<text x="{PAD}" y="{y+12}" font-family="{FONT}" font-size="10" font-style="italic" class="note-text">{xml_escape(line)}</text>')
            y += 15
        y += 6
    else:
        y += 8

    section_divider()

    # ── EXCEPTIONS ───────────────────────────────────────────
    if conditions:
        section_header("Conditional Exceptions")
        for cond in conditions:
            comp   = cond.get("component", "")
            reason = cond.get("reason", "")
            # amber left bar
            lines.append(f'<rect x="0" y="{y}" width="{W}" height="4" fill="#1c1109" class="exc-bg"/>')
            lines.append(f'<rect x="0" y="{y}" width="3" height="100" fill="#f59e0b"/>')  # will be clipped by card

            lines.append(f'<rect x="0" y="{y}" width="{W}" height="60" fill="#1c1109" class="exc-bg"/>')
            lines.append(f'<rect x="0" y="{y}" width="3" height="60" fill="#f59e0b"/>')
            lines.append(f'<text x="{PAD+4}" y="{y+16}" font-family="{FONT}" font-size="10" font-weight="700" fill="#fbbf24" class="exc-title">{xml_escape(comp)}</text>')
            reason_y = y + 28
            for line in wrap_text(reason, 55):
                lines.append(f'<text x="{PAD+4}" y="{reason_y}" font-family="{FONT}" font-size="9" fill="#78716c" class="exc-reason">{xml_escape(line)}</text>')
                reason_y += 13
            y += max(60, reason_y - y + 8)

    total_h = y

    # ── ASSEMBLE ─────────────────────────────────────────────
    base_styles = f"""
    :root {{ color-scheme: light dark; }}
    .sec-bg     {{ fill: #1e1e21; }}
    .sec-label  {{ fill: #52525b; }}
    .divider    {{ stroke: #27272a; stroke-width: 1; }}
    .field-label{{ fill: #52525b; }}
    .note-text  {{ fill: #71717a; }}
    .dot-active {{ fill: #a78bfa; }}
    .dot-empty  {{ fill: #3f3f46; }}
    .ux-score   {{ fill: #a78bfa; }}
    .exc-bg     {{ fill: #1c1109; }}
    .exc-title  {{ fill: #fbbf24; }}
    .exc-reason {{ fill: #78716c; }}
    @media (prefers-color-scheme: light) {{
      .sec-bg     {{ fill: #f4f4f6; }}
      .sec-label  {{ fill: #a1a1aa; }}
      .divider    {{ stroke: #e4e4e7; }}
      .field-label{{ fill: #a1a1aa; }}
      .note-text  {{ fill: #71717a; }}
      .dot-active {{ fill: #7c3aed; }}
      .dot-empty  {{ fill: #e4e4e7; }}
      .ux-score   {{ fill: #7c3aed; }}
      .exc-bg     {{ fill: #fffbeb; }}
      .exc-title  {{ fill: #b45309; }}
      .exc-reason {{ fill: #92400e; }}
    }}
    """
    all_css = base_styles + "\n".join(styles)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}" viewBox="0 0 {W} {total_h}">
<defs>
  <style>{all_css}</style>
  <linearGradient id="hdr_grad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#5b21b6"/>
    <stop offset="60%"  stop-color="#7c3aed"/>
    <stop offset="100%" stop-color="#8b5cf6"/>
  </linearGradient>
  {''.join(f'<clipPath id="hc{i}"><rect x="0" y="0" width="6" height="12"/></clipPath>' for i in range(1,6))}
</defs>
<rect x="0" y="0" width="{W}" height="{total_h}" fill="#18181b" class="card-bg"/>
{"".join(lines)}
</svg>"""

    # fix duplicate defs
    svg = svg.replace('<defs>\n</defs>', '')
    return svg


for json_file in sorted(REGISTRY.glob("*.json")):
    try:
        data = json.loads(json_file.read_text())
        svg  = generate_svg(data)
        out_path = OUT / (json_file.stem + ".svg")
        out_path.write_text(svg)
        print(f"  generated: {out_path.name}")
    except Exception as e:
        print(f"  ERROR {json_file.name}: {e}", file=sys.stderr)
