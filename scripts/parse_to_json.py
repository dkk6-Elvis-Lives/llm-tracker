"""Parse the research subagent's markdown table into a structured models.json."""
import json
import re
from datetime import datetime
from pathlib import Path

# Paths are relative to the repo root. Update SRC when you add a new dated inventory file.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "data" / "inventory_2026-08-04.md"
OUT = REPO_ROOT / "data" / "models.json"

# Regex to extract markdown links: [text](url). Also captures plain text.
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def parse_cell(cell):
    """Return {value, source}. If cell is a markdown link, split text and URL.
    If cell is plain (like 'USA' or 'n.a.'), source is None."""
    cell = cell.strip()
    if not cell or cell.lower() == "n.a.":
        return {"value": None, "source": None}
    m = LINK_RE.fullmatch(cell)
    if m:
        return {"value": m.group(1).strip(), "source": m.group(2).strip()}
    # Multiple links or mixed content? Take first link's text as value.
    m = LINK_RE.search(cell)
    if m:
        return {"value": m.group(1).strip(), "source": m.group(2).strip()}
    return {"value": cell, "source": None}


def parse_price(text):
    """Convert '2.50', '2', or '3 (intro 2 through ...)' to leading float."""
    if text is None:
        return None
    text = text.replace(",", "").replace("$", "").strip()
    # extract leading number
    m = re.match(r"^([\d.]+)", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def parse_context(text):
    """'200,000' or '1,047,576' or '1M' or '200K' or '128k' -> int tokens."""
    if text is None:
        return None
    t = text.replace(",", "").strip().upper()
    # Extract leading number+suffix
    m = re.match(r"^([\d.]+)\s*([KM])?", t)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2) == "K":
        n *= 1_000
    elif m.group(2) == "M":
        n *= 1_000_000
    return int(n)


def parse_release(text):
    """Normalize to YYYY-MM-DD or YYYY-MM."""
    if text is None:
        return None
    t = text.strip()
    # try full date, then year-month, then year
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(t, fmt)
            if fmt == "%Y-%m-%d":
                return t
            if fmt == "%Y-%m":
                return t
            return t
        except ValueError:
            pass
    return t


def normalize_status(v):
    if v is None:
        return None
    vl = v.lower()
    if vl.startswith("current"):
        return "current"
    if "deprecated" in vl or "retired" in vl or "shutdown" in vl:
        return "deprecated"
    if "superseded" in vl:
        return "superseded"
    return v


def normalize_tier(v):
    if v is None:
        return None
    return v.strip()


def normalize_modality(v):
    if v is None:
        return None
    return v.strip()


def normalize_openness(v):
    if v is None:
        return None
    vl = v.lower()
    if "closed" in vl:
        return "Closed API"
    if "open" in vl:
        return "Open weights"
    return v.strip()


def openness_license(v):
    """Extract license name from full openness text like 'Open weights (Apache 2.0)'."""
    if v is None:
        return None
    m = re.search(r"\(([^)]+)\)", v)
    if m:
        return m.group(1).strip()
    return None


def main():
    text = SRC.read_text()
    lines = text.splitlines()

    # Find header row
    rows = []
    header_seen = False
    for line in lines:
        if not line.startswith("|"):
            continue
        # Split on | but drop leading/trailing empty
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if not header_seen:
            if parts and parts[0] == "Vendor":
                header_seen = True
            continue
        # Skip separator row of --- cells
        if all(re.fullmatch(r"[-:]+", p) for p in parts):
            continue
        if len(parts) != 13:
            continue
        rows.append(parts)

    models = []
    for i, parts in enumerate(rows):
        vendor = parts[0]
        family = parts[1]
        variant = parts[2]
        release = parse_cell(parts[3])
        status = parse_cell(parts[4])
        openness = parse_cell(parts[5])
        tier = parse_cell(parts[6])
        modality = parse_cell(parts[7])
        ctx = parse_cell(parts[8])
        inp = parse_cell(parts[9])
        out = parse_cell(parts[10])
        pos = parse_cell(parts[11])
        country = parts[12].strip()

        # Deprecation date extraction from status text
        deprecation_date = None
        if status["value"]:
            m = re.search(r"(shutdown|retired)\s+(\d{4}-\d{2}-\d{2})", status["value"], re.I)
            if m:
                deprecation_date = m.group(2)

        model = {
            "id": f"{vendor.lower().replace(' ', '_').replace('/', '_')}__{variant.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')}",
            "vendor": vendor,
            "family": family,
            "variant": variant,
            "release_date": parse_release(release["value"]),
            "release_date_source": release["source"],
            "status": normalize_status(status["value"]),
            "status_raw": status["value"],
            "status_source": status["source"],
            "deprecation_date": deprecation_date,
            "openness": normalize_openness(openness["value"]),
            "openness_raw": openness["value"],
            "license": openness_license(openness["value"]),
            "openness_source": openness["source"],
            "tier": normalize_tier(tier["value"]),
            "tier_source": tier["source"],
            "modality": normalize_modality(modality["value"]),
            "modality_source": modality["source"],
            "context_window": parse_context(ctx["value"]),
            "context_window_source": ctx["source"],
            "price_input_per_1m": parse_price(inp["value"]),
            "price_input_source": inp["source"],
            "price_output_per_1m": parse_price(out["value"]),
            "price_output_source": out["source"],
            "positioning": pos["value"],
            "positioning_source": pos["source"],
            "country": country,
        }
        models.append(model)

    # Sort: vendor A-Z, then by release date desc (nulls last)
    def sort_key(m):
        d = m["release_date"] or "0000-00"
        return (m["vendor"], d)

    models.sort(key=sort_key)

    payload = {
        "last_updated": "2026-08-04",
        "source_document": "llm_inventory_2026-08-04.md",
        "notes": "Every field with a *_source suffix links to the exact URL the value was verified against. Prices are USD per 1M tokens on vendor primary API when available.",
        "vendors": sorted(set(m["vendor"] for m in models)),
        "count": len(models),
        "models": models,
    }

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT} with {len(models)} models across {len(payload['vendors'])} vendors")
    # Quick sanity summary
    by_vendor = {}
    for m in models:
        by_vendor.setdefault(m["vendor"], 0)
        by_vendor[m["vendor"]] += 1
    for v, n in sorted(by_vendor.items(), key=lambda x: -x[1]):
        print(f"  {v}: {n}")


if __name__ == "__main__":
    main()
