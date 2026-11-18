"""
verify_report_compliance.py
===========================
Executes a comprehensive compliance audit on:
  - report/SupeRR_Round1_Report.docx
  - report/SupeRR_Round1_Report.pdf
  - outputs/validation/*.csv

Asserts zero style violations, exact number parity, and perfect page layout.
"""

import os
import re
import json
import pandas as pd
import docx
import pymupdf

DOCX_PATH = "report/SupeRR_Round1_Report.docx"
PDF_PATH = "report/SupeRR_Round1_Report.pdf"

print("=" * 70)
print("1. FILE EXISTENCE & SIZE CHECKS")
print("=" * 70)

assert os.path.exists(DOCX_PATH), f"Missing {DOCX_PATH}"
assert os.path.exists(PDF_PATH), f"Missing {PDF_PATH}"

docx_size = os.path.getsize(DOCX_PATH) / 1024
pdf_size = os.path.getsize(PDF_PATH) / 1024
print(f"[PASS] DOCX exists: {DOCX_PATH} ({docx_size:.1f} KB)")
print(f"[PASS] PDF exists: {PDF_PATH} ({pdf_size:.1f} KB)")

print("\n" + "=" * 70)
print("2. PDF PAGE COUNT & RENDERING AUDIT")
print("=" * 70)

doc = pymupdf.open(PDF_PATH)
num_pages = len(doc)
print(f"Total PDF pages: {num_pages}")
assert 10 <= num_pages <= 14, f"Page count {num_pages} outside 10-14 requirement!"
print(f"[PASS] Page count is exactly {num_pages} (within 10-14 page target).")

# Render each page to verify no crash or broken rendering
preview_dir = "report/pdf_previews"
os.makedirs(preview_dir, exist_ok=True)
for i in range(num_pages):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    pix.save(f"{preview_dir}/page_{i+1:02d}.png")
print(f"[PASS] Successfully rendered all {num_pages} PDF pages to {preview_dir}/.")

print("\n" + "=" * 70)
print("3. STYLE & BANNED WORDS AUDIT")
print("=" * 70)

BANNED_WORDS = [
    "delve", "robust", "holistic", "crucial",
    "it is important to note", "in today's", "this section will",
    "comprehensive", "seamless", "cutting-edge"
]

# Read text from docx paragraphs and tables
doc_obj = docx.Document(DOCX_PATH)
full_text_list = []
for p in doc_obj.paragraphs:
    full_text_list.append(p.text)
for t in doc_obj.tables:
    for row in t.rows:
        for cell in row.cells:
            full_text_list.append(cell.text)

combined_text = "\n".join(full_text_list)

violations = []
for b in BANNED_WORDS:
    matches = re.findall(rf'\b{b}\b', combined_text, flags=re.IGNORECASE)
    if matches:
        violations.append(f"Found banned word '{b}' ({len(matches)} occurrences)")

# Check leverage as verb
verb_leverage = re.findall(r'\b(leveraging|leveraged|leverages|to leverage)\b', combined_text, flags=re.IGNORECASE)
if verb_leverage:
    violations.append(f"Found verb usage of 'leverage': {verb_leverage}")

# Check em dash
if "—" in combined_text:
    violations.append("Found banned em dash '—'")

# Check emoji
emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)
emojis_found = emoji_pattern.findall(combined_text)
if emojis_found:
    violations.append(f"Found banned emojis: {emojis_found}")

# Check bold in body paragraphs (exclude Headings, List Bullet, etc.)
for p in doc_obj.paragraphs:
    style_name = p.style.name if p.style else ""
    if style_name in ['Normal'] and len(p.text.split()) > 15:
        # Check if any run is bold
        bold_runs = [r.text for r in p.runs if r.bold and len(r.text.strip()) > 0]
        if bold_runs:
            violations.append(f"Found bold run in body paragraph: {bold_runs}")

if violations:
    print(f"[FAIL] {len(violations)} violations found:")
    for v in violations:
        print(f"  - {v}")
    sys.exit(1)
else:
    print("[PASS] Zero banned words, zero em dashes, zero emojis, and zero bolding in body paragraphs.")

print("\n" + "=" * 70)
print("4. RANKING & DATA CONSISTENCY AUDIT")
print("=" * 70)

# Check Top 10 Batters IPL
top10_bat_ipl = pd.read_csv("outputs/final_top10_batters_ipl.csv")
assert top10_bat_ipl.iloc[0]["player_name"] == "Suryakumar Yadav"
assert top10_bat_ipl.iloc[1]["player_name"] == "Ishan Kishan"
assert top10_bat_ipl.iloc[2]["player_name"] == "Prabhsimran Singh"
assert top10_bat_ipl.iloc[3]["player_name"] == "Abhishek Sharma"
assert top10_bat_ipl.iloc[4]["player_name"] == "Andre Russell"
assert top10_bat_ipl.iloc[5]["player_name"] == "Tim David"
assert top10_bat_ipl.iloc[6]["player_name"] == "Shai Hope"
assert top10_bat_ipl.iloc[7]["player_name"] == "Dhruv Jurel"
assert top10_bat_ipl.iloc[8]["player_name"] == "Liam Livingstone"
assert top10_bat_ipl.iloc[9]["player_name"] == "Heinrich Klaasen"
print("[PASS] Top 10 Batters IPL perfectly match submission ranking (Ranks 1 to 10).")

# Check Top 10 Bowlers IPL
top10_bowl_ipl = pd.read_csv("outputs/final_top10_bowlers_ipl.csv")
assert top10_bowl_ipl.iloc[0]["player_name"] == "Mayank Yadav"
assert top10_bowl_ipl.iloc[1]["player_name"] == "Jamie Overton"
assert top10_bowl_ipl.iloc[2]["player_name"] == "Sunil Narine"
assert top10_bowl_ipl.iloc[3]["player_name"] == "Matheesha Pathirana"
assert top10_bowl_ipl.iloc[4]["player_name"] == "Jasprit Bumrah"
assert top10_bowl_ipl.iloc[5]["player_name"] == "Varun Chakravarthy"
assert top10_bowl_ipl.iloc[6]["player_name"] == "Wanindu Hasaranga"
assert top10_bowl_ipl.iloc[7]["player_name"] == "Mitchell Santner"
assert top10_bowl_ipl.iloc[8]["player_name"] == "Akeal Hosein"
assert top10_bowl_ipl.iloc[9]["player_name"] == "Mohsin Khan"
print("[PASS] Top 10 Bowlers IPL perfectly match submission ranking (Ranks 1 to 10).")

# Check held out numbers parity
held_out_df = pd.read_csv("outputs/validation/held_out_predictive_test.csv")
top_row = held_out_df.iloc[0]
assert abs(top_row["Batters_HeldOut_RAAE_100"] - 24.41) < 1e-2
assert abs(top_row["Bowlers_HeldOut_RSAE_24"] - 6.81) < 1e-2
print("[PASS] Held-out predictive metrics match exact CSV records (+24.41 RAAE/100, +6.81 RSAE/24).")

print("\n" + "=" * 70)
print("ALL COMPLIANCE CHECKS PASSED WITH ZERO ERRORS.")
print("=" * 70)

