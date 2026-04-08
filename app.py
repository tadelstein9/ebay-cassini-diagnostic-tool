import streamlit as st
import pandas as pd
from datetime import datetime
from cassini_analyzer import analyze_listings

st.set_page_config(
    page_title="Cassini Tool",
    layout="wide",
    page_icon="📈"
)

st.title("📈 Cassini Tool")
st.markdown("**Helping eBay sellers improve titles and increase sales**")

tab1, tab2, tab3, tab4 = st.tabs(["1. Upload CSV", "2. Prioritized Fix List", "3. Download CSV", "4. 📄 Full Report"])

with tab1:
    st.subheader("Step 1: Upload your CSV")
    st.info("Export your Active Listings from eBay Seller Hub → Upload the CSV here.")
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
    if uploaded_file is not None:
        with st.spinner("Analyzing your listings..."):
            df = pd.read_csv(uploaded_file)
            results = analyze_listings(df)
            st.session_state['results'] = results
            st.session_state['df_raw'] = df
        st.success(f"✅ Successfully analyzed {len(results)} listings!")

with tab2:
    results = st.session_state.get('results', None)
    if results is not None and not results.empty:
        st.subheader("Prioritized Fix List (Fix Lowest Scores First)")
        available_cols = ['Priority', 'Title', 'Cassini Score', 'Main Issue', 'Suggested Title']
        display_cols = [col for col in available_cols if col in results.columns]
        if display_cols:
            st.dataframe(results[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(results, use_container_width=True, hide_index=True)
        if 'Cassini Score' in results.columns:
            avg_score = results['Cassini Score'].mean()
            st.subheader("Summary & Action Plan")
            st.markdown(f"""
            **Your average Cassini score:** `{avg_score:.0f}/100`

            **Biggest quick win:** Add **"New without tags"** at the end of your titles and front-load strong buyer keywords (such as Waldemar, Double Albert, Arnex, or Unitas 6498).

            **Recommended Action Today:**
            1. Start with the top 10–12 lowest-scoring listings shown above.
            2. Use **Sell Similar** on eBay and paste the Suggested Title.
            3. Make sure "New without tags" also appears naturally in the description.
            4. Turn on Promoted Listings at 5–8% for your strongest items (especially chains and watches).
            """)
    else:
        st.info("↑ Upload your CSV file on the first tab to see prioritized fixes.")

with tab3:
    results = st.session_state.get('results', None)
    if results is not None and not results.empty:
        st.subheader("Export Raw Data as CSV")
        csv = results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Report as CSV",
            data=csv,
            file_name="cassini_recommendations.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.info("**Mobile / iPad users:** Open the downloaded CSV in Google Sheets or Excel → Share → Print → Save as PDF.")
        st.caption("Built for USWatchMasters • Helping the eBay community")
    else:
        st.info("Upload a CSV first to generate your report.")

with tab4:
    results = st.session_state.get('results', None)
    df_raw = st.session_state.get('df_raw', None)

    if results is not None and not results.empty and df_raw is not None:
        st.subheader("Full Diagnostic Report")
        st.markdown("A formatted HTML report you can open in any browser, print, or share. Every listing gets a score, plain-English explanation, and suggested title.")

        if st.button("Generate Full Report", type="primary", use_container_width=True):
            with st.spinner("Building your report..."):
                html = generate_html_report(df_raw)
            st.download_button(
                label="📄 Download HTML Report",
                data=html,
                file_name="cassini_diagnostic_report.html",
                mime="text/html",
                use_container_width=True
            )
            st.success("Report ready. Open it in any browser — Chrome, Firefox, Safari, Edge.")
            st.info("**To print or save as PDF:** Open the HTML file → File → Print → Save as PDF")
    else:
        st.info("↑ Upload your CSV file on the first tab to generate the full report.")


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

def cassini_score_row(row):
    """Score a single CSV row. Returns (score, gaps, actions, found_kw)."""
    score = 0
    gaps = []
    actions = []

    title = str(row.get('Title', '') or '')
    tlen = len(title)

    # 1. Title length (25 pts)
    if tlen >= 60:
        score += 25
    elif tlen >= 40:
        score += 12
        gaps.append(f"Title only {tlen} chars — target 60–80")
        actions.append("Expand title to 60–80 characters. Add material, brand, or use case keywords.")
    else:
        gaps.append(f"Title critically short ({tlen} chars)")
        actions.append("Rewrite title completely. Must be 60–80 chars with strongest keywords first.")

    # 2. Power keywords (25 pts)
    power_kw = [
        'waldemar', 'double albert', 'unitas', 'arnex', '6498', '6497',
        'pt5000', 'flieger', 'pilot', 'pocket watch chain', 'swivel', 'fob'
    ]
    found_kw = [kw for kw in power_kw if kw.lower() in title.lower()]
    if len(found_kw) >= 2:
        score += 25
    elif len(found_kw) == 1:
        score += 12
        gaps.append(f"Only 1 power keyword: '{found_kw[0]}'")
        actions.append("Add a second strong keyword — material (Silver/Brass/Gold), style, or type.")
    else:
        gaps.append("No power keywords detected")
        actions.append("Front-load title with your strongest product terms immediately.")

    # 3. Condition (20 pts)
    condition = str(row.get('Condition', '') or '')
    if condition.strip():
        score += 20
    else:
        gaps.append("Condition not set")
        actions.append("Set condition to 'New without tags' for accessories and chains.")

    # 4. Watchers signal (15 pts)
    try:
        watchers = int(row.get('Watchers', 0) or 0)
    except (ValueError, TypeError):
        watchers = 0
    if watchers >= 10:
        score += 15
    elif watchers >= 3:
        score += 8
    else:
        gaps.append(f"Low watchers ({watchers}) — listing may be suppressed")
        actions.append("Consider Sell Similar to reset listing age if active 60+ days with no views.")

    # 5. Price tier (15 pts)
    try:
        price = float(row.get('Start price', 0) or 0)
    except (ValueError, TypeError):
        price = 0
    if price >= 30:
        score += 15
    elif price >= 15:
        score += 8
    else:
        gaps.append(f"Price ${price:.2f} may signal low value to Cassini")
        actions.append("Review pricing — very low prices can reduce Cassini placement priority.")

    return score, gaps, actions, found_kw


def suggest_title(title, found_kw, tlen):
    """Generate a suggested title improvement."""
    if 'waldemar' in title.lower() and tlen < 70:
        return title.rstrip() + ' New without tags'
    if 'double albert' in title.lower() and tlen < 70:
        return title.rstrip() + ' New without tags'
    if 'pocket watch chain' in title.lower() and tlen < 65:
        return title.rstrip() + ' New without tags'
    if any(w in title.lower() for w in ['cleaning', 'putty', 'pegwood']):
        return 'Watchmaker Cleaning Putty Pegwood Stick Set Watch Repair Tools New without tags'
    if any(w in title.lower() for w in ['winding', 'arbor', 'bergeon']):
        return title.rstrip() + ' Watchmaker Tool New without tags'
    if tlen < 60:
        return title.rstrip() + ' New without tags'
    return title


def generate_html_report(df):
    """
    Build and return a complete HTML diagnostic report as a string.
    Accepts a pandas DataFrame (raw CSV data).
    """
    rows = df.to_dict('records')
    now = datetime.now().strftime('%B %d, %Y at %I:%M %p')

    scored = []
    for row in rows:
        score, gaps, actions, found_kw = cassini_score_row(row)
        try:
            sold = int(row.get('Sold quantity', 0) or 0)
            watchers = int(row.get('Watchers', 0) or 0)
            price = float(row.get('Start price', 0) or 0)
        except (ValueError, TypeError):
            sold = watchers = 0
            price = 0

        title = str(row.get('Title', '') or '')
        tlen = len(title)
        revenue = sold * price
        item_id = str(row.get('Item number', '') or '')
        category = str(row.get('eBay category 1 name', '') or '')
        condition = str(row.get('Condition', '') or '')
        sug = suggest_title(title, found_kw, tlen)

        if score >= 80:
            priority = 'GOOD'
        elif score >= 60:
            priority = 'MEDIUM'
        elif score >= 40:
            priority = 'HIGH'
        else:
            priority = 'CRITICAL'

        scored.append({
            'item_id': item_id, 'title': title, 'tlen': tlen,
            'price': price, 'sold': sold, 'revenue': revenue,
            'watchers': watchers, 'category': category, 'condition': condition,
            'score': score, 'priority': priority,
            'gaps': gaps, 'actions': actions,
            'suggested_title': sug,
            'title_improved': sug != title,
        })

    scored.sort(key=lambda x: x['score'])

    total       = len(scored)
    zero_sold   = len([r for r in scored if r['sold'] == 0])
    avg_score   = sum(r['score'] for r in scored) // total if total else 0
    total_rev   = sum(r['revenue'] for r in scored)
    critical    = len([r for r in scored if r['priority'] == 'CRITICAL'])
    high        = len([r for r in scored if r['priority'] == 'HIGH'])
    medium      = len([r for r in scored if r['priority'] == 'MEDIUM'])
    good        = len([r for r in scored if r['priority'] == 'GOOD'])
    top5        = sorted(scored, key=lambda x: x['revenue'], reverse=True)[:5]
    fix_needed  = [r for r in scored if r['priority'] in ('CRITICAL', 'HIGH', 'MEDIUM')]
    good_list   = [r for r in scored if r['priority'] == 'GOOD']

    def bar_color(s):
        if s >= 80: return '#166534'
        if s >= 60: return '#1a56db'
        if s >= 40: return '#92400e'
        return '#b91c1c'

    def priority_badge(p):
        colors = {
            'CRITICAL': ('fef2f2', 'b91c1c', 'fca5a5'),
            'HIGH':     ('fffbeb', '92400e', 'fcd34d'),
            'MEDIUM':   ('eff6ff', '1e40af', '93c5fd'),
            'GOOD':     ('f0fdf4', '166534', '86efac'),
        }
        bg, fg, border = colors.get(p, ('f3f4f6','374151','d1d5db'))
        return f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;font-family:monospace;background:#{bg};color:#{fg};border:1px solid #{border}">{p}</span>'

    # --- HTML ---
    css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
:root{--bg:#f4f5f7;--surface:#fff;--border:#e0e4eb;--accent:#1a56db;--warn:#c47d00;--danger:#b91c1c;--success:#166534;--text:#1e2532;--dim:#6b7280;--mono:'IBM Plex Mono',monospace;--sans:'IBM Plex Sans',sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;line-height:1.6}
.page{max-width:1100px;margin:0 auto;padding:40px 24px}
.rh{margin-bottom:36px;padding-bottom:24px;border-bottom:2px solid var(--border)}
.store{font-family:var(--mono);font-size:11px;letter-spacing:3px;color:var(--accent);text-transform:uppercase;margin-bottom:8px}
.rtitle{font-size:28px;font-weight:600;margin-bottom:4px}
.rsub{color:var(--dim);font-size:14px}
.rmeta{margin-top:12px;font-size:12px;color:var(--dim);font-family:var(--mono)}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:16px;margin-bottom:36px}
.sc{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px}
.sl{font-size:11px;letter-spacing:1.5px;color:var(--dim);text-transform:uppercase;margin-bottom:8px;font-weight:500}
.sv{font-size:32px;font-weight:600;font-family:var(--mono);line-height:1}
.sv.d{color:var(--danger)}.sv.w{color:var(--warn)}.sv.s{color:var(--success)}.sv.a{color:var(--accent)}
.ss{font-size:11px;color:var(--dim);margin-top:6px}
.alert{border-radius:8px;padding:16px 20px;margin-bottom:28px;border-left:4px solid}
.alert-d{background:#fef2f2;border-color:#dc2626}
.alert-i{background:#eff6ff;border-color:#3b82f6}
.at{font-weight:600;margin-bottom:4px}
.ab{font-size:13px;color:#374151;line-height:1.6}
.sec{margin-bottom:40px}
.sec-t{font-size:13px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--dim);margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border)}
table{width:100%;border-collapse:collapse;background:var(--surface);border-radius:8px;overflow:hidden;border:1px solid var(--border);margin-bottom:12px}
th{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--dim);padding:12px 16px;text-align:left;background:#f9fafb;border-bottom:1px solid var(--border);font-weight:500}
td{padding:12px 16px;border-bottom:1px solid #f3f4f6;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#f9fafb}
.mono{font-family:var(--mono);font-size:12px}
a.il{color:var(--accent);text-decoration:none;font-family:var(--mono);font-size:12px}
a.il:hover{text-decoration:underline}
.lc{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:16px}
.lch{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;gap:16px}
.lt{font-size:15px;font-weight:500;line-height:1.4;flex:1}
.lm{display:flex;gap:20px;margin-bottom:14px;flex-wrap:wrap}
.mi{font-size:12px;color:var(--dim)}
.mi strong{color:var(--text)}
.bw{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.bn{font-family:var(--mono);font-size:14px;font-weight:600;min-width:36px}
.bb{flex:1;height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden}
.bf{height:100%;border-radius:3px}
.gi{display:flex;align-items:flex-start;gap:8px;font-size:13px;color:#92400e;margin-bottom:4px;background:#fffbeb;padding:6px 10px;border-radius:4px}
.ai{display:flex;align-items:flex-start;gap:8px;font-size:13px;color:#1e40af;margin-bottom:4px;background:#eff6ff;padding:6px 10px;border-radius:4px}
.stb{margin-top:12px;padding:12px 14px;background:#f0fdf4;border:1px solid #86efac;border-radius:6px}
.stl{font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#166534;font-weight:600;margin-bottom:4px}
.stt{font-size:13px;color:#14532d;font-weight:500}
.stc{font-size:11px;color:#166534;margin-top:2px;font-family:monospace}
.pb{background:#eff6ff;border:1px solid #93c5fd;border-radius:8px;padding:20px;margin-bottom:28px}
.pbt{font-weight:600;color:#1e40af;margin-bottom:8px;font-size:14px}
.pbb{font-size:13px;color:#1e3a8a;line-height:1.7}
.pbb li{margin-left:20px;margin-bottom:4px}
.ft{margin-top:48px;padding-top:24px;border-top:1px solid var(--border);font-size:12px;color:var(--dim);text-align:center}
@media print{body{background:white}.page{padding:20px}.lc{break-inside:avoid}}
</style>"""

    top5_rows = ''
    for r in top5:
        top5_rows += f"""
        <tr>
          <td><a class="il" href="https://www.ebay.com/itm/{r['item_id']}" target="_blank">{r['item_id']}</a><br>
              <span style="font-size:13px">{r['title'][:60]}{'...' if r['tlen']>60 else ''}</span></td>
          <td class="mono">${r['price']:.2f}</td>
          <td class="mono">{r['sold']}</td>
          <td class="mono">${r['revenue']:.2f}</td>
          <td class="mono">{r['watchers']}</td>
          <td class="mono">{r['tlen']}</td>
        </tr>"""

    fix_cards = ''
    for r in fix_needed:
        bc = bar_color(r['score'])
        gaps_html = ''.join([f'<div class="gi"><span>⚠</span>{g}</div>' for g in r['gaps']])
        acts_html = ''.join([f'<div class="ai"><span>→</span>{a}</div>' for a in r['actions']])
        sug_html = ''
        if r['title_improved']:
            slen = len(r['suggested_title'])
            sug_html = f"""
            <div class="stb">
              <div class="stl">Suggested Title</div>
              <div class="stt">{r['suggested_title']}</div>
              <div class="stc">{slen} characters</div>
            </div>"""

        fix_cards += f"""
        <div class="lc">
          <div class="lch">
            <div class="lt">{r['title']}</div>
            {priority_badge(r['priority'])}
          </div>
          <div class="lm">
            <div class="mi"><strong>Item:</strong> <a class="il" href="https://www.ebay.com/itm/{r['item_id']}" target="_blank">{r['item_id']}</a></div>
            <div class="mi"><strong>Price:</strong> ${r['price']:.2f}</div>
            <div class="mi"><strong>Sold:</strong> {r['sold']}</div>
            <div class="mi"><strong>Watchers:</strong> {r['watchers']}</div>
            <div class="mi"><strong>Title Length:</strong> {r['tlen']} chars</div>
            <div class="mi"><strong>Category:</strong> {r['category'] or 'Unknown'}</div>
          </div>
          <div class="bw">
            <span class="bn" style="color:{bc}">{r['score']}</span>
            <div class="bb"><div class="bf" style="width:{r['score']}%;background:{bc}"></div></div>
            <span style="font-size:11px;color:#6b7280">/ 100</span>
          </div>
          {gaps_html}
          {acts_html}
          {sug_html}
        </div>"""

    good_rows = ''
    for r in good_list:
        good_rows += f"""
        <tr>
          <td><a class="il" href="https://www.ebay.com/itm/{r['item_id']}" target="_blank">{r['item_id']}</a></td>
          <td style="font-size:13px">{r['title'][:65]}{'...' if r['tlen']>65 else ''}</td>
          <td>{priority_badge('GOOD')}</td>
          <td class="mono">{r['sold']}</td>
          <td class="mono">{r['watchers']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cassini Diagnostic Report</title>
{css}
</head>
<body>
<div class="page">

<div class="rh">
  <div class="store">eBay Seller Diagnostic</div>
  <div class="rtitle">Cassini Visibility Report</div>
  <div class="rsub">Prioritized action plan to recover zero-view listings and restore sales velocity</div>
  <div class="rmeta">Generated: {now} &nbsp;|&nbsp; Listings analyzed: {total} &nbsp;|&nbsp; Data source: eBay Active Listings CSV</div>
</div>

<div class="alert alert-d">
  <div class="at">⚠ Critical Finding: {zero_sold} of {total} listings have zero sales ({zero_sold*100//total if total else 0}%)</div>
  <div class="ab">This report identifies every listing that needs attention, explains why in plain English, and gives you an exact title to copy. Work through HIGH priority listings first. Do not run Promoted Listings on any listing scoring below 80.</div>
</div>

<div class="sg">
  <div class="sc"><div class="sl">Total Listings</div><div class="sv">{total}</div><div class="ss">Active in store</div></div>
  <div class="sc"><div class="sl">Zero Sales</div><div class="sv d">{zero_sold}</div><div class="ss">{zero_sold*100//total if total else 0}% of inventory stalled</div></div>
  <div class="sc"><div class="sl">Avg Cassini Score</div><div class="sv w">{avg_score}</div><div class="ss">Target: 80+ for PL campaigns</div></div>
  <div class="sc"><div class="sl">Revenue Generated</div><div class="sv a">${total_rev:.0f}</div><div class="ss">From {total - zero_sold} selling listings</div></div>
  <div class="sc"><div class="sl">Need Attention</div><div class="sv w">{high + critical + medium}</div><div class="ss">HIGH, MEDIUM or CRITICAL</div></div>
  <div class="sc"><div class="sl">Good Standing</div><div class="sv s">{good}</div><div class="ss">Scoring 80+ (PL eligible)</div></div>
</div>

<div class="pb">
  <div class="pbt">What Your Sales Data Tells Us</div>
  <div class="pbb">
    <ul>
      <li><strong>Your proven sellers:</strong> Waldemar chains, Double Albert chains — titles 70–79 chars, condition set as "New without tags"</li>
      <li><strong>What kills visibility:</strong> Short titles (under 60 chars), missing power keywords, no condition signal</li>
      <li><strong>The fix pattern:</strong> Add "New without tags" to end of title + front-load strongest keywords + verify 60–80 chars</li>
      <li><strong>Do not mass-refresh:</strong> No more than 5 Sell Similar revisions per day — mass refreshing triggers further suppression</li>
      <li><strong>New Listings vs Sell Similar:</strong> Use Sell Similar only if listing is 90+ days old with zero views</li>
    </ul>
  </div>
</div>

<div class="sec">
  <div class="sec-t">Your Top Performing Listings — Replicate These Patterns</div>
  <table>
    <thead><tr><th>Listing</th><th>Price</th><th>Sold</th><th>Revenue</th><th>Watchers</th><th>Title Length</th></tr></thead>
    <tbody>{top5_rows}</tbody>
  </table>
</div>

<div class="sec">
  <div class="sec-t">Priority Fix List — Work Through These In Order</div>
  {fix_cards}
</div>

<div class="sec">
  <div class="sec-t">Listings in Good Standing ({good} listings — score 80+)</div>
  <table>
    <thead><tr><th>Item ID</th><th>Title</th><th>Score</th><th>Sold</th><th>Watchers</th></tr></thead>
    <tbody>{good_rows}</tbody>
  </table>
</div>

<div class="ft">Cassini Diagnostic Report &nbsp;|&nbsp; For seller use only &nbsp;|&nbsp; Generated by eBay Cassini Tool</div>
</div>
</body>
</html>"""

    return html.encode('utf-8')
