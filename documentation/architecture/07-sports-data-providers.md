# Prediqo — Sports Data Provider Evaluation (Phase 0)

**Critical finding:** real fixtures/results/statistics cannot be delivered without a
licensed data source. This is the **hardest blocker** for Phase 3 and requires a budget
decision before implementation. All pricing below is indicative — verify current
terms directly with each provider before committing.

---

## 1. Evaluation criteria

- Competition coverage for target markets (Kenya, UK, SA, Nigeria, Ghana).
- Historical fixtures and results (needed for model training and backtests).
- Team/player statistics: goals, xG, corners, first-half, H2H, form.
- Lineups and injuries (optional advanced intelligence).
- Update frequency, rate limits, latency, reliability.
- **Commercial licence and redistribution rights** (using data inside a commercial app).
- Right to use data for ML model training and to publish derived probabilities.
- Cost and free-tier suitability.

---

## 2. Candidate providers

| Provider | Coverage | Stats depth | Indicative cost | Licensing notes | Verdict |
|---|---|---|---|---|---|
| **API-Football (API-Sports)** | Very broad, strong Africa/Europe | Fixtures, results, standings, events, stats, lineups, injuries, some xG | Free tier very limited; paid plans roughly tens of USD/month; verify | Commercial licence needed for app redistribution; check ToS on derived predictions | **Recommended starting point** — best coverage/cost balance, pending licence confirmation |
| **football-data.org** | Good European focus; limited Africa | Fixtures, results, standings, basic stats | Free tier limited; paid plans low tens USD/month | Clearer free/paid split; check commercial terms | Good fallback / secondary source |
| **TheSportsDB** | Broad, community-driven | Fixtures, results, some stats | Free / low cost | Community data quality varies; verify licence | Supplementary only |
| **StatsBomb (open data)** | Select competitions only | Very rich, includes xG and events | Free open datasets | Open licence for specific datasets | Excellent for **model R&D/backtesting** on covered leagues, not live |
| **FBref / Understat** | Broad xG data | xG-heavy | Free (scraping) | **ToS/risk**: scraping may violate terms; no reliable commercial licence | Do not rely on for production |
| **Sportradar / Opta** | Elite, official | Deep, official xG | Enterprise, expensive | Full commercial licence | Future upgrade path only |

---

## 3. Recommendation

1. **Phase 3 primary:** API-Football paid tier (or football-data.org if licence/terms are
   clearer). Confirm in writing that the licence permits:
   - storing normalized data in our database,
   - displaying derived statistics in a commercial app,
   - using historical data to train and evaluate models,
   - publishing probability estimates derived from that data.
2. **AI/ML R&D:** StatsBomb open datasets for xG-rich backtesting where competition
   coverage overlaps; clearly labelled as research data.
3. **No scraping** of sites whose terms forbid it.
4. Build the **provider abstraction now** so a switch is a config change, not a rewrite:

```
ProviderAdapter (interface)
  ├── fetch_competitions()
  ├── fetch_teams(competition)
  ├── fetch_fixtures(date_range)
  ├── fetch_results(fixture_ids)
  ├── fetch_statistics(fixture_id)
  ├── fetch_head_to_head(team_a, team_b)
  └── fetch_lineups_injuries(fixture_id)  # optional
          ↓
Normaliser → Validator → Provenance metadata → Repository → DB
```

---

## 4. Data quality rules

- Every ingested record carries `provider_id`, `provider_record_id`, `captured_at`,
  and a completeness score.
- Missing data stays `null` — no interpolation or fabricated placeholders.
- De-duplicate by provider ID with UNIQUE constraints.
- Retry with exponential backoff; timeouts; rate limiting; failed jobs recorded in
  `sync_jobs`.
- Scheduled sync: fixtures (every few hours), results (after full time), standings/stats
  (daily). Use Celery Beat.
- Cache provider responses in Redis to reduce calls.

---

## 5. Cost / approval note

No provider API key will be embedded in the mobile app. The key is stored as a backend
secret (`.env` locally, GitHub Actions secret / host env in deployment). **Approval and
a monthly budget are required before Phase 3 provider integration.**
