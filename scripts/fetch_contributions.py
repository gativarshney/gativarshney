"""Fetch the public contribution calendar. No token, no GraphQL.

GitHub serves the contribution calendar as public HTML at
https://github.com/users/<username>/contributions - the same fragment the
profile page itself renders. This script parses the day cells and writes
data/contributions.json with raw days plus derived stats.

Run locally or from the daily GitHub Actions workflow:

    python scripts/fetch_contributions.py
"""

import json
import re
import sys
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

USERNAME = "gativarshney"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = "data/contributions.json"


def parse_count(text: str) -> int:
    m = re.match(r"(\d+|No)\s+contribution", text.strip())
    if not m:
        return 0
    return 0 if m.group(1) == "No" else int(m.group(1))


def main() -> None:
    resp = requests.get(URL, headers={"User-Agent": "profile-art-refresh"},
                        timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        sys.exit("no day cells found; GitHub may have changed the markup")

    # Counts live in <tool-tip for="<td id>"> elements next to the table.
    tips = {t.get("for"): parse_count(t.get_text())
            for t in soup.select("tool-tip")}

    days = sorted(
        [
            {
                "date": td["data-date"],
                "level": int(td.get("data-level", 0)),
                "count": tips.get(td.get("id"), 0),
            }
            for td in cells
        ],
        key=lambda d: d["date"],
    )

    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # Streaks (a streak = consecutive days with >= 1 contribution).
    longest = run = 0
    prev = None
    for d in days:
        day = date.fromisoformat(d["date"])
        if d["count"] > 0:
            run = run + 1 if prev and day - prev == timedelta(days=1) else 1
            longest = max(longest, run)
            prev = day
        else:
            run = 0

    # Current streak: walk backwards; today with 0 doesn't break it.
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break

    out = {
        "username": USERNAME,
        "fetched": days[-1]["date"],
        "total": total,
        "best_day": best,
        "longest_streak": longest,
        "current_streak": current,
        "days": days,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {OUT}: {len(days)} days, {total} contributions, "
          f"best {best['count']} on {best['date']}, "
          f"streak {current} (longest {longest})")


if __name__ == "__main__":
    main()
