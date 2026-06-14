#!/usr/bin/env python3
"""Export classified deals from SQLite to deals.json for the static site."""

import sqlite3
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "ai-deals-pipeline" / "deals.db"


def _parse_verification_evidence(raw: str) -> str:
    """Extract evidence string from verification_details JSON."""
    if not raw:
        return ""
    try:
        data = json.loads(raw)
        return data.get("evidence", "")
    except (json.JSONDecodeError, TypeError):
        return ""
OUTPUT_PATH = Path(__file__).parent.parent / "deals.json"
MAX_DAYS = 90  # Rolling window

# Deal type → color mapping for UI
DEAL_TYPE_COLORS = {
    "free_tier": "#10b981",
    "free_api_credits": "#06b6d4",
    "free_trial": "#8b5cf6",
    "discount": "#f59e0b",
    "promo_code": "#ec4899",
    "lifetime_deal": "#6366f1",
    "giveaway": "#f97316",
    "price_cut": "#ef4444",
    "launch": "#3b82f6",
}


def _compute_brand_logo(brand: str) -> str:
    """Generate UI Avatars URL for brand."""
    if not brand:
        return ""
    from urllib.parse import quote
    return f"https://ui-avatars.com/api/?name={quote(brand)}&background=6366f1&color=fff&size=64&bold=true"


def _compute_display_price(details: dict) -> str:
    """Compute a human-readable display price from deal details."""
    discount_pct = details.get("discount_percent", "")
    discount_amt = details.get("discount_amount", "")
    price_info = details.get("price_info", "")
    free_tier = details.get("free_tier_details", "")
    free_credits = details.get("free_api_credits", "")

    if free_tier:
        return "Free"
    if free_credits:
        return f"Free ({free_credits})" if isinstance(free_credits, str) and len(free_credits) < 30 else "Free Credits"
    if discount_pct:
        return f"{discount_pct}% off"
    if discount_amt:
        return f"{discount_amt} off"
    if price_info:
        return price_info[:50]
    return ""


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
            ci.classified_at,
            ci.verification_status,
            ci.verified_at,
            ci.verification_details
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

        # Computed fields
        now = datetime.now(timezone.utc)
        pub_date = None
        days_old = 0
        is_new = False
        is_expiring_soon = False
        try:
            if row["published_at"]:
                pub_date = datetime.fromisoformat(row["published_at"].replace("Z", "+00:00"))
                days_old = (now - pub_date).days
                is_new = days_old < 1
        except (ValueError, TypeError):
            pass

        expiry_str = details.get("expiry", "")
        if expiry_str:
            try:
                exp = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                is_expiring_soon = 0 < (exp - now).days < 7
            except (ValueError, TypeError):
                pass

        brand = details.get("normalized_brand", "")
        deal_type = row["deal_type"] or details.get("deal_type", "unknown")

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
                "normalized_brand": brand,
                "deal_type": deal_type,
                "deal_url": details.get("tool_url") or row["source_url"],
                "discount_percent": details.get("discount_percent", ""),
                "discount_amount": details.get("discount_amount", ""),
                "discount_code": details.get("discount_code", ""),
                "price_info": details.get("price_info", ""),
                "free_tier_details": details.get("free_tier_details", ""),
                "free_trial_details": details.get("free_trial_details", ""),
                "free_api_credits": details.get("free_api_credits", ""),
                "how_to_claim": details.get("how_to_claim", ""),
                "expiry": expiry_str,
                "summary": details.get("summary", ""),
                "is_ai_model": details.get("is_ai_model", False),
                "model_provider": details.get("model_provider", ""),
                "verification_status": row["verification_status"] or "unverified",
                "verified_at": row["verified_at"] or "",
                "verification_evidence": _parse_verification_evidence(row["verification_details"]),
                # Computed fields for UI
                "days_old": days_old,
                "is_new": is_new,
                "is_expiring_soon": is_expiring_soon,
                "brand_logo_url": _compute_brand_logo(brand),
                "display_price": _compute_display_price(details),
                "category_color": DEAL_TYPE_COLORS.get(deal_type, "#64748b"),
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
