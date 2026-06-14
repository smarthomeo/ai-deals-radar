# AI Deals Radar — State-of-the-Art Redesign

Rebuild the AI Deals Radar website and pipeline to be a professional, beautiful, 
highly usable deals discovery platform. The current site at /root/ai-deals-radar/ 
is a basic dark-theme card grid. Transform it into something that looks and works 
like a premium product (think Linear, Vercel Dashboard, or Product Hunt quality).

## STOP CONDITION
1. The website at /root/ai-deals-radar/index.html is a complete single-file SPA 
   that looks professional, modern, and polished — not a "developer project"
2. All 337 deals from deals.json render correctly with rich filtering
3. The site is fully responsive (mobile, tablet, desktop)
4. Run: python3 /root/ai-deals-radar/scripts/export_deals.py && echo "Export OK"
5. The index.html works as a standalone file (no build step, no npm, just open in browser)

## CONTEXT

### Current State
- Pipeline: /root/ai-deals-pipeline/ — collects from Twitter, YouTube, HN, deal sites
- Website: /root/ai-deals-radar/ — static GitHub Pages site
- DB: /root/ai-deals-pipeline/deals.db — 337 deals, 6128 raw items
- Data: /root/ai-deals-radar/deals.json — 337 deals with rich metadata
- Live: https://smarthomeo.github.io/ai-deals-radar/

### Deal Data Structure (from deals.json)
Each deal has:
  id, source, title, source_url, author, published_at, score (1-5),
  tool_name, normalized_brand, deal_type, deal_url, discount_percent,
  discount_amount, discount_code, price_info, free_tier_details,
  free_trial_details, free_api_credits, how_to_claim, expiry, summary,
  is_ai_model, model_provider, verification_status, verified_at,
  verification_evidence

### Deal Type Distribution
  free_api_credits: 97, free_tier: 75, twitter: 232, twitter_account: 98,
  promo_code: 43, discount: 41, free_trial: 32, lifetime_deal: 22,
  giveaway: 13, price_cut: 13, launch: 1

### Source Distribution
  twitter: 232, twitter_account: 98, youtube: 5, hackernews: 2

## STEP 1: Redesign index.html — Premium SPA

Create a COMPLETELY NEW index.html that is a state-of-the-art single-page app.

### Design Requirements
- **Visual Style**: Dark theme with subtle gradients, glass-morphism cards, 
  smooth animations. Think Linear.app meets Product Hunt.
- **Typography**: Inter or system font stack, clear hierarchy (h1/h2/body/caption)
- **Color Palette**: 
  - Background: #0a0a0f (near-black) with subtle radial gradients
  - Cards: rgba(255,255,255,0.03) with backdrop-blur, subtle border
  - Accent: #6366f1 (indigo) for primary actions
  - Success: #10b981 (emerald) for active deals
  - Warning: #f59e0b (amber) for expiring
  - Danger: #ef4444 (red) for expired
  - Categories: unique color per deal_type
- **Layout**: 
  - Hero section with animated stats counter (total deals, tools tracked, sources)
  - Category tabs/chips at top (Free Tier, Lifetime Deal, Discount, Promo Code, 
    Free API Credits, Free Trial, Giveaway, Price Cut, Launch)
  - Each category shows count badge
  - "All" tab selected by default
  - Deal cards in a responsive masonry-like grid (CSS grid with auto-fill)
  - Sticky header with search + quick filters

### Card Design (MUST be information-rich but clean)
Each card should show:
  - Deal type badge (color-coded, top-left)
  - Verification badge (verified=green check, unverified=gray, suspicious=yellow, 
    expired=red X — top-right)
  - Tool/brand name (bold, prominent)
  - Title (1-2 lines, truncated)
  - Summary (2-3 lines, truncated)
  - Key deal info highlighted: discount %, price, free tier details
  - Promo code (if exists) — click-to-copy with visual feedback
  - Source icon + date
  - Score indicator (1-5 dots or bar)
  - "Claim Deal" button that opens source_url in new tab
  - Expandable detail section (click card to expand, shows full info: 
    how_to_claim, expiry, free_trial_details, verification_evidence)

