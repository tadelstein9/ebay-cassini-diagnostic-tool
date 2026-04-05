# cassini_analyzer.py
# Version 3.7 - Final safe version for public use
# April 05, 2026

import pandas as pd

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
        'condition': 'Condition'
    }
    for old, new in col_map.items():
        for col in list(df.columns):
            if old.lower() in col.lower():
                df = df.rename(columns={col: new})
                break
    return df

def calculate_cassini_score(row):
    title = str(row.get('Title', '')).strip()
    t_lower = title.lower()
    
    score = 60
    issues = []
    fixes = []
    
    strong_keywords = ["waldemar", "double albert", "unitas", "6498", "arnex", 
                       "pocket watch chain", "swivel fob", "lobster clasp", "double curb"]
    
    match_count = sum(1 for kw in strong_keywords if kw in t_lower)
    
    if match_count >= 2:
        score += 25
    elif match_count == 1:
        score += 12
    else:
        issues.append("Weak keyword match")
        fixes.append("Add keywords like Waldemar or Unitas")
    
    title_len = len(title)
    if title_len < 50:
        issues.append("Title too short")
        fixes.append("Expand with key details")
        score -= 8
    elif title_len > 90:
        issues.append("Title too long")
        fixes.append("Shorten to 75-80 characters")
        score -= 6
    
    has_condition = any(word in t_lower for word in ["new without tags", "new with tags", "serviced", "restored", "excellent condition"])
    if not has_condition:
        issues.append("Missing condition signal")
        fixes.append("Add New without tags at the end")
        score -= 15
    
    views = pd.to_numeric(row.get('Views', 0), errors='coerce') or 0
    if views == 0:
        issues.append("Zero views")
        fixes.append("Improve title and consider Promoted Listings")
        score -= 8
    elif views < 10:
        score -= 4
    
    # Safe suggested title
    suggested = title
    if "waldemar" in t_lower or "double albert" in t_lower:
        base = "Waldemar Pocket Watch Chain" if "waldemar" in t_lower else "Double Albert Pocket Watch Chain"
        suggested = (base + " " + title.split(" ", 2)[-1] if len(title.split(" ")) > 2 else base).strip()
    elif "unitas" in t_lower or "arnex" in t_lower:
        suggested = ("Arnex Unitas 6498 Pocket Watch " + title[-40:]).strip()
    
    if "new without tags" not in t_lower:
        suggested = (suggested + " New without tags").strip()[:80]
    
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
        "Title": title,
        "Suggested Title": suggested,
        "Issues": " | ".join(issues) if issues else "Strong baseline",
        "Fixes": " | ".join(fixes) if fixes else "Ready to promote",
        "Available Qty": row.get("Available Qty", ""),
        "Price": row.get("Price", ""),
        "Views": views
    }

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
    high_potential = (report["Title"].str.lower().str.contains("waldemar|double albert|unitas|arnex")).sum()
    
    return {
        "Total Listings": total,
        "Average Cassini Score": f"{avg_score}/100",
        "CRITICAL to Fix": critical,
        "HIGH Priority": high,
        "High Potential Items": high_potential
    }
