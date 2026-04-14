#!/usr/bin/env python3
# cassini_analyzer.py
# Version 5.0 - Database-backed scoring using eBay Taxonomy API data
# April 14, 2026

import pandas as pd
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "cassini.db")

CATEGORY_MAP = {
    "wristwatch": "31387",
    "pocket watch": "3937",
    "chain": "260329",
    "fob": "260329",
    "waldemar": "260329",
    "albert": "260329",
    "movement": "57720",
    "tool": "117039",
    "repair": "117039",
    "laptop": "177",
    "watch box": "260330",
    "display": "260330",
    "strap": "98624",
    "band": "98624",
}

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def detect_category_id(row):
    title = str(row.get("Title", "")).lower()
    for keyword, cat_id in CATEGORY_MAP.items():
        if keyword in title:
            return cat_id
    return "31387"

def get_required_fields(category_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT aspect_name, aspect_mode, required FROM item_specifics WHERE category_id=? AND required=1", (category_id,))
    required = [dict(r) for r in c.fetchall()]
    conn.close()
    return required

def get_selection_only_fields(category_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT aspect_name FROM item_specifics WHERE category_id=? AND aspect_mode=?", (category_id, "SELECTION_ONLY"))
    fields = [r[0] for r in c.fetchall()]
    conn.close()
    return fields

def get_allowed_values(category_id, aspect_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT v.value FROM allowed_values v
        JOIN item_specifics s ON v.specific_id = s.id
        WHERE s.category_id=? AND s.aspect_name=?""", (category_id, aspect_name))
    values = [r[0] for r in c.fetchall()]
    conn.close()
    return values

def calculate_cassini_score(row):
    title = str(row.get("Title", "")).strip()
    t_lower = title.lower()
    category_id = detect_category_id(row)
    score = 60
    issues = []
    fixes = []

    # 1. Title length
    title_len = len(title)
    if title_len < 50:
        issues.append(f"Title too short ({title_len} chars)")
        fixes.append("Expand title — target 60-80 characters")
        score -= 8
    elif title_len > 90:
        issues.append(f"Title too long ({title_len} chars)")
        fixes.append("Shorten to 75-80 characters")
        score -= 6

    # 2. Condition signal in title
    condition_words = ["new without tags", "new with tags", "serviced", "restored",
        "excellent condition", "mint", "like new", "nwt", "nib", "nos", "refurbished", "seller refurbished", "pre-owned", "remanufactured"]
    if not any(w in t_lower for w in condition_words):
        issues.append("Missing condition signal in title")
        fixes.append("Add condition signal e.g. New without tags")
        score -= 10

    # 3. Required fields check via database
    required_fields = get_required_fields(category_id)
    for field in required_fields:
        field_name = field["aspect_name"]
        col_val = str(row.get(field_name, "")).strip()
        if not col_val or col_val.lower() in ["nan", "none", ""]:
            issues.append(f"Missing required field: {field_name}")
            fixes.append(f"Add {field_name} to item specifics")
            score -= 10

    # 4. SELECTION_ONLY fields check
    selection_fields = get_selection_only_fields(category_id)
    for field in selection_fields[:5]:
        col_val = str(row.get(field, "")).strip()
        if not col_val or col_val.lower() in ["nan", "none", ""]:
            issues.append(f"Missing Cassini filter field: {field}")
            fixes.append(f"Add {field} — buyers filter by this")
            score -= 5

    # 5. Views signal
    views = pd.to_numeric(row.get("Views", 0), errors="coerce") or 0
    watchers = pd.to_numeric(row.get("Watchers", 0), errors="coerce") or 0
    if views == 0 and watchers == 0:
        issues.append("Zero views and watchers — listing may be suppressed")
        fixes.append("Consider Sell Similar if listing is 90+ days old")
        score -= 8
    elif views < 10:
        score -= 4

    # Suggested title
    suggested = generate_suggested_title(title, t_lower, category_id)
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
        "Score": score,
        "Priority": priority,
        "Issues": " | ".join(issues) if issues else "None",
        "Fixes": " | ".join(fixes) if fixes else "None",
        "Suggested Title": suggested,
        "Category ID": category_id,
    }

def generate_suggested_title(title, t_lower, category_id):
    suggested = title.strip()
    condition_words = ["new without tags", "serviced", "restored", "nos"]
    if not any(w in t_lower for w in condition_words):
        if len(suggested) < 70:
            suggested = suggested + " New without tags"
        else:
            suggested = suggested[:65] + " New without tags"
    return suggested[:80]

def analyze_listings(df):
    results = []
    for _, row in df.iterrows():
        score_data = calculate_cassini_score(row)
        result = {
            "Title": str(row.get("Title", ""))[:60],
            "Price": row.get("Start Price", row.get("Buy It Now Price", "")),
            "Views": row.get("Views", 0),
            "Watchers": row.get("Watchers", 0),
        }
        result.update(score_data)
        results.append(result)
    return pd.DataFrame(results).sort_values("Score")
