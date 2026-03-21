import requests
import sqlite3
import os
import html
from datetime import datetime, timedelta
from groq import Groq

# ── Locations ──────────────────────────────────────────────────────────────────
LOCATIONS = [
    {"name": "Kathmandu",  "lat": 27.7172, "lon": 85.3240},
    {"name": "Biratnagar", "lat": 26.4525, "lon": 87.2718},
    {"name": "Aalborg",    "lat": 57.0488, "lon": 9.9217},
]

# ── Open-Meteo variables ───────────────────────────────────────────────────────
VARIABLES = "temperature_2m_max,temperature_2m_min,wind_speed_10m_max,cloud_cover_mean,precipitation_sum"

# ── Database ───────────────────────────────────────────────────────────────────
DB_PATH = "weather.db"


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            location             TEXT    NOT NULL,
            forecast_date        TEXT    NOT NULL,
            temperature_max      REAL,
            temperature_min      REAL,
            wind_speed_max       REAL,
            cloud_cover_mean     REAL,
            precipitation_sum    REAL,
            fetched_at           TEXT    NOT NULL
        )
    """)
    conn.commit()


def fetch_weather(location: dict) -> dict:
    """Fetch tomorrow's forecast for a single location."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['lat']}&longitude={location['lon']}"
        f"&daily={VARIABLES}"
        f"&start_date={tomorrow}&end_date={tomorrow}"
        f"&timezone=auto"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()["daily"]

    return {
        "location":          location["name"],
        "forecast_date":     data["time"][0],
        "temperature_max":   data["temperature_2m_max"][0],
        "temperature_min":   data["temperature_2m_min"][0],
        "wind_speed_max":    data["wind_speed_10m_max"][0],
        "cloud_cover_mean":  data["cloud_cover_mean"][0],
        "precipitation_sum": data["precipitation_sum"][0],
        "fetched_at":        datetime.utcnow().isoformat(),
    }


def save_forecast(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute("""
        INSERT INTO forecasts
            (location, forecast_date, temperature_max, temperature_min,
             wind_speed_max, cloud_cover_mean, precipitation_sum, fetched_at)
        VALUES
            (:location, :forecast_date, :temperature_max, :temperature_min,
             :wind_speed_max, :cloud_cover_mean, :precipitation_sum, :fetched_at)
    """, row)
    conn.commit()


def generate_poem(forecasts: list[dict]) -> str:
    """Ask Groq to write a bilingual weather poem."""
    summary = "\n".join(
        f"- {f['location']}: max {f['temperature_max']}°C, min {f['temperature_min']}°C, "
        f"wind {f['wind_speed_max']} km/h, cloud cover {f['cloud_cover_mean']}%, "
        f"precipitation {f['precipitation_sum']} mm"
        for f in forecasts
    )

    prompt = f"""
You are a creative poet. Here is tomorrow's weather forecast for three cities:

{summary}

Write a short poem (8–12 lines) that:
1. Compares the weather in the three cities
2. Describes the differences vividly
3. Suggests which city would be nicest to be in tomorrow
4. Is written FIRST in English, then translated naturally into Nepali

Requirements:
- Mention all three cities
- Avoid clichés such as "bright and bold", "young and old", or "the choice is clear"
- Use sensory imagery such as breeze, light, chill, warmth, sky, air, or scent
- Make the English version poetic but clear
- Make the Nepali version natural and fluent
- Do not mix Hindi words into Nepali
- Avoid awkward contradictions like "cloudless grey"
- Keep the recommendation clear but elegant

Separate the two versions with a blank line and the label "— नेपाली अनुवाद —".
"""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return response.choices[0].message.content.strip()


def save_html(forecasts: list[dict], poem: str) -> None:
    """Write docs/index.html for GitHub Pages."""
    os.makedirs("docs", exist_ok=True)
    date_str = forecasts[0]["forecast_date"]
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    rows = ""
    for f in forecasts:
        rows += f"""
        <tr>
            <td>{html.escape(str(f['location']))}</td>
            <td>{f['temperature_max']} / {f['temperature_min']}</td>
            <td>{f['wind_speed_max']}</td>
            <td>{f['cloud_cover_mean']}</td>
            <td>{f['precipitation_sum']}</td>
        </tr>"""

    poem_html = "".join(
        f'<p class="poem-line">{html.escape(line) if line.strip() else "&nbsp;"}</p>'
        for line in poem.splitlines()
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Weather Poem – {date_str}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Georgia', serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      min-height: 100vh;
      color: #e8f4f8;
      padding: 2rem 1rem;
    }}

    header {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}

    header h1 {{
      font-size: 2.2rem;
      letter-spacing: 0.05em;
      color: #a8d8ea;
    }}

    header p {{
      margin-top: 0.4rem;
      font-size: 0.9rem;
      color: #7fb3c8;
    }}

    .card {{
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 1rem;
      padding: 1.8rem 2rem;
      max-width: 860px;
      margin: 0 auto 2rem;
      backdrop-filter: blur(6px);
    }}

    .card h2 {{
      font-size: 1.2rem;
      color: #a8d8ea;
      margin-bottom: 1.2rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}

    th, td {{
      padding: 0.6rem 0.8rem;
      text-align: center;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}

    th {{
      color: #7fb3c8;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}

    tr:last-child td {{ border-bottom: none; }}

    .poem-line {{
      line-height: 1.85;
      font-size: 1.05rem;
    }}

    footer {{
      text-align: center;
      font-size: 0.8rem;
      color: #4a8fa8;
      margin-top: 1rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>🌤 Weather Poem</h1>
    <p>Forecast for <strong>{date_str}</strong> · Generated at {generated_at}</p>
  </header>

  <div class="card">
    <h2>📊 Tomorrow's Forecast</h2>
    <table>
      <thead>
        <tr>
          <th>Location</th>
          <th>Temp Max / Min (°C)</th>
          <th>Wind Speed (km/h)</th>
          <th>Cloud Cover (%)</th>
          <th>Precipitation (mm)</th>
        </tr>
      </thead>
      <tbody>{rows}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>✍️ Poem — English &amp; Nepali</h2>
    {poem_html}
  </div>

  <footer>
    Auto-generated by GitHub Actions · Data from Open-Meteo · Poem by Groq LLaMA 3
  </footer>
</body>
</html>
"""
    with open("docs/index.html", "w", encoding="utf-8") as fh:
        fh.write(html_content)
    print("✅ docs/index.html written.")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    forecasts = []
    for loc in LOCATIONS:
        print(f"Fetching weather for {loc['name']}…")
        row = fetch_weather(loc)
        save_forecast(conn, row)
        forecasts.append(row)
        print(f"  ✅ Saved: {row}")

    conn.close()

    print("\nGenerating poem with Groq…")
    poem = generate_poem(forecasts)
    print("\n── POEM ──────────────────────────────────────────────")
    print(poem)
    print("──────────────────────────────────────────────────────\n")

    save_html(forecasts, poem)


if __name__ == "__main__":
    main()
