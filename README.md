# eBay Cassini Diagnostic Tool

**Free tool for eBay sellers** — Analyze your Active Listings CSV from Seller Hub and get prioritized fixes + smart suggested titles.

Built by Tom Adelstein (USWatchMasters) to help sellers fix zero-view listings and improve sales in 2026.

## Features
- Upload your "All active listings" CSV
- Instant prioritized scoring (CRITICAL → HIGH → MEDIUM → GOOD)
- Smart suggested titles
- Summary dashboard
- Download full report as CSV
- Guidance for the new eBay listing form

## How to Use
1. Seller Hub → Reports → Download → **All active listings**
2. Upload the CSV here
3. Focus on CRITICAL and HIGH listings first
4. Copy Suggested Titles when creating new listings
5. Add "New without tags" at the end of the title
6. Put condition details in the Description field

## Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
