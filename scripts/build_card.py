"""Builds the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Run locally with no token to rebuild layout only, or in GitHub Actions with
GITHUB_TOKEN (or ACCESS_TOKEN for private repo stats) to refresh live stats.
Edit PROFILE below to change what the card says.
"""
import json
import os
import time
import urllib.request
from html import escape
from pathlib import Path

USER = "GarlenWoest"
ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")

# ---- content ---------------------------------------------------------------
# (key, value) rows; None = blank spacer; ("#", title) = section rule
PROFILE = [
    ("#", "garlen@woest"),
    ("Host", "Case Western Reserve University"),
    ("Kernel", "Finance & Business Analytics"),
    ("Program", "MS Business Analytics & Intelligence"),
    ("Background", "BSBA Finance, John Carroll University"),
    ("Experience", "Private Equity Intern, MCM Capital"),
    ("Founder", "Talent Harbor"),
    ("Location", "Cleveland, OH | Hamburg, DE"),
    None,
    ("Languages.Programming", "Python, SQL"),
    ("Languages.Tools", "pandas, scikit-learn, DuckDB, Power BI"),
    ("Languages.Real", "German, English, Spanish"),
    None,
    ("Focus.Finance", "Valuation, Credit Risk, Private Equity"),
    ("Focus.Data", "ML, Forecasting, LLM Agents"),
    ("Hobbies", "Soccer, Markets"),
    None,
    ("#", "Contact"),
    ("LinkedIn", "in/garlenwoest"),
    ("GitHub", "GarlenWoest"),
    None,
    ("#", "GitHub Stats"),
    "STATS",
]

WIDTH_CH = 62          # characters per info line
FONT = 15              # px
LINE = 19              # px line height
CH = FONT * 0.602      # monospace advance (DejaVu/Menlo); Consolas is narrower
PAD = 22

THEMES = {
    "dark": dict(bg="#161b22", border="#30363d", text="#c9d1d9", art="#adbac7",
                 key="#ffa657", val="#a5d6ff", rule="#6e7681", add="#3fb950", dele="#f85149"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", text="#24292f", art="#57606a",
                  key="#953800", val="#0a3069", rule="#8c959f", add="#1a7f37", dele="#cf222e"),
}


