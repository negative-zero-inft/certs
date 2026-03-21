#!/usr/bin/env python3
"""
Reads all JSON files in registry/ and generates SVGs into svg-out/.
SVGs use CSS prefers-color-scheme for automatic dark/light switching.
"""
import json, sys, textwrap, secrets, string
from pathlib import Path

ROOT     = Path(__file__).parent.parent
REGISTRY = ROOT / "registry"
OUT      = ROOT / "svg-out"
OUT.mkdir(exist_ok=True)

W    = 420
PAD  = 16
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

ID_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

def generate_id():
    return "".join(secrets.choice(ID_CHARS) for _ in range(7))

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
        ("Base cost",       "monetization", "base_cost"),
        ("Revenue model",   "monetization", "model"),
        ("Ads",             "monetization", "ads"),
        ("In-app purchases","monetization", "iap"),
    ]),
    ("Privacy & Transparency", [
        ("Telemetry",                      "privacy", "telemetry"),
        ("Network activity disclosure",    "privacy", "network_disclosure"),
        ("Abstraction layers inspectable", "privacy", "layers_inspectable"),
    ]),
    ("Reproducibility", [
        ("Configuration portable",    "reproducibility", "config_portable"),
        ("Silent behavior changes",   "reproducibility", "silent_updates"),
        ("Rebuild from description",  "reproducibility", "rebuild_from_desc"),
    ]),
    ("Ability & Modularity", [
        ("Configurability floor",  "ability", "configurability"),
        ("Modularity",             "ability", "component_replace"),
        ("Power user ceiling",     "ability", "power_user_ceiling"),
    ]),
]


def xe(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def wrap_text(text, max_chars=52):
    return textwrap.wrap(str(text), max_chars) or [""]

def pill_svg(x, y, text, color, uid):
    dk = COLOR_DARK.get(color, COLOR_DARK["green"])
    lk = COLOR_LIGHT.get(color, COLOR_LIGHT["green"])
    w  = max(40, len(text) * 7 + 20)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="20" rx="5" class="pb{uid}"/>'
        f'<text x="{x+w//2}" y="{y+14}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="11" font-weight="700" letter-spacing="0.5" class="pt{uid}">{xe(text)}</text>',
        w,
        f'.pb{uid}{{fill:{dk["bg"]};stroke:{dk["border"]};stroke-width:1}}'
        f'.pt{uid}{{fill:{dk["text"]}}}'
        f'@media(prefers-color-scheme:light){{'
        f'.pb{uid}{{fill:{lk["bg"]};stroke:{lk["border"]}}}'
        f'.pt{uid}{{fill:{lk["text"]}}}}}'
    )