### Filter/Sort Panel (left sidebar on desktop, top bar on mobile)
  - Search: real-time fuzzy search across title, summary, tool_name, brand
  - Deal Type: multi-select chips (with counts)
  - Source: multi-select (Twitter, YouTube, HN, Deal Sites)
  - Score: range slider (1-5)
  - Verification: toggle buttons (All, Verified, Unverified, Suspicious, Expired)
  - Price Range: "Free Only", "Under $10", "Under $50", "Any"
  - Expiry: "Active Only", "Expiring Soon (<7d)", "All"
  - AI Model toggle: show only AI model deals vs tools
  - Sort: Latest, Highest Score, Most Relevant, Expiring Soon
  - Clear All Filters button
  - URL hash sync (so filtered views are shareable)

### Additional Features
  - Dark/light theme toggle (default dark)
  - "New" badge on deals from last 24h
  - "Expiring Soon" badge on deals with expiry < 7 days
  - Skeleton loading animation while fetching deals.json
  - Empty state with illustration when no deals match filters
  - Stats dashboard: deals by type (donut chart via CSS), deals over time, 
    top brands leaderboard
  - Keyboard shortcuts: / to focus search, Esc to clear, j/k to navigate cards
  - Share button per card (copies deal URL with hash)
  - Infinite scroll or "Load More" (don't render all 337 at once)
  - Smooth scroll animations (cards fade in as they enter viewport)

### Technical Requirements
  - Single index.html file (inline CSS + JS, no external deps except Google Fonts)
  - No framework (vanilla JS, no React/Vue/etc.)
  - Fetch deals.json via relative path
  - CSS Grid + Flexbox for layout
  - CSS custom properties for theming
  - IntersectionObserver for lazy loading / scroll animations
  - URL hash for filter state persistence
  - LocalStorage for theme preference
  - Must work offline after first load (deals.json cached)

## STEP 2: Improve export_deals.py

Update /root/ai-deals-radar/scripts/export_deals.py to include additional 
computed fields that make the website better:

  - days_old: computed from published_at
  - is_expiring_soon: true if expiry exists and < 7 days from now
  - is_new: true if published_at > 24h ago
  - brand_logo_url: construct from normalized_brand using Clearbit or UI Avatars 
    API (https://ui-avatars.com/api/?name=BRAND&background=6366f1&color=fff&size=64)
  - display_price: computed from price_info, discount_amount, free_tier_details
  - category_color: map deal_type to hex color for the UI

## STEP 3: Improve Pipeline Accuracy

Update /root/ai-deals-pipeline/classifier.py to improve classification accuracy:

  - Add a "confidence threshold" — deals with confidence < 0.6 should be marked 
    as "unverified" not auto-accepted
  - Add deal_type validation — ensure deal_type is one of the known types, 
    default to "unknown" if not
  - Better extraction of discount_code — some deals have codes buried in summary 
    but not in discount_code field
  - Add expiry parsing — try to extract dates from summary/details text

## STEP 4: Pipeline Collection Enhancement

Update /root/ai-deals-pipeline/config.yaml to add last30days as a source:

  - Add a new collector that runs: 
    python3 ~/.hermes/skills/research/last30days/scripts/last30days.py 
    "AI deals free tier discount" --days=2 --emit=json
  - Parse the output and feed into the classification pipeline
  - This adds Reddit, HN (beyond current queries), Polymarket, GitHub signals

## STEP 5: Deploy Script

Update /root/ai-deals-radar/scripts/deploy.sh to:
  - Run export_deals.py first
  - Git commit with timestamp
  - Push to main
  - Verify the push succeeded

## CONSTRAINTS
- index.html MUST be a single file with inline CSS/JS — no build step
- Do NOT change the deals.json schema (export_deals.py output must be backward 
  compatible — add new fields, don't rename existing ones)
- Do NOT modify pipeline.py orchestrator logic — only classifier.py and config.yaml
- Keep the dark theme as default (light is optional toggle)
- All text must be html.escape() safe
- The site must work on GitHub Pages (no server-side code)
- Use system font stack + Inter from Google Fonts as the only external dependency

## VERIFY
1. Open /root/ai-deals-radar/index.html in browser — loads deals, renders cards
2. Test all filters work (search, type, source, score, verification)
3. Test mobile responsive at 375px width
4. Click a card — expands to show details
5. Click "Claim Deal" — opens correct URL
6. Promo code click-to-copy works
7. Theme toggle works
8. python3 /root/ai-deals-radar/scripts/export_deals.py runs without errors
9. All 337 deals render (scroll to bottom)
