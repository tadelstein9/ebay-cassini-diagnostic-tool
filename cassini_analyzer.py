# cassini_analyzer.py
# Version 4.0 - Multi-category support
# April 08, 2026

import pandas as pd

# ---------------------------------------------------------------------------
# Category keyword sets
# Each category has power keywords that signal a well-optimized listing.
# Add new categories here — the rest of the code adapts automatically.
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS = {
    "watches_jewelry": [
        "waldemar", "double albert", "unitas", "6498", "6497", "arnex",
        "pocket watch chain", "swivel fob", "lobster clasp", "double curb",
        "flieger", "pilot watch", "pt5000", "automatic", "mechanical",
        "sterling silver", "gold filled", "hallmark", "signed", "vintage"
    ],
    "clothing_fashion": [
        "vintage", "retro", "designer", "brand new with tags", "nwt",
        "size", "wool", "leather", "silk", "cotton", "linen", "denim",
        "made in usa", "made in italy", "deadstock", "1950s", "1960s",
        "1970s", "1980s", "rare", "collectible"
    ],
    "sports_cards_collectibles": [
        "psa", "bgs", "graded", "rookie", "refractor", "auto", "autograph",
        "numbered", "parallel", "holographic", "mint", "gem mint",
        "1st edition", "holo", "foil", "error card", "short print"
    ],
    "electronics": [
        "unlocked", "original", "oem", "tested working", "refurbished",
        "4k", "hd", "wifi", "bluetooth", "usb-c", "fast charging",
        "original box", "mint condition", "no reserve"
    ],
    "vintage_antiques": [
        "antique", "vintage", "rare", "collectible", "signed", "numbered",
        "original", "authentic", "19th century", "art deco", "victorian",
        "edwardian", "arts and crafts", "mid century", "depression glass",
        "bakelite", "sterling", "cast iron", "hand painted"
    ],
    "tools_hardware": [
        "usa made", "vintage", "working", "restored", "professional grade",
        "heavy duty", "set", "lot", "complete", "original", "rare",
        "machinist", "watchmaker", "jeweler", "craftsman", "snap-on",
        "proto", "starrett", "mitutoyo"
    ],
    "books_media": [
        "first edition", "signed", "hardcover", "rare", "out of print",
        "mint", "fine", "like new", "collectible", "illustrated",
        "limited edition", "ex library", "vintage", "antique"
    ],
    "coins_currency": [
        "ms", "pcgs", "ngc", "anacs", "proof", "uncirculated", "bu",
        "key date", "rare", "silver", "gold", "copper", "mint mark",
        "error", "variety", "toned", "original skin"
    ],
    "general": [
        "new without tags", "new with tags", "excellent condition",
        "tested working", "free shipping", "lot", "set", "rare",
        "vintage", "collectible", "original"
    ]
}

# Category detection — maps eBay category names to our keyword sets
CATEGORY_MAP = {
    "chains": "watches_jewelry",
    "fob": "watches_jewelry",
    "watch": "watches_jewelry",
    "jewelry": "watches_jewelry",
    "ring": "watches_jewelry",
    "necklace": "watches_jewelry",
    "bracelet": "watches_jewelry",
    "clothing": "clothing_fashion",
    "shirt": "clothing_fashion",
    "dress": "clothing_fashion",
    "pants": "clothing_fashion",
    "shoes": "clothing_fashion",
    "fashion": "clothing_fashion",
    "card": "sports_cards_collectibles",
    "sports": "sports_cards_collectibles",
    "trading": "sports_cards_collectibles",
    "pokemon": "sports_cards_collectibles",
    "phone": "electronics",
    "tablet": "electronics",
    "laptop": "electronics",
    "computer": "electronics",
    "camera": "electronics",
    "electronic": "electronics",
    "antique": "vintage_antiques",
    "vintage": "vintage_antiques",
    "collectible": "vintage_antiques",
    "pottery": "vintage_antiques",
    "glassware": "vintage_antiques",
    "tool": "tools_hardware",
    "hardware": "tools_hardware",
    "machinist": "tools_hardware",
    "book": "books_media",
    "magazine": "books_media",
    "vinyl": "books_media",
    "record": "books_media",
    "coin": "coins_currency",
    "stamp": "coins_currency",
    "currency": "coins_currency",
    "bullion": "coins_currency",
}


def detect_category(row):
    """
    Detect category from eBay category name or title keywords.
    Returns a key from CATEGORY_KEYWORDS.
    """
    category_field = str(row.get('eBay category 1 name', '') or '').lower()
    title = str(row.get('Title', '') or '').lower()
    combined = category_field + ' ' + title

    for keyword, category in CATEGORY_MAP.items():
        if keyword in combined:
            return category

    return 'general'


def normalize_columns(df):
    col_map = {
        'title': 'Title',
        'item title': 'Title',
        'current price': 'Price',
        'start price': 'Price',
        'available quantity': 'Available Qty',
        'quantity': 'Available Qty',
        'views': 'Views',
        'watchers': 'Watchers',
        'custom label': 'Custom Label',
        'condition': 'Condition',
        'ebay category 1 name': 'eBay category 1 name',
        'item number': 'Item number',
        'sold quantity': 'Sold quantity',
    }
    for old, new in col_map.items():
        for col in list(df.columns):
            if old.lower() in col.lower() and new not in df.columns:
                df = df.rename(columns={col: new})
                break
    return df