# ---- stats -----------------------------------------------------------------
def api(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-card",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, (json.loads(r.read() or b"null"))


def fetch_stats():
    if not TOKEN:
        return None
    q = """query($login:String!){ user(login:$login){
      followers{totalCount}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}
      repositories(ownerAffiliations:OWNER, first:100){ totalCount
        nodes{ nameWithOwner stargazerCount isFork } } } }"""
    _, d = api("https://api.github.com/graphql",
               json.dumps({"query": q, "variables": {"login": USER}}).encode())
    u = d["data"]["user"]
    repos = u["repositories"]["nodes"]
    s = dict(repos=u["repositories"]["totalCount"],
             contrib=u["repositoriesContributedTo"]["totalCount"],
             stars=sum(r["stargazerCount"] for r in repos),
             followers=u["followers"]["totalCount"], commits=0, add=0, dele=0)
    for r in repos:
        if r["isFork"]:
            continue
        url = f"https://api.github.com/repos/{r['nameWithOwner']}/stats/contributors"
        for _ in range(8):  # GitHub returns 202 while it computes stats
            try:
                code, body = api(url)
            except Exception:
                code, body = 0, None
            if code == 200 and isinstance(body, list):
                for c in body:
                    if c.get("author") and c["author"]["login"].lower() == USER.lower():
                        s["commits"] += c["total"]
                        s["add"] += sum(w["a"] for w in c["weeks"])
                        s["dele"] += sum(w["d"] for w in c["weeks"])
                break
            time.sleep(4)
    return s


def load_cached():
    p = ROOT / "assets" / "stats.json"
    return json.loads(p.read_text()) if p.exists() else None


# ---- svg -------------------------------------------------------------------
def dots(n):
    return " " + "." * max(n, 1) + " "


def kv_line(key, val):
    n = WIDTH_CH - 2 - len(key) - 1 - len(val) - 2
    return [(". ", "rule"), (key, "key"), (":", "text"), (dots(n), "rule"), (val, "val")]


def rule_line(title):
    if title == "garlen@woest":
        return [(title, "key"), (" " + "-" * (WIDTH_CH - len(title) - 1), "rule")]
    return [("- ", "rule"), (title, "text"), (" " + "-" * (WIDTH_CH - len(title) - 3), "rule")]


def filled(prefix, value, width):
    """prefix/value are segment lists; dots fill the gap to exactly `width` chars."""
    used = sum(len(t) for t, _ in prefix) + sum(len(t) for t, _ in value)
    return prefix + [(dots(width - used - 2), "rule")] + value


def stat_lines(s):
    f = lambda v: "--" if v is None else f"{v:,}"
    k = s or {}
    repos, contrib, stars = f(k.get("repos")), f(k.get("contrib")), f(k.get("stars"))
    commits, foll = f(k.get("commits")), f(k.get("followers"))
    loc = f(None if s is None else s["add"] - s["dele"])
    add, dele = f(k.get("add")), f(k.get("dele"))

    left = 36                  # width of left half incl. ". "
    right = WIDTH_CH - left - 3  # after " | "
    sep = [(" | ", "rule")]
    key = lambda name: [(name, "key"), (":", "text")]

    line1 = (filled([(". ", "rule")] + key("Repos"),
                    [(repos, "val"), (" {", "text"), ("Contributed", "key"), (": ", "text"),
                     (contrib, "val"), ("}", "text")], left)
             + sep + filled(key("Stars"), [(stars, "val")], right))
    line2 = (filled([(". ", "rule")] + key("Commits"), [(commits, "val")], left)
             + sep + filled(key("Followers"), [(foll, "val")], right))
    line3 = filled([(". ", "rule")] + key("Lines of Code"),
                   [(loc, "val"), (" ( ", "text"), (f"{add}++", "add"), (", ", "text"),
                    (f"{dele}--", "dele"), (" )", "text")], WIDTH_CH)
    return [line1, line2, line3]


def build(theme, stats):
    t = THEMES[theme]
    art = (ROOT / "assets" / "ascii.txt").read_text().rstrip("\n").split("\n")
    if theme == "light":  # art encodes brightness for a dark background; invert for light
        ramp = ".:-=+*#%@"
        flip = {c: ramp[len(ramp) - 1 - i] for i, c in enumerate(ramp)}
        art = ["".join(flip.get(c, c) for c in l) for l in art]
    art_w = max(len(l) for l in art)

    info = []
    for row in PROFILE:
        if row is None:
            info.append([])
        elif row == "STATS":
            info += stat_lines(stats)
        elif row[0] == "#":
            info.append(rule_line(row[1]))
        else:
            info.append(kv_line(*row))
    info.append([])
    info.append([(">", "key")])

    rows = max(len(art), len(info))
    art_x = PAD
    info_x = PAD + art_w * CH + 28
    width = round(info_x + WIDTH_CH * CH + PAD)
    height = PAD * 2 + rows * LINE
    art_top = PAD + LINE + (rows - len(art)) * LINE / 2
    info_top = PAD + LINE + (rows - len(info)) * LINE / 2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-size="{FONT}px" xml:space="preserve">',
         "<style>text,tspan{white-space:pre;font-family:ConsolasFallback,Consolas,'SF Mono',Menlo,"
         "'DejaVu Sans Mono','Liberation Mono',monospace}"
         f".text{{fill:{t['text']}}}.key{{fill:{t['key']}}}.val{{fill:{t['val']}}}"
         f".rule{{fill:{t['rule']}}}.add{{fill:{t['add']}}}.dele{{fill:{t['dele']}}}"
         f".art{{fill:{t['art']}}}</style>",
         f'<rect width="{width}" height="{height}" rx="14" fill="{t["bg"]}" '
         f'stroke="{t["border"]}" stroke-width="1.5"/>']

    o.append(f'<text x="{art_x:.1f}" y="{art_top:.1f}" class="art">')
    for i, l in enumerate(art):
        o.append(f'<tspan x="{art_x:.1f}" dy="{0 if i == 0 else LINE}">{escape(l) or " "}</tspan>')
    o.append("</text>")

    o.append(f'<text x="{info_x:.1f}" y="{info_top:.1f}" class="text">')
    for i, segs in enumerate(info):
        dy = 0 if i == 0 else LINE
        if not segs:
            o.append(f'<tspan x="{info_x:.1f}" dy="{dy}"> </tspan>')
            continue
        o.append(f'<tspan x="{info_x:.1f}" dy="{dy}">' +
                 "".join(f'<tspan class="{c}">{escape(s)}</tspan>' for s, c in segs) + "</tspan>")
    o.append("</text></svg>")
    return "\n".join(o)


def main():
    stats = None
    try:
        stats = fetch_stats()
    except Exception as e:
        print("stats fetch failed:", e)
    if stats:
        (ROOT / "assets" / "stats.json").write_text(json.dumps(stats, indent=2))
    else:
        stats = load_cached()
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(build(theme, stats))
    print("stats:", stats)


if __name__ == "__main__":
    main()
