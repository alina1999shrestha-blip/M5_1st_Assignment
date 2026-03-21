# 🌤 Automated Weather Pipeline
> **Course:** M6-Data Engineering and Machine Learning Operations in Business  
> **Semester:** 2nd Semester — 2nd Course  
> **Assignment:** 1st Assignment

Collects daily weather forecasts for **Kathmandu**, **Biratnagar**, and **Aalborg**, generates a bilingual (English + Nepali) poem using the Groq LLM, and publishes the result on GitHub Pages.

## How it works

1. **`fetch.py`** — fetches tomorrow's weather from [Open-Meteo](https://open-meteo.com/), stores it in `weather.db` (SQLite), calls the Groq API to generate a poem, and writes `docs/index.html`.
2. **GitHub Actions** (`.github/workflows/weather.yml`) — runs the pipeline every day at 20:00 Danish time and commits the updated files back to the repo.
3. **GitHub Pages** — serves `docs/index.html` as a public website.

## Weather variables

| Variable | Source field |
|---|---|
| Max / Min temperature (°C) | `temperature_2m_max`, `temperature_2m_min` |
| Max wind speed (km/h) | `wind_speed_10m_max` |
| Mean cloud cover (%) | `cloud_cover_mean` |
| Precipitation sum (mm) | `precipitation_sum` |

## Setup

### 1. Fork / clone this repository

### 2. Add your Groq API key as a GitHub Secret

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|---|---|
| `GROQ_API_KEY` | your key from [console.groq.com](https://console.groq.com) |

### 3. Enable GitHub Pages

Go to **Settings → Pages** and set:
- **Source**: Deploy from a branch
- **Branch**: `main` / `docs` folder

### 4. Trigger a first run

Go to **Actions → Weather Pipeline → Run workflow** to test it immediately.

## Local development

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python fetch.py
```