def calculate_cassini_score(row):
    title = str(row.get('Title', '')).strip()
    t_lower = title.lower()

    # Detect category and load appropriate keywords
    category = detect_category(row)
    strong_keywords = CATEGORY_KEYWORDS.get(category, CATEGORY_KEYWORDS['general'])

    score = 60
    issues = []
    fixes = []

    # 1. Keyword match (up to +25 pts)
    match_count = sum(1 for kw in strong_keywords if kw in t_lower)
    if match_count >= 2:
        score += 25
    elif match_count == 1:
        score += 12
    else:
        issues.append("Weak keyword match for this category")
        fixes.append(f"Add strong keywords for {category.replace('_', ' ')} category")

    # 2. Title length
    title_len = len(title)
    if title_len < 50:
        issues.append(f"Title too short ({title_len} chars)")
        fixes.append("Expand title with key details — target 60–80 characters")
        score -= 8
    elif title_len > 90:
        issues.append(f"Title too long ({title_len} chars)")
        fixes.append("Shorten to 75–80 characters")
        score -= 6

    # 3. Condition signal in title
    condition_words = [
        "new without tags", "new with tags", "serviced", "restored",
        "excellent condition", "mint", "like new", "graded", "tested working",
        "nwt", "nib", "nos", "deadstock"
    ]
    has_condition = any(word in t_lower for word in condition_words)
    if not has_condition:
        issues.append("Missing condition signal in title")
        fixes.append("Add condition signal e.g. 'New without tags' or 'Excellent condition'")
        score -= 15

    # 4. Views signal
    views = pd.to_numeric(row.get('Views', 0), errors='coerce') or 0
    watchers = pd.to_numeric(row.get('Watchers', 0), errors='coerce') or 0
    if views == 0 and watchers == 0:
        issues.append("Zero views and zero watchers — listing may be suppressed")
        fixes.append("Consider Sell Similar if listing is 90+ days old")
        score -= 8
    elif views < 10:
        score -= 4

    # 5. Generate suggested title
    suggested = generate_suggested_title(title, t_lower, category, strong_keywords)
    suggested = suggested[:80]

    score = max(15, min(100, score))

    if score <= 45:
        priority = "CRITICAL"
    elif score <= 65:
        priority = "HIGH"
    elif score <= 80:
        priority = "MEDIUM"
    else:
        priority = "GOOD"

    return {
        "Priority": priority,
        "Cassini Score": round(score),
        "Category": category.replace('_', ' ').title(),
        "Title": title,
        "Suggested Title": suggested,
        "Main Issue": issues[0] if issues else "Strong baseline",
        "Issues": " | ".join(issues) if issues else "Strong baseline",
        "Fixes": " | ".join(fixes) if fixes else "Ready to promote",
        "Available Qty": row.get("Available Qty", ""),
        "Price": row.get("Price", ""),
        "Views": views,
        "Watchers": watchers,
        "Item number": row.get("Item number", ""),
        "Sold quantity": row.get("Sold quantity", ""),
    }


def generate_suggested_title(title, t_lower, category, strong_keywords):
    """Generate an improved title suggestion based on category."""
    suggested = title

    if category == "watches_jewelry":
        if "waldemar" in t_lower or "double albert" in t_lower:
            base = "Waldemar Pocket Watch Chain" if "waldemar" in t_lower else "Double Albert Pocket Watch Chain"
            parts = title.split(" ", 2)
            suggested = (base + " " + parts[-1] if len(parts) > 2 else base).strip()
        elif "unitas" in t_lower or "arnex" in t_lower:
            suggested = ("Arnex Unitas 6498 Pocket Watch " + title[-40:]).strip()

    elif category == "clothing_fashion":
        if len(title) < 60:
            suggested = title.rstrip() + " Vintage Excellent Condition"

    elif category == "sports_cards_collectibles":
        if "psa" not in t_lower and "bgs" not in t_lower:
            suggested = title.rstrip() + " Mint Condition"

    elif category == "electronics":
        if "unlocked" not in t_lower and "phone" in t_lower:
            suggested = title.rstrip() + " Unlocked"
        elif len(title) < 60:
            suggested = title.rstrip() + " Tested Working"

    elif category == "vintage_antiques":
        if len(title) < 60:
            suggested = title.rstrip() + " Vintage Excellent Condition"

    # Add condition signal if missing
    condition_words = ["new without tags", "new with tags", "mint", "excellent",
                       "tested", "graded", "serviced", "nwt"]
    if not any(w in t_lower for w in condition_words):
        suggested = (suggested + " New without tags").strip()

    return suggested[:80]


def analyze_listings(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    results = [calculate_cassini_score(row) for _, row in df.iterrows()]
    report = pd.DataFrame(results)
    report = report.sort_values("Cassini Score").reset_index(drop=True)
    return report


def get_summary(report: pd.DataFrame):
    avg_score = round(report["Cassini Score"].mean(), 1)
    total = len(report)
    critical = (report["Priority"] == "CRITICAL").sum()
    high = (report["Priority"] == "HIGH").sum()

    # Category breakdown
    if "Category" in report.columns:
        category_counts = report["Category"].value_counts().to_dict()
    else:
        category_counts = {}

    return {
        "Total Listings": total,
        "Average Cassini Score": f"{avg_score}/100",
        "CRITICAL to Fix": critical,
        "HIGH Priority": high,
        "Categories Detected": category_counts,
    }
