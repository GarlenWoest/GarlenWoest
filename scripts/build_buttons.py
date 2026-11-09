"""Builds the link buttons under the card (assets/btn-*-{dark,light}.svg)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUTTONS = {"linkedin": "LINKEDIN", "projects": "PROJECTS"}
THEMES = {
    "dark": dict(bg="#161b22", border="#30363d", text="#c9d1d9", accent="#ffa657"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", text="#24292f", accent="#953800"),
}
W, H = 300, 44

for theme, t in THEMES.items():
    for slug, label in BUTTONS.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" xml:space="preserve">
<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="8" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1.5"/>
<rect x="10" y="{H-3}" width="{W-20}" height="2" rx="1" fill="{t['accent']}"/>
<text x="{W/2}" y="{H/2+5}" text-anchor="middle" font-size="15px" font-family="ConsolasFallback,Consolas,'SF Mono',Menlo,'DejaVu Sans Mono',monospace"><tspan fill="{t['accent']}">&gt; </tspan><tspan fill="{t['text']}">{label}</tspan></text>
</svg>'''
        (ROOT / "assets" / f"btn-{slug}-{theme}.svg").write_text(svg)
