# LLM Tracker

Living inventory and comparison dashboard for large language models from the major frontier and open-weights vendors. Every non-trivial field links back to the vendor's own source page.

**Live site:** [llmtracker.pplx.app](https://llmtracker.pplx.app)

![Screenshot placeholder — Lineage view](./screenshot.png)

## What it does

Three views on the same underlying dataset:

- **Lineage** — one column per vendor, oldest → newest. See how each vendor's family tree evolved (Anthropic: Claude 2 → 3 → 3.5 → 4 → 4.5 → 5, etc.). Filter by status (current / superseded / deprecated / legacy) and openness (closed / open weights).
- **Compare** — sortable, filterable table across all models. Filter by vendor, tier, openness, status, modality, minimum context window, or maximum input price. Answer questions like *"cheapest open-weights vision model with 200K+ context."*
- **Detail** — click any model for a card with pricing, license, positioning, and inline source links to the vendor's own page.

Current coverage: **165 models across 10 vendors** (OpenAI, Anthropic, Google, xAI, Meta, DeepSeek, Alibaba/Qwen, Mistral, Moonshot AI, Cohere), 2023 through the latest refresh.

## Repository layout

```
.
├── index.html                     # The dashboard (single-file SPA, no build step)
├── data/
│   ├── models.json                # Structured data the dashboard reads
│   └── inventory_YYYY-MM-DD.md    # Source-cited research markdown (audit trail)
├── scripts/
│   └── parse_to_json.py           # Converts the inventory markdown into models.json
├── LICENSE                        # MIT
└── README.md
```

## Running it locally

No build step, no dependencies. Any static file server works:

```bash
# Python 3
python3 -m http.server 8000

# or Node
npx serve .
```

Then open `http://localhost:8000`.

## Refreshing the data

Two ways:

1. **Via Perplexity Computer** — in the AI Learning Facilitator project on Perplexity, say *"refresh the LLM tracker."* The `dk-llm-tracker-refresh` skill runs a live research pass, shows a diff, and updates the JSON after approval.
2. **Manually** — edit `data/inventory_YYYY-MM-DD.md` with new rows, then run:
   ```bash
   python3 scripts/parse_to_json.py
   ```

The parser writes `data/models.json` with normalized fields (vendor, family, variant, release date, status, openness, license, tier, modality, context window, input/output price per 1M tokens, positioning, country, and a `*_source` URL for every value).

## Data schema

Each entry in `models.json` looks like:

```json
{
  "id": "anthropic__claude_sonnet_5",
  "vendor": "Anthropic",
  "family": "Claude 5",
  "variant": "Claude Sonnet 5",
  "release_date": "2026-05-20",
  "status": "current",
  "openness": "Closed API",
  "license": null,
  "tier": "Balanced / mid",
  "modality": "Text+Vision",
  "context_window": 200000,
  "price_input_per_1m": 3.0,
  "price_output_per_1m": 15.0,
  "positioning": "Balanced performance and cost for everyday agentic work.",
  "country": "USA",
  "release_date_source": "https://...",
  "price_input_source": "https://...",
  "...": "every non-trivial field has a matching *_source URL"
}
```

## Notes and caveats

- **Prices** are USD per 1M tokens on the vendor's own primary API at standard tier. Batch discounts, cached-input pricing, and prompt caching are not reflected. For open-weights models without a first-party API, a representative host's price may be shown (noted in the source link).
- **Missing prices** (roughly 50 of 165 models) are almost all open-weights models without vendor-hosted inference. The dashboard shows `—` rather than guessing.
- **Release dates** for a handful of legacy models (e.g. gpt-3.5-turbo, o1-pro) are marked `n.a.` rather than fabricated.
- **Tier assignments** reflect each vendor's own positioning at the time of release, paraphrased into a common vocabulary.

## License

[MIT](./LICENSE) — use it however you want, just don't sue me.
