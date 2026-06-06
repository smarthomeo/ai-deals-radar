#!/usr/bin/env python3
"""Export classified deals from SQLite to deals.json for the static site."""

import sqlite3
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "ai-deals-pipeline" / "deals.db"
OUTPUT_PATH = Path(__file__).parent.parent / "deals.json"
MAX_DAYS = 90  # Rolling window


def export_deals():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_DAYS)).isoformat()

    cur.execute(
        """
        SELECT
            ci.id,
            ri.source,
            ri.title,
            ri.url as source_url,
            ri.author,
            ri.published_at,
            ci.score,
            ci.tool_name,
            ci.deal_type,
            ci.deal_details,
            ci.classified_at
        FROM classified_items ci
        JOIN raw_items ri ON ci.raw_item_id = ri.id
        WHERE ci.is_deal = 1
          AND ri.published_at >= ?
        ORDER BY ci.score DESC, ri.published_at DESC
        """,
        (cutoff,),
    )

    deals = []
    for row in cur.fetchall():
        details = {}
        if row["deal_details"]:
            try:
                details = json.loads(row["deal_details"])
            except json.JSONDecodeError:
                pass

        deals.append(
            {
                "id": row["id"],
                "source": row["source"],
                "title": row["title"],
                "source_url": row["source_url"],
                "author": row["author"],
                "published_at": row["published_at"],
                "score": row["score"],
                "tool_name": details.get("tool_name") or row["tool_name"] or "Unknown",
                "normalized_brand": details.get("normalized_brand", ""),
                "deal_type": row["deal_type"] or details.get("deal_type", "unknown"),
                "deal_url": details.get("tool_url") or row["source_url"],
                "discount_percent": details.get("discount_percent", ""),
                "discount_amount": details.get("discount_amount", ""),
                "discount_code": details.get("discount_code", ""),
                "price_info": details.get("price_info", ""),
                "free_tier_details": details.get("free_tier_details", ""),
                "free_trial_details": details.get("free_trial_details", ""),
                "free_api_credits": details.get("free_api_credits", ""),
                "how_to_claim": details.get("how_to_claim", ""),
                "expiry": details.get("expiry", ""),
                "summary": details.get("summary", ""),
                "is_ai_model": details.get("is_ai_model", False),
                "model_provider": details.get("model_provider", ""),
            }
        )

    conn.close()

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(deals),
        "window_days": MAX_DAYS,
        "deals": deals,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Exported {len(deals)} deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    export_deals()