def generate_svg(data):
    lines  = []
    styles = []
    y      = 0

    pid    = data.get("id", "unknown")
    meta   = data.get("meta", {})
    status = data.get("status", {})
    ux     = data.get("ux", {})
    table  = data.get("table", {})
    tier   = status.get("tier", "pending")
    conds  = status.get("conditions", [])
    tier_c = TIER_COLORS.get(tier, TIER_COLORS["pending"])

    # header
    header_h = 64
    lines.append(
        f'<rect x="0" y="0" width="{W}" height="{header_h}" fill="url(#hg)"/>'
        f'<rect x="0" y="0" width="{W}" height="{header_h}" fill="rgba(30,10,60,0.45)"/>'
        f'<text x="20" y="38" font-family="{FONT}" font-size="18" font-weight="700" fill="white" opacity="0.9">-0</text>'
        f'<text x="58" y="32" font-family="{FONT}" font-size="15" font-weight="700" fill="white">{xe(meta.get("name",""))}</text>'
        f'<text x="58" y="48" font-family="{FONT}" font-size="10" fill="rgba(255,255,255,0.55)">{xe(meta.get("vendor",""))} · {xe(meta.get("type",""))}</text>'
        f'<text x="{W-PAD}" y="22" text-anchor="end" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">{xe(pid)}</text>'
    )
    tw = len(tier_c["label"]) * 7 + 20
    lines.append(
        f'<rect x="{W-PAD-tw}" y="30" width="{tw}" height="20" rx="5" fill="{tier_c["bg"]}"/>'
        f'<text x="{W-PAD-tw//2}" y="44" text-anchor="middle" font-family="{FONT}" '
        f'font-size="9" font-weight="700" letter-spacing="0.8" fill="{tier_c["text"]}">{xe(tier_c["label"])}</text>'
    )
    y = header_h

    def sec_header(title):
        nonlocal y
        lines.append(
            f'<rect x="0" y="{y}" width="{W}" height="28" class="sec-bg"/>'
            f'<text x="{PAD}" y="{y+19}" font-family="{FONT}" font-size="9" font-weight="700" '
            f'letter-spacing="0.8" class="sec-label">{xe(title.upper())}</text>'
        )
        y += 28

    def divider():
        lines.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" class="div"/>')

    for sec_title, fields in SECTIONS:
        sec_header(sec_title)
        n      = len(fields)
        col_w  = (W - PAD * 2) // n
        lbl_y  = y + 16
        bdg_y  = y + 28

        for i, (label, sk, fk) in enumerate(fields):
            cx    = PAD + i * col_w
            field = table.get(sk, {}).get(fk, {})
            val   = field.get("value", "") if isinstance(field, dict) else str(field)
            color = field.get("color", "green") if isinstance(field, dict) else "green"
            uid   = f"{sec_title[:2].replace(' ','')}{i}"

            lines.append(f'<text x="{cx}" y="{lbl_y}" font-family="{FONT}" font-size="9" letter-spacing="0.3" class="flbl">{xe(label)}</text>')
            ps, pw, pc = pill_svg(cx, bdg_y, val, color, uid)
            lines.append(ps)
            styles.append(pc)

        y += 54

        if sec_title == "Monetization":
            note = table.get("monetization", {}).get("service_note", "")
            if note:
                lines.append(f'<text x="{PAD}" y="{y+14}" font-family="{FONT}" font-size="9" class="flbl">1st party service</text>')
                y += 20
                for line in wrap_text(note, 60):
                    lines.append(f'<text x="{PAD}" y="{y+12}" font-family="{FONT}" font-size="10" class="ntxt">{xe(line)}</text>')
                    y += 15
                y += 6

        divider()

    # UX
    sec_header("User Experience")
    ux_score = float(ux.get("score", 0))
    ux_note  = ux.get("note", "")
    lines.append(f'<text x="{PAD}" y="{y+15}" font-family="{FONT}" font-size="9" class="flbl">Tester score</text>')
    dot_x = W - PAD - 5 * 16
    for i in range(1, 6):
        cx2 = dot_x + (i-1)*16 + 6
        cy2 = y + 10
        full = ux_score >= i
        half = (not full) and ux_score >= i - 0.5
        if half:
            lines.append(f'<defs><clipPath id="hc{i}"><rect x="{cx2-6}" y="{cy2-6}" width="6" height="12"/></clipPath></defs>')
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" class="de"/>')
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" class="da" clip-path="url(#hc{i})"/>')
        else:
            lines.append(f'<circle cx="{cx2}" cy="{cy2}" r="5" class="{"da" if full else "de"}"/>')
    lines.append(f'<text x="{dot_x+5*16+8}" y="{y+15}" font-family="{FONT}" font-size="10" font-weight="700" class="uxs">{ux_score}/5</text>')
    y += 28
    if ux_note:
        for line in wrap_text(f'"{ux_note}"', 58):
            lines.append(f'<text x="{PAD}" y="{y+12}" font-family="{FONT}" font-size="10" font-style="italic" class="ntxt">{xe(line)}</text>')
            y += 15
        y += 6
    else:
        y += 8
    divider()

    # exceptions
    if conds:
        sec_header("Conditional Exceptions")
        for cond in conds:
            comp   = cond.get("component", "")
            reason = cond.get("reason", "")
            lines.append(f'<rect x="0" y="{y}" width="{W}" height="60" class="exc-bg"/>')
            lines.append(f'<rect x="0" y="{y}" width="3" height="60" fill="#f59e0b"/>')
            lines.append(f'<text x="{PAD+4}" y="{y+16}" font-family="{FONT}" font-size="10" font-weight="700" class="etit">{xe(comp)}</text>')
            ry = y + 28
            for line in wrap_text(reason, 55):
                lines.append(f'<text x="{PAD+4}" y="{ry}" font-family="{FONT}" font-size="9" class="eras">{xe(line)}</text>')
                ry += 13
            y += max(60, ry - y + 8)

    total_h = y
    base_css = (
        ".card-bg{fill:#18181b}.sec-bg{fill:#1e1e21}.sec-label{fill:#52525b}"
        ".div{stroke:#27272a;stroke-width:1}.flbl{fill:#52525b}.ntxt{fill:#71717a}"
        ".da{fill:#a78bfa}.de{fill:#3f3f46}.uxs{fill:#a78bfa}"
        ".exc-bg{fill:#1c1109}.etit{fill:#fbbf24}.eras{fill:#78716c}"
        "@media(prefers-color-scheme:light){"
        ".card-bg{fill:#fff}.sec-bg{fill:#f4f4f6}.sec-label{fill:#a1a1aa}"
        ".div{stroke:#e4e4e7}.flbl{fill:#a1a1aa}"
        ".da{fill:#7c3aed}.de{fill:#e4e4e7}.uxs{fill:#7c3aed}"
        ".exc-bg{fill:#fffbeb}.etit{fill:#b45309}.eras{fill:#92400e}}"
    )
    all_css = base_css + "".join(styles)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}" viewBox="0 0 {W} {total_h}">'
        f'<defs><style>{all_css}</style>'
        f'<linearGradient id="hg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#5b21b6"/>'
        f'<stop offset="60%" stop-color="#7c3aed"/>'
        f'<stop offset="100%" stop-color="#8b5cf6"/>'
        f'</linearGradient></defs>'
        f'<rect x="0" y="0" width="{W}" height="{total_h}" rx="12" class="card-bg"/>'
        + "".join(lines) +
        f'</svg>'
    )


for json_file in sorted(REGISTRY.glob("*.json")):
    try:
        data = json.loads(json_file.read_text())
        svg  = generate_svg(data)
        out  = OUT / (json_file.stem + ".svg")
        out.write_text(svg)
        print(f"  ✓ {out.name}")
    except Exception as e:
        print(f"  ✗ {json_file.name}: {e}", file=sys.stderr)
