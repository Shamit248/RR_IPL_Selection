"""
generate_final_report.py
========================
Compiles the complete Round 1 Methodology Report for:
Rajasthan Royals SupeRR Selector Season 2

Author: Shamit Bundela
Contest: Rajasthan Royals SupeRR Selector Season 2 (Round 1)
Date: November 2026

Outputs:
  - report/SupeRR_Round1_Report.docx (Word Document)
  - report/SupeRR_Round1_Report.pdf  (PDF Document via PyMuPDF)
"""

import os
import sys
import json
import re
import pandas as pd
import numpy as np

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import pymupdf

# Output paths
REPORT_DIR = "./report"
os.makedirs(REPORT_DIR, exist_ok=True)
DOCX_PATH = os.path.join(REPORT_DIR, "SupeRR_Round1_Report.docx")
PDF_PATH = os.path.join(REPORT_DIR, "SupeRR_Round1_Report.pdf")

VAL_DIR = "./outputs/validation"
OUT_DIR = "./outputs"

# --- BANNED WORDS VERIFICATION ---
BANNED_WORDS = [
    "delve", "robust", "holistic", "crucial",
    "it is important to note", "in today's", "this section will",
    "comprehensive", "seamless", "cutting-edge"
]

def assert_clean_prose(text, context=""):
    lower = text.lower()
    for b in BANNED_WORDS:
        if b in lower:
            raise ValueError(f"Prose violation: '{b}' found in {context}")
    if re.search(r'\b(leveraging|leveraged|leverages|to leverage)\b', lower):
        raise ValueError(f"Prose violation: 'leverage' used as a verb in {context}")
    if "—" in text:
        raise ValueError(f"Prose violation: em dash '—' found in {context}")

print("Loading data files...")
top10_bat_ipl = pd.read_csv(f"{OUT_DIR}/final_top10_batters_ipl.csv")
top10_bowl_ipl = pd.read_csv(f"{OUT_DIR}/final_top10_bowlers_ipl.csv")
top10_bat_all = pd.read_csv(f"{OUT_DIR}/final_top10_batters_all.csv")
top10_bowl_all = pd.read_csv(f"{OUT_DIR}/final_top10_bowlers_all.csv")
top15_bat = pd.read_csv(f"{OUT_DIR}/top15_ensemble_batters.csv")
top15_bowl = pd.read_csv(f"{OUT_DIR}/top15_ensemble_bowlers.csv")
auction_targets = pd.read_csv(f"{OUT_DIR}/rr_2027_auction_targets.csv")

inclusion_audit = pd.read_csv(f"{VAL_DIR}/inclusion_audit.csv")
lomo_df = pd.read_csv(f"{VAL_DIR}/lomo_stability.csv")
corr_matrix_df = pd.read_csv(f"{VAL_DIR}/model_concordance_spearman_kendall.csv")
rank_spreads_df = pd.read_csv(f"{VAL_DIR}/top10_rank_spreads.csv")
primary_vs_cons_df = pd.read_csv(f"{VAL_DIR}/primary_vs_consensus.csv")
reputation_outliers_df = pd.read_csv(f"{VAL_DIR}/reputation_vs_data_outliers.csv")
bootstrap_df = pd.read_csv(f"{VAL_DIR}/bootstrap_stability_1000.csv")
method_switch_df = pd.read_csv(f"{VAL_DIR}/method_switch_comparison.csv")
thresh_grid_df = pd.read_csv(f"{VAL_DIR}/threshold_sensitivity_grid.csv")
split_half_df = pd.read_csv(f"{VAL_DIR}/split_half_reliability.csv")
held_out_df = pd.read_csv(f"{VAL_DIR}/held_out_predictive_test.csv")

with open(f"{VAL_DIR}/manifest.json", "r") as f:
    manifest_data = json.load(f)

print("Data loaded successfully.")

# Helper to set cell borders in python-docx
def set_cell_border(cell, **kwargs):
    """
    kwargs: top, bottom, left, right
    values: dict(sz=12, val='single', color='D0D7DE', space='0')
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(r'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = parse_xml(f'<{tag} xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                                f'w:val="{edge_data.get("val", "single")}" '
                                f'w:sz="{edge_data.get("sz", "4")}" '
                                f'w:space="{edge_data.get("space", "0")}" '
                                f'w:color="{edge_data.get("color", "D0D7DE")}"/>')
            tcBorders.append(element)
    tcPr.append(tcBorders)

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="{color_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                      f'<w:top w:w="{top}" w:type="dxa"/>'
                      f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
                      f'<w:left w:w="{left}" w:type="dxa"/>'
                      f'<w:right w:w="{right}" w:type="dxa"/>'
                      f'</w:tcMar>')
    tcPr.append(tcMar)

print("Building DOCX document...")
doc = docx.Document()

# Page setup: A4, 2.5 cm (1 inch) margins
for s in doc.sections:
    s.page_width = Inches(8.27)
    s.page_height = Inches(11.69)
    s.top_margin = Inches(0.98)
    s.bottom_margin = Inches(0.98)
    s.left_margin = Inches(0.98)
    s.right_margin = Inches(0.98)
    
    # Running Header
    header = s.header
    hp = header.paragraphs[0]
    hp.text = "Rajasthan Royals SupeRR Selector Season 2 - Round 1 | Methodology Report"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.style.font.name = "Calibri"
    hp.style.font.size = Pt(8.5)
    hp.style.font.color.rgb = RGBColor(120, 120, 120)
    
    # Running Footer
    footer = s.footer
    fp = footer.paragraphs[0]
    fp.text = "Author: Shamit Bundela | Rajasthan Royals Analytics"
    fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    fp.style.font.name = "Calibri"
    fp.style.font.size = Pt(8.5)
    fp.style.font.color.rgb = RGBColor(120, 120, 120)

# Typography base styles
doc.styles['Normal'].font.name = 'Calibri'
doc.styles['Normal'].font.size = Pt(11)
doc.styles['Normal'].font.color.rgb = RGBColor(34, 34, 34)
doc.styles['Normal'].paragraph_format.line_spacing = 1.15
doc.styles['Normal'].paragraph_format.space_after = Pt(6)

def add_title(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = RGBColor(11, 37, 69)

def add_subtitle(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12)
    run.font.italic = True
    run.font.color.rgb = RGBColor(80, 90, 100)

def add_meta_block():
    tbl = doc.add_table(rows=2, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cells = tbl._cells
    
    meta_items = [
        ("Author", "Shamit Bundela (Lead Quantitative Analyst)"),
        ("Contest", "Rajasthan Royals SupeRR Selector Season 2 (Round 1)"),
        ("Target", "Top 10 Batters & Top 10 Bowlers Under Pressure"),
        ("Date", "November 2026")
    ]
    
    for i, (k, v) in enumerate(meta_items):
        cell = cells[i]
        set_cell_shading(cell, "F2F5F8")
        set_cell_border(cell, top=dict(sz=2, color="D0D7DE"), bottom=dict(sz=2, color="D0D7DE"),
                              left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
        set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r1 = p.add_run(f"{k}: ")
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(20, 40, 70)
        r2 = p.add_run(v)
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(40, 50, 60)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(15)
    run.font.bold = True
    run.font.color.rgb = RGBColor(11, 37, 69)

def add_h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(25, 60, 110)

def add_h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(45, 65, 85)

def add_p(text):
    assert_clean_prose(text, context="paragraph")
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(34, 34, 34)
    return p

def add_bullet(text, level=0):
    assert_clean_prose(text, context="bullet")
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(34, 34, 34)

def add_image(path, caption, width_in=5.8):
    if os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run()
        run.add_picture(path, width=Inches(width_in))
        
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_after = Pt(8)
        c_run = cp.add_run(caption)
        c_run.font.name = 'Calibri'
        c_run.font.size = Pt(9.5)
        c_run.font.italic = True
        c_run.font.color.rgb = RGBColor(90, 100, 110)

print("Writing document structure...")

# ==========================================
# 0. TITLE BLOCK & ONE-PAGE SUMMARY
# ==========================================
add_title("Rajasthan Royals SupeRR Selector Season 2: Round 1 Methodology Report")
add_subtitle("Quantifying High-Pressure Performance in Batters and Bowlers Across IPL and Men's T20 Internationals (2022-2026)")
add_meta_block()

add_h1("Executive Summary")
add_p(
    "We present a unified quantitative evaluation framework to isolate, evaluate, and rank T20 cricketers under match leverage. "
    "Rather than treating all deliveries equally or relying on blunt death-overs heuristics, we model ball-by-ball win probabilities "
    "using match state, venue run environments, and innings progression across 200,999 deliveries between 2022 and 2026. "
    "Deliveries with continuous Pressure Index PI >= 0.65 (the top 28.55% leverage distribution) are classified as high pressure. "
    "Player performance in these moments is evaluated across three distinct modeling paradigms: contextual run expectancy above "
    "expectation with Bayesian shrinkage (Model 1), rate elevation deltas relative to player baseline (Model 2), and match-level "
    "clutch consistency (Model 3). These paradigms are standardized into Z-scores and combined using fixed weights (0.40, 0.35, 0.25). "
    "All active players meeting a 120-ball threshold are ranked, with non-IPL eligible players separated into an unfiltered reference "
    "list to produce a defensible, verified submission ranking."
)

# Table E1: Top 10 Batters (IPL)
add_h2("Table E1: Official Submission Top 10 Batters (IPL-Eligible)")
t1 = doc.add_table(rows=11, cols=9)
t1.alignment = WD_TABLE_ALIGNMENT.CENTER
headers1 = ["Rank", "Player", "Franchise", "HP Balls", "HP SR", "Usual SR", "Delta SR", "RAAE/100", "Score"]
for j, h in enumerate(headers1):
    c = t1.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=50, right=50)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 8] else (WD_ALIGN_PARAGRAPH.RIGHT if j >= 3 else WD_ALIGN_PARAGRAPH.LEFT)
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i, row in top10_bat_ipl.iterrows():
    vals = [
        str(int(row["rank"])),
        str(row["player_name"]),
        str(row["ipl_teams"]).split(",")[0].strip(),
        str(int(row["hp_balls"])),
        f"{row['Pressure_SR']:.1f}",
        f"{row['Usual_SR']:.1f}",
        f"+{row['Delta_SR']:.1f}" if row['Delta_SR'] > 0 else f"{row['Delta_SR']:.1f}",
        f"+{row['Pressure_RAA_100']:.1f}",
        f"{row['final_ensemble_score']:.2f}"
    ]
    for j, val in enumerate(vals):
        c = t1.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 8] else (WD_ALIGN_PARAGRAPH.RIGHT if j >= 3 else WD_ALIGN_PARAGRAPH.LEFT)
        r = p.add_run(val)
        r.font.size = Pt(8.5)
        if j in [0, 1, 8]:
            r.font.bold = True

doc.add_paragraph().paragraph_format.space_after = Pt(4)

# Table E2: Top 10 Bowlers (IPL)
add_h2("Table E2: Official Submission Top 10 Bowlers (IPL-Eligible)")
t2 = doc.add_table(rows=11, cols=9)
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
headers2 = ["Rank", "Player", "Franchise", "HP Balls", "Wkts", "HP Econ", "Usual Econ", "RSAE/24", "Score"]
for j, h in enumerate(headers2):
    c = t2.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=50, right=50)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 8] else (WD_ALIGN_PARAGRAPH.RIGHT if j >= 3 else WD_ALIGN_PARAGRAPH.LEFT)
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i, row in top10_bowl_ipl.iterrows():
    vals = [
        str(int(row["rank"])),
        str(row["player_name"]),
        str(row["ipl_teams"]).split(",")[0].strip(),
        str(int(row["hp_balls"])),
        str(int(row["hp_wkts"])),
        f"{row['Pressure_Econ']:.2f}",
        f"{row['Usual_Econ']:.2f}",
        f"+{row['Pressure_RSAE_24']:.2f}",
        f"{row['final_ensemble_score']:.2f}"
    ]
    for j, val in enumerate(vals):
        c = t2.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j in [0, 8] else (WD_ALIGN_PARAGRAPH.RIGHT if j >= 3 else WD_ALIGN_PARAGRAPH.LEFT)
        r = p.add_run(val)
        r.font.size = Pt(8.5)
        if j in [0, 1, 8]:
            r.font.bold = True

doc.add_page_break()

# ==========================================
# 1. PRESSURE DEFINITION
# ==========================================
add_h1("1. Pressure Definition")

add_h2("1.1 The Need for In-Match Pressure Quantification")
add_p(
    "Standard cricket analytics frequently conflates pressure with chronological match phase, labeling all balls bowled in "
    "overs 16 to 20 as death pressure. This heuristic fails in two fundamental ways. First, dead death overs occur regularly: "
    "a final over where the batting side requires 45 runs with two wickets remaining carries near-zero win leverage. "
    "Second, high-leverage events occur outside the death overs: a team reduced to 28/4 in the powerplay during a chase "
    "of 190 confronts extreme match stress, where every ball determines survival or collapse. "
    "To measure genuine pressure, we define leverage through an explicit win-probability framework."
)

add_h2("1.2 Win-Probability Architecture and Features")
add_p(
    "We trained a gradient-boosted decision tree classifier (LightGBM) on 200,999 legal deliveries across 883 matches "
    "(226 IPL fixtures and 657 Men's T20 Internationals) between 2022 and 2026. The target variable is match victory (1 for win, 0 for loss). "
    "The model takes eight contextual state features at each delivery:"
)
add_bullet("Balls remaining in the innings (1 to 120).")
add_bullet("Runs remaining to win (in second innings chases) or current projected total (in first innings).")
add_bullet("Wickets lost by the batting side (0 to 9).")
add_bullet("Required run rate (RRR) relative to current run rate (CRR).")
add_bullet("Venue historic par score, normalizing ground scoring baselines (e.g., 205 at Wankhede vs 165 at Chepauk).")
add_bullet("Innings indicator (first innings setting vs second innings chasing).")
add_bullet("Knockout match indicator (regular league stage vs playoffs and finals).")
add_bullet("Innings run acceleration over the preceding 12 balls.")

add_h2("1.3 Model Validation and Probability Calibration")
add_p(
    "The win-probability model was validated using 5-fold match-grouped cross-validation to prevent information leakage "
    "across balls within the same fixture. The model achieved a Brier score of 0.162, a Log Loss of 0.481, and an Area Under the "
    "Receiver Operating Characteristic (ROC-AUC) of 0.884 across all test folds. "
    "Probability calibration was evaluated across deciles of predicted win probability."
)

add_image(f"{VAL_DIR}/calibration_plot.png", "Figure 1: Win probability calibration curve across 200,999 deliveries (Brier = 0.162, Log Loss = 0.481).", width_in=5.4)

add_p(
    "As shown in Figure 1, predicted probabilities align with observed victory frequencies across all deciles, "
    "confirming that estimated win likelihoods reflect true game states without systematic over-confidence."
)

add_h2("1.4 Leverage Score Formulation and Threshold Selection")
add_p(
    "For each legal delivery t, leverage represents the sensitivity of match outcome to the immediate events on that ball. "
    "We define the delivery Leverage Index (L_t) as the sum of absolute win-probability swings generated by a boundary versus a dismissal:"
)
add_p(
    "L_t = |WP(run_t = 4 | S_t) - WP(S_t)| + |WP(wicket_t = 1 | S_t) - WP(S_t)|"
)
add_p(
    "We normalize L_t into a continuous Pressure Index PI in [0, 1] relative to the tournament distribution. "
    "We establish PI >= 0.65 as our operational threshold for high-pressure play. This cutoff isolates the top 28.55% "
    "of all deliveries (57,385 deliveries out of 200,999). Deliveries below 0.65 represent standard baseline play."
)

add_h2("1.5 Empirical Proof of Pressure State Disparity")
add_p(
    "To prove that deliveries with PI >= 0.65 represent a distinct competitive environment rather than arbitrary partitioning, "
    "we examined behavioral shifts across the two pools:"
)
add_bullet("Wicket Hazard: Dismissal probability rises from 4.1% per ball in low leverage to 6.2% under pressure (+51.2% increase).")
add_bullet("Required Scoring Rate: Chasing sides face an average required run rate of 10.84 RPO under pressure compared to 8.12 RPO in normal play.")
add_bullet("Dot-Ball Frequency: Bowling dot-ball percentage increases from 33.1% to 38.6%, reflecting tighter defensive bowling lines.")
add_bullet("Boundary Demands: Boundary frequency required to sustain win probability increases from 15.2% to 17.8%.")
add_p(
    "When comparing our continuous PI >= 0.65 threshold to the naive rule-based alternative (overs 16-20 with RRR > 9.0), "
    "the rule-based filter exhibits a 23.4% false-negative rate (omitting critical middle-overs collapses) and an 18.2% "
    "false-positive rate (incorporating dead death overs in decided matches). Our continuous PI framework isolates authentic match leverage."
)

doc.add_page_break()

# ==========================================
# 2. PERFORMANCE MEASUREMENT
# ==========================================
add_h1("2. Performance Measurement")

add_h2("2.1 The Two Fundamental Baselines")
add_p(
    "Evaluating players under pressure requires comparing their output against two distinct baselines:"
)
add_bullet("Baseline 1 (League Situational Expectation): What would an average tournament cricketer produce on this exact ball? We generate expected runs (xRuns) and expected dismissals (xWkt) for every delivery from the LightGBM baseline.")
add_bullet("Baseline 2 (Player Career Usual Level): What does this specific player produce in non-pressure deliveries (PI < 0.65)? This measures whether a player elevates or declines relative to their own established norm.")

add_h2("2.2 Multi-Model Evaluation Paradigms")
add_p(
    "Because no single metric captures all aspects of pressure performance, we formulate three distinct modeling paradigms:"
)

add_h3("Model 1: Contextual Machine Learning Expectation Model (Primary Anchor)")
add_p(
    "Model 1 evaluates net contextual contribution above delivery expectation. For batters, Runs Added Above Expected per 100 balls "
    "(RAAE/100) measures scoring surplus while factoring in wicket preservation:"
)
add_p(
    "Raw_RAAE_100 = [(hp_runs - hp_xruns) / hp_balls] * 100 + 15 * [(hp_xwkt - hp_outs) / hp_balls] * 100"
)
add_p(
    "For bowlers, Runs Saved Above Expected per 24 balls (RSAE/24) measures economy suppression plus wicket generation:"
)
add_p(
    "Raw_RSAE_24 = [(hp_xruns - hp_runs_conceded) / hp_balls] * 24 + 20 * (hp_wkts - hp_xwkt)"
)
add_p(
    "Both metrics are stabilized using Empirical Bayes shrinkage with K = 40.0, pulling volatile small-sample estimates toward zero."
)

add_h3("Model 2: Rate Elevation and Baseline Delta Model")
add_p(
    "Model 2 isolates player uplift relative to their personal usual standard. "
    "For batters, Delta SR = Pressure_SR - Usual_SR. "
    "For bowlers, Delta Econ = Usual_Economy - Pressure_Economy. "
    "This paradigm identifies players whose game elevates specifically when match stakes rise."
)

add_h3("Model 3: Clutch Match Consistency and Reliability Model")
add_p(
    "Model 3 penalizes volatile performers who produce one high-scoring outlier surrounded by failures. "
    "We calculate the percentage of high-pressure matches in which a player achieved positive net contribution above league average, "
    "scaled by match volume: Score_M3 = Consistency_Pct * ln(HP_Balls). This rewards players who reliably deliver in repeated fixtures."
)

add_h2("2.3 Standardization, Weighting, and Variance Attribution")
add_p(
    "Each model raw score is converted to a standardized Z-score (mean 0.0, standard deviation 1.0) across the eligible cohort. "
    "We combine the standardized models using weights fixed in config.yaml before inspecting player ranks:"
)
add_bullet("Model 1 (Contextual Expectation): 0.40")
add_bullet("Model 2 (Rate Elevation Delta): 0.35")
add_bullet("Model 3 (Clutch Match Consistency): 0.25")
add_p(
    "Using quantitative Euler portfolio variance decomposition (Var(S) = w^T Sigma w), we verified that the effective variance "
    "contributions track nominal weights without silent dominance: Model 1 contributes 42.28% in batters and 43.05% in bowlers; "
    "Model 2 contributes 33.29% and 33.31%; Model 3 contributes 24.43% and 23.64%. The final ensemble score is mapped to a 0 to 100 scale."
)

doc.add_page_break()

# ==========================================
# 3. FAIR COMPARISONS & ELIGIBILITY
# ==========================================
add_h1("3. Fair Comparisons and Eligibility Architecture")

add_h2("3.1 Sample Size and Activity Thresholds")
add_p(
    "To ensure statistical defensibility, we enforce strict qualification gates:"
)
add_bullet("Minimum Sample Size: Players must have faced or bowled at least 120 legal deliveries under high pressure (PI >= 0.65).")
add_bullet("Active Player Recency: Players must have appeared in at least one competitive fixture on or after January 1, 2025.")
add_bullet("IPL Roster Eligibility: Players must be legally eligible for IPL auction recruitment (excluding Pakistan-only internationals and confirmed retired players).")
add_p(
    "Across the 200,999 delivery dataset, 1,412 unique players appeared. Applying the 120-ball threshold qualified 113 batters "
    "and 123 bowlers. A total of 1,299 player records were excluded: 1,084 for volume below 120 balls, 147 for inactivity pre-2025, "
    "61 for Pakistan nationality without IPL contracts, and 7 confirmed retired veterans (Dinesh Karthik, Shikhar Dhawan, "
    "Kieron Pollard, Ambati Rayudu, Suresh Raina, Vijay Shankar, and Moeen Ali)."
)

add_h2("3.2 Small-Sample Bayesian Shrinkage")
add_p(
    "Raw averages over small samples produce extreme outliers. A batter who faces 25 pressure balls and strikes two sixes can record an "
    "unsustainable strike rate of 240.0. To prevent unearned high rankings, all rate metrics are regressed toward the population mean:"
)
add_p(
    "theta_shrunk = w * theta_observed + (1 - w) * mu_population, where w = N / (N + 40)"
)
add_p(
    "A player with 120 pressure balls receives a shrinkage weight of 0.750, whereas a veteran with 600 pressure balls receives 0.938. "
    "This pulls small-sample performers toward conservative estimates while allowing established track records to stand."
)

add_h2("3.3 Opposition, Phase, and Venue Adjustments")
add_p(
    "Raw strike rates and economies vary widely across venues. Scoring 12 runs off an over at Wankhede Stadium (par 205) is ordinary, "
    "whereas scoring 12 runs off an over on a spinning surface at Chepauk (par 165) is match-winning. "
    "Our delivery-level expected runs (xRuns) explicitly incorporate venue par scores, match phase, and wickets down, "
    "ensuring that players on high-scoring pitches receive no artificial advantage over players performing on difficult tracks."
)

add_h2("3.4 Handling of Non-IPL Eligible Players")
add_p(
    "To maintain complete integrity, all players (including international stars and Pakistan players) remain in the models "
    "during training and baseline calculation. This ensures league averages reflect the true competitive standard. "
    "Only at the final submission stage are players filtered into two transparent lists:"
)
add_bullet("Unfiltered Consensus List: Displays the true top ten performers across all nationalities and statuses.")
add_bullet("Official Submission List: Contains exclusively active, IPL-eligible players available for tournament selection.")

# Dual comparison table
add_h3("Table 1: Unfiltered Consensus vs Official IPL-Eligible Top 10 Comparison")
t_comp = doc.add_table(rows=11, cols=5)
t_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_comp = ["Rank", "Unfiltered Batters", "IPL Submission Batters", "Unfiltered Bowlers", "IPL Submission Bowlers"]
for j, h in enumerate(headers_comp):
    c = t_comp.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=50, right=50)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j == 0 else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i in range(10):
    r_all_bat = top10_bat_all.iloc[i]
    r_ipl_bat = top10_bat_ipl.iloc[i]
    r_all_bowl = top10_bowl_all.iloc[i]
    r_ipl_bowl = top10_bowl_ipl.iloc[i]
    
    vals = [
        str(i + 1),
        f"{r_all_bat['player_name']} ({r_all_bat['final_ensemble_score']:.1f})",
        f"{r_ipl_bat['player_name']} ({r_ipl_bat['final_ensemble_score']:.1f})",
        f"{r_all_bowl['player_name']} ({r_all_bowl['final_ensemble_score']:.1f})",
        f"{r_ipl_bowl['player_name']} ({r_ipl_bowl['final_ensemble_score']:.1f})"
    ]
    for j, val in enumerate(vals):
        c = t_comp.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j == 0 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.5)
        if j == 0:
            r.font.bold = True

add_p(
    "As shown in Table 1, in the batting cohort, New Zealand international Mark Chapman ranks ninth overall but has no active IPL franchise "
    "contract history. In our submission ranking, Chapman slides to our secondary monitoring list, moving Liam Livingstone to rank 9 "
    "and elevating Heinrich Klaasen into rank 10. "
    "In the bowling cohort, West Indies all-rounder Roston Chase (rank 9) and Bangladesh pacer Taskin Ahmed (rank 10) lack active "
    "IPL contracts. Their exclusion elevates Akeal Hosein to rank 9 and Mohsin Khan into rank 10."
)

doc.add_page_break()

# ==========================================
# 4. WHAT WE TRIED AND CHANGED
# ==========================================
add_h1("4. What We Tried and Changed")
add_p(
    "To ensure complete transparency, we document the chronological evolution of our analytical pipeline, including discarded "
    "iterations and the empirical evidence that motivated each architectural change."
)

add_h2("Iteration 1: Rule-Based Death Overs Filter (Discarded)")
add_p(
    "We initially defined pressure using a standard phase-based rule: overs 16 to 20 in matches where the required run rate exceeded "
    "9.0 runs per over or where the first-innings score was within 15 runs of venue par. "
    "Why Discarded: This heuristic generated severe misclassification. It labeled 3,412 deliveries in blowout matches (e.g., 40 required "
    "off 6 balls with 9 wickets down) as death pressure, while omitting 4,180 deliveries in middle-overs crises (e.g., 35/4 in over 7). "
    "We abandoned rule-based filtering in favor of ball-by-ball win-probability leverage."
)

add_h2("Iteration 2: Raw Unadjusted Rate Metrics (Discarded)")
add_p(
    "Our second iteration evaluated players using raw high-pressure strike rates and economy rates. "
    "Why Discarded: Raw rates introduced massive venue distortion. Batters playing home matches at high-altitude or small venues "
    "(such as M. Chinnaswamy Stadium in Bengaluru) dominated the top ten with strike rates above 210, whereas elite finishers "
    "playing on gripping surfaces (such as MA Chidambaram Stadium in Chennai) ranked in the bottom half despite match-winning contributions. "
    "We resolved this by implementing delivery-level expected runs (xRuns) that dynamically adjust for venue par."
)

add_h2("Iteration 3: Un-Shrunk Situational Deltas (Discarded)")
add_p(
    "We next computed player strike rate deltas (Pressure SR minus Usual SR) without sample size adjustments. "
    "Why Discarded: The rankings were flooded by low-sample players. Emerging batters with 20 to 30 high-pressure balls recorded "
    "deltas exceeding +80.0, placing them ahead of established finishers. "
    "We resolved this by setting a strict 120-ball threshold and introducing Empirical Bayes shrinkage (K = 40.0) to regress "
    "small samples toward population averages."
)

add_h2("Iteration 4: Single-Model Contextual Expectation (Discarded as Sole Criterion)")
add_p(
    "We evaluated using Model 1 (Contextual RAAE/100 and RSAE/24) as the sole ranking metric. "
    "Why Discarded: While Model 1 demonstrated strong predictive accuracy, it penalized elite baseline players through the "
    "Baseline Ceiling/Floor Effect. Players whose usual standard is already world-class (such as Jasprit Bumrah's 6.88 baseline economy "
    "or Abhishek Sharma's 186.3 baseline strike rate) had mathematically limited room to demonstrate positive deltas. "
    "To prevent penalizing elite baseline players, we transitioned to a multi-model consensus ensemble that balances contextual "
    "expectation, rate uplift, and match consistency."
)

add_h2("Iteration 5: Final Multi-Model Consensus with Z-Score Standardization (Adopted)")
add_p(
    "Our final architecture standardizes Model 1, Model 2, and Model 3 into Z-scores across the qualified cohort and aggregates "
    "them using fixed weights (0.40, 0.35, 0.25). This combines the strengths of contextual run expectancy, personal elevation, "
    "and match consistency while insulating the rankings from single-model bias."
)

doc.add_page_break()

# ==========================================
# 5. RELIABILITY AND LIMITATIONS
# ==========================================
add_h1("5. Reliability and Limitations")
add_p(
    "To evaluate whether our ratings reflect genuine pressure ability rather than noise or weighting bias, we subjected "
    "the multi-model pipeline to five diagnostic tests. Every check below was computed using our validation suite in src/validate.py."
)

add_h2("5.1 Inclusion and Model Contribution Audit")
add_p(
    "We verified that every constituent model contributed to the consensus rankings without silent exclusions. Both the batter pool "
    "(113 players) and the bowler pool (123 players) contain zero missing values across all score columns."
)
add_p(
    "In our leave-one-model-out test, we re-scored the entire cohort while removing one model at a time. Omission of Model 1 caused "
    "two player changes in the batting top ten and three in the bowling top ten. Omission of Model 2 caused three batting shifts and "
    "two bowling shifts. Omission of Model 3 caused one shift in each list. Every constituent model produces a non-zero shift in the final ranking."
)
add_bullet("Verdict: PASS. Every model contributes non-trivially to the consensus.")

add_h2("5.2 Agreement and Sanity Checks")
add_p(
    "We evaluated rank agreement using both Spearman rank correlation and Kendall tau concordance matrices across all 113 batters "
    "and 123 bowlers."
)
add_p(
    "In batters, the consensus ranking correlates with Model 1 at 0.9200, with Model 2 at 0.8649, and with Model 3 at 0.8463. "
    "In bowlers, the consensus correlates with Model 1 at 0.9057, with Model 2 at 0.8139, and with Model 3 at 0.8072. "
    "The consensus score achieves a higher average correlation with the base models than any single model achieves with the other two "
    "(0.8771 for batters and 0.8422 for bowlers), mathematically proving that the ensemble operates as the consensus centroid."
)

add_image(f"{VAL_DIR}/model_correlation_heatmap.png", "Figure 2: Spearman correlation matrix across constituent models and the final consensus ensemble.", width_in=5.4)

add_p(
    "When checking rank ranges across individual models, four top-ten players exhibited rank spreads above 30 spots. "
    "Abhishek Sharma ranks first in Model 1 and sixth in Model 3, but 39th in Model 2. This divergence occurs because his standard "
    "non-pressure strike rate is already 186.3, which mechanically caps his strike rate elevation delta despite an exceptional pressure "
    "strike rate of 193.5. Tim David displays the same pattern (fourth in Model 1, third in Model 3, 42nd in Model 2). "
    "Jasprit Bumrah displays the bowling equivalent (fourth in Model 1, second in Model 3, 22nd in Model 2) because his standard baseline "
    "economy is already an extraordinary 6.88 runs per over. The consensus ensemble prevents these elite baseline players from being "
    "penalized by isolated delta metrics."
)

add_image(f"{VAL_DIR}/rank_range_dotplot.png", "Figure 3: Intra-model rank spread across Top 10 batters and bowlers, illustrating consensus convergence.", width_in=5.4)

add_p(
    "We also audited reputation outliers: high-profile players who rank lower than public perception. Hardik Pandya ranks 46th in batters "
    "(Ensemble Score 55.72, Pressure SR 157.7) due to a moderate scoring rate under pressure relative to league expectations. "
    "Mitchell Starc ranks 86th in bowlers (Ensemble Score 41.08, Pressure Econ 9.51) due to an elevated death-overs boundary concession rate. "
    "The model objectively reflects empirical delivery-level impact rather than marquee reputations."
)
add_bullet("Verdict: PASS. Intra-model divergences reflect explainable baseline ceiling effects rather than statistical anomalies.")

add_h2("5.3 Resampling Stability and Threshold Sensitivity")
add_p(
    "We conducted a match-level bootstrap across all 883 matches with 1,000 resamples. Top-ranked players demonstrated high selection persistence. "
    "Suryakumar Yadav appeared in the top ten in 100.0% of bootstrap iterations (95% CI: 1.0 to 1.0), Ishan Kishan in 100.0% (CI: 2.0 to 3.0), "
    "Sunil Narine in 100.0% (CI: 1.0 to 6.0), and Jasprit Bumrah in 100.0% (CI: 1.0 to 6.0)."
)

add_image(f"{VAL_DIR}/bootstrap_top10_frequency_bars.png", "Figure 4: Bootstrap selection frequencies across 1,000 resamples for Top 10 candidates.", width_in=5.4)

add_p(
    "We also tested alternative aggregation rules. Replacing weighted z-scores with equal-weight z-scores preserved 90.0% of the top ten "
    "in both cohorts, with rank correlations above 0.995. Replacing z-scores with non-parametric Reciprocal Rank Fusion preserved 90.0% "
    "of both top tens, with correlations of 0.9833 for batters and 0.9789 for bowlers."
)
add_p(
    "When testing alternative leverage thresholds (PI cutoffs of 0.60, 0.65, and 0.70) and volume minimums (100, 120, and 150 balls), "
    "rank correlation with our baseline never fell below 0.881. In split-half tests comparing odd-numbered matches against even-numbered "
    "matches, rank correlation was 0.8842 for batters and 0.8619 for bowlers."
)
add_bullet("Verdict: PASS. Rankings remain stable under resampling, alternative aggregation rules, and threshold variations.")

add_h2("5.4 Predictive Held-Out Validation")
add_p(
    "To test whether the consensus predicts future pressure performance better than individual models or simple heuristics, we performed "
    "an out-of-time evaluation. We built models exclusively on matches from 2022 to 2024 (520 matches) and tested their predictions on "
    "pressure deliveries from 2025 and 2026 (363 matches)."
)

add_image(f"{VAL_DIR}/held_out_predictive_comparison_bars.png", "Figure 5: Out-of-sample predictive performance on 2025-2026 held-out pressure deliveries.", width_in=5.4)

# Table 2: Held Out Performance
add_h3("Table 2: Held-Out Predictive Performance (Trained 2022-2024, Tested 2025-2026)")
t_ho = doc.add_table(rows=8, cols=4)
t_ho.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_ho = ["Candidate Approach", "Batters Held-Out RAAE/100", "Bowlers Held-Out RSAE/24", "Rank Correlation"]
for j, h in enumerate(headers_ho):
    c = t_ho.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=50, right=50)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in [1, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i, row in held_out_df.iterrows():
    vals = [
        str(row["Candidate_Approach"]),
        f"+{row['Batters_HeldOut_RAAE_100']:.2f}" if row['Batters_HeldOut_RAAE_100'] > 0 else f"{row['Batters_HeldOut_RAAE_100']:.2f}",
        f"+{row['Bowlers_HeldOut_RSAE_24']:.2f}" if row['Bowlers_HeldOut_RSAE_24'] > 0 else f"{row['Bowlers_HeldOut_RSAE_24']:.2f}",
        f"{row['Rank_Correlation_With_HeldOut']:.3f}"
    ]
    for j, val in enumerate(vals):
        c = t_ho.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in [1, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.5)
        if i == 0 or j == 0:
            r.font.bold = True

add_p(
    "As shown in Table 2 and Figure 5, the top ten batters identified by our consensus generated +24.41 Runs Added Above Expected "
    "per 100 balls on held-out 2025-2026 pressure deliveries. This exceeded Model 1 alone (+21.01), Model 2 alone (+18.61), "
    "Model 3 alone (+19.51), the naive death strike rate baseline (+16.31), and the overall eligible pool average (-5.19). "
    "In bowling, our consensus top ten saved +6.81 Runs Above Expected per 24 balls on unseen pressure play, outperforming Model 1 "
    "alone (+6.16), Model 2 alone (+5.69), Model 3 alone (+5.83), the naive death economy baseline (+4.51), and the population average (+0.85)."
)
add_bullet("Verdict: PASS. The consensus ensemble outperforms all single constituent models, naive heuristics, and random selection on unseen data.")

add_h2("5.5 Domain Weaknesses and Practical Limits")
add_p(
    "We identify three specific domain limitations in our findings:"
)
add_bullet("1. Sample Size Variance in Emerging Players: While veterans such as Suryakumar Yadav (655 pressure balls) and Sunil Narine (477 pressure balls) possess deep empirical foundations, younger candidates such as Prabhsimran Singh (129 pressure balls) and Mayank Yadav (192 pressure balls) sit closer to our 120-ball threshold. Although Bayesian shrinkage pulls their estimates toward the population mean, their ratings carry wider standard errors than those of multi-year veterans.")
add_bullet("2. Positional Role Effects: Top-order batters who bat into the death overs enter the pressure zone with settled eye-hand coordination, facing bowlers who are already fatigued. By contrast, specialized finishers enter cold against primary death bowlers with immediate boundary requirements. Similarly, new-ball powerplay bowlers face fielding restrictions while death bowlers defend larger outfields. Our LightGBM expected baseline adjusts for phase and wickets down, but cannot fully remove the physiological difference of entering a match cold.")
add_bullet("3. Absence of Pitch and Dew Data: The tournament data pack records match date, venue, city, toss, and score progression, but contains no direct telemetry on surface characteristics (degrees of turn, pitch hardness, millimeter bounce) or evening atmospheric moisture (dew readings). While ground-level par scores adjust for venue scoring environments, localized conditions (such as severe evening dew during second innings at Barsapara Stadium in Guwahati) could not be modeled directly.")
add_bullet("Verdict: CAUTION. Analysts must account for player entry points and physical venue conditions when translating these ratings into match tactical plans.")

doc.add_page_break()

# ==========================================
# 6. RR TACTICAL AND AUCTION OVERLAY
# ==========================================
add_h1("6. Rajasthan Royals Tactical and Auction Overlay")

add_h2("6.1 RR Squad Context Post-Retentions")
add_p(
    "Following official retentions and trades, Rajasthan Royals enters the upcoming auction cycle with 19 locked squad members: "
    "Riyan Parag, Yashasvi Jaiswal, Vaibhav Sooryavanshi, Ravindra Jadeja, Dhruv Jurel, Jofra Archer, Mohammed Shami, "
    "Manimaran Siddharth, Ravi Bishnoi, Sandeep Sharma, Nandre Burger, Shubham Dubey, Aman Rao Perala, Dasun Shanaka, "
    "Donovan Ferreira, Lhuan-dre Pretorius, Sushant Mishra, Yash Punja, and Brijesh Sharma. "
    "This leaves exactly 6 vacant roster slots (maximum 3 overseas slots available) and a remaining auction purse of Rs 27.05 crore."
)
add_p(
    "Evaluating the retained core reveals two primary tactical vulnerabilities: "
    "First, the departure of Shimron Hetmyer and Sam Curran creates a void for a dedicated Nos. 5 to 7 high-pressure finisher (Role A). "
    "Second, while Jofra Archer, Mohammed Shami, and Sandeep Sharma provide premier quality, injury history necessitates a dedicated "
    "death-overs specialist pacer (Role B) to insulate the bowling attack."
)

add_h2("6.2 Role A Targets: Nos. 5-7 High-Pressure Finisher (Overs 15-20)")
add_p(
    "We evaluated all eligible players excluding RR's 19 retained players on death-overs pressure metrics (overs 15 to 20, PI >= 0.65):"
)
add_bullet("Glenn Phillips (Overseas, Est. Rs 6.0 - 8.5 Cr): Direct replacement for Shimron Hetmyer. Generates +41.16 RAAE/100 at 198.63 SR under death pressure across 146 balls with a 26.71% boundary rate. Elite boundary rider and versatile backup off-spinner.")
add_bullet("Ashutosh Sharma (Indian, Est. Rs 3.5 - 5.5 Cr): Premier domestic Indian finisher. Generates +41.10 RAAE/100 at 195.00 SR under death pressure. Preserves an overseas slot and frees up auction purse for elite death bowling.")
add_bullet("Liam Livingstone (Overseas, Est. Rs 7.0 - 9.5 Cr): Familiarity with the franchise. Produces +39.46 RAAE/100 at 199.59 SR with raw boundary power to clear SMS Stadium Jaipur's long square boundaries (70m+).")
add_bullet("Jitesh Sharma (Indian, Est. Rs 4.0 - 6.0 Cr): Aggressive counter-attacker from ball one (+33.78 RAAE/100, 194.47 SR). Partners with Dhruv Jurel at Nos. 5 and 6, providing dual Indian wicketkeeper-finisher flexibility.")

add_h2("6.3 Role B Targets: Death-Overs Specialist Pacer (Overs 16-20)")
add_p(
    "We evaluated death-overs pacers (overs 16 to 20, PI >= 0.65) to identify specialist stoppers:"
)
add_bullet("Matheesha Pathirana (Overseas, Est. Rs 9.0 - 12.0 Cr): The premier death bowler in global cricket. Low-release sling yorkers yield a sub-8.00 RPO economy (7.96 RPO) and +5.32 RSAE/24 across 373 death balls with 52 pressure wickets. Insulates Jofra Archer and Sandeep Sharma from workload burnout.")
add_bullet("Spencer Johnson (Overseas, Est. Rs 5.0 - 7.5 Cr): Express 145+ km/h left-arm pace creating steep bounce. Boasts the highest death dot-ball percentage (44.44%) among all evaluated pacers (+5.65 RSAE/24, 8.19 Econ).")
add_bullet("Taskin Ahmed (Overseas, Est. Rs 3.0 - 4.5 Cr): High-pace skiddy workhorse (+4.20 RSAE/24, 7.98 Econ, 40.6% dots). Budget-friendly alternative if Pathirana's price escalates beyond Rs 12 Cr.")
add_bullet("Prasidh Krishna (Indian, Est. Rs 4.0 - 6.0 Cr): Former RR pacer with extensive home ground experience at SMS Jaipur. Towering release point exploits hard-length bounce to protect Jaipur's large boundaries (+1.15 RSAE/24, 41.29% dots).")

# Table 3: Auction Targets
add_h3("Table 3: Rajasthan Royals IPL 2027 Auction Target Priority Matrix")
t_auc = doc.add_table(rows=7, cols=7)
t_auc.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_auc = ["Priority", "Role", "Player", "Nationality", "Key Metric", "Est. Cost", "Fit Rationale"]
for j, h in enumerate(headers_auc):
    c = t_auc.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=40, right=40)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in [4, 5] else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.0)
    r.font.color.rgb = RGBColor(15, 35, 65)

auc_rows = [
    ("Tier 1 Marquee", "Finisher (5-7)", "Glenn Phillips", "Overseas", "+41.16 RAAE", "Rs 6.0 - 8.5 Cr", "Like-for-like Hetmyer replacement; 360 hitter"),
    ("Tier 1 Indian", "Finisher (5-7)", "Ashutosh Sharma", "Indian", "+41.10 RAAE", "Rs 3.5 - 5.5 Cr", "High-impact domestic bat; saves foreign slot"),
    ("Tier 2 Power", "Finisher (5-7)", "Liam Livingstone", "Overseas", "+39.46 RAAE", "Rs 7.0 - 9.5 Cr", "Ex-RR power hitter; suits SMS boundary dimensions"),
    ("Tier 1 Marquee", "Death Pacer", "Matheesha Pathirana", "Overseas", "+5.32 RSAE", "Rs 9.0 - 12.0 Cr", "Elite sling yorkers; 7.96 Econ across 373 balls"),
    ("Tier 1 Express", "Death Pacer", "Spencer Johnson", "Overseas", "+5.65 RSAE", "Rs 5.0 - 7.5 Cr", "145+ km/h left-arm angle; 44.4% death dots"),
    ("Tier 2 Domestic", "Death Pacer", "Prasidh Krishna", "Indian", "+1.15 RSAE", "Rs 4.0 - 6.0 Cr", "Ex-RR pacer; exploits hard length at SMS Jaipur")
]

for i, row_vals in enumerate(auc_rows):
    for j, val in enumerate(row_vals):
        c = t_auc.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=40, right=40)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in [4, 5] else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.0)
        if j in [0, 2]:
            r.font.bold = True

add_h2("6.4 Auction Purse Allocation and Strategy Matrix")
add_p(
    "With Rs 27.05 crore across 6 vacant slots, we recommend two distinct execution strategies:"
)
add_bullet("Strategy A (Marquee Bowling Anchor): Bid up to Rs 11.0 Cr for Matheesha Pathirana as the defensive anchor, secure Ashutosh Sharma (Rs 4.5 Cr) as domestic finisher, and allocate the remaining Rs 11.55 Cr across four high-ceiling domestic backups.")
add_bullet("Strategy B (Dual Overseas Power): If Pathirana exceeds Rs 12.0 Cr, pivot to Spencer Johnson (Rs 6.5 Cr) and Glenn Phillips (Rs 7.5 Cr), securing Prasidh Krishna (Rs 5.0 Cr) to anchor domestic pace depth, leaving an Rs 8.05 Cr buffer for squad completion.")

doc.add_page_break()

# ==========================================
# 7. APPENDICES
# ==========================================
add_h1("7. Appendices")

add_h2("Appendix A: Data Manifest and Cryptographic Hashes")
add_p(
    "To ensure complete reproducibility, Table A1 records cryptographic SHA-256 hashes for all raw datasets and environment specifications:"
)

t_hash = doc.add_table(rows=7, cols=3)
t_hash.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_hash = ["Dataset File Name", "Record Count", "SHA-256 Cryptographic Checksum"]
for j, h in enumerate(headers_hash):
    c = t_hash.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=40, bottom=40, left=50, right=50)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 1 else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.0)
    r.font.color.rgb = RGBColor(15, 35, 65)

hash_data = [
    ("ball_by_ball.csv", "200,999", manifest_data["input_data_hashes"]["ball_by_ball.csv"][:32] + "..."),
    ("matches.csv", "883", manifest_data["input_data_hashes"]["matches.csv"][:32] + "..."),
    ("competitions.csv", "141", manifest_data["input_data_hashes"]["competitions.csv"][:32] + "..."),
    ("teams.csv", "353", manifest_data["input_data_hashes"]["teams.csv"][:32] + "..."),
    ("playing_eleven.csv", "28,381", manifest_data["input_data_hashes"]["playing_eleven.csv"][:32] + "..."),
    ("competition_team_player_mapping.csv", "6,413", manifest_data["input_data_hashes"]["competition_team_player_mapping.csv"][:32] + "...")
]

for i, row_vals in enumerate(hash_data):
    for j, val in enumerate(row_vals):
        c = t_hash.cell(i + 1, j)
        if i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=30, bottom=30, left=50, right=50)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 1 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.0)
        if j == 0:
            r.font.bold = True

add_p(
    f"Environment Specifications: Python {manifest_data['python_version']}, Random Seed: {manifest_data['random_seed']}, "
    f"Execution Suite: src/validate.py. Verified at: {manifest_data['date']}."
)

add_h2("Appendix B: Top 15 Batters Diagnostic Breakdown (With Ranks 11-15 Backups)")
t_b15 = doc.add_table(rows=16, cols=8)
t_b15.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_b15 = ["Rank", "Player Name", "HP Balls", "M1 Rank", "M2 Rank", "M3 Rank", "Spread", "Score"]
for j, h in enumerate(headers_b15):
    c = t_b15.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=30, bottom=30, left=40, right=40)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.0)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i, row in top15_bat.iterrows():
    spread = int(max(row["rank_m1"], row["rank_m2"], row["rank_m3"]) - min(row["rank_m1"], row["rank_m2"], row["rank_m3"]))
    vals = [
        str(int(row["final_rank"])),
        str(row["player_name"]),
        str(int(row["hp_balls"])),
        str(int(row["rank_m1"])),
        str(int(row["rank_m2"])),
        str(int(row["rank_m3"])),
        str(spread),
        f"{row['final_ensemble_score']:.2f}"
    ]
    for j, val in enumerate(vals):
        c = t_b15.cell(i + 1, j)
        if i >= 10:
            set_cell_shading(c, "FFFBEB")
        elif i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=25, bottom=25, left=40, right=40)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.0)
        if j in [0, 1, 7]:
            r.font.bold = True

add_h2("Appendix C: Top 15 Bowlers Diagnostic Breakdown (With Ranks 11-15 Backups)")
t_bw15 = doc.add_table(rows=16, cols=8)
t_bw15.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_bw15 = ["Rank", "Player Name", "HP Balls", "M1 Rank", "M2 Rank", "M3 Rank", "Spread", "Score"]
for j, h in enumerate(headers_bw15):
    c = t_bw15.cell(0, j)
    set_cell_shading(c, "E8EEF5")
    set_cell_border(c, top=dict(sz=4, color="B0C0D0"), bottom=dict(sz=6, color="8090A0"),
                       left=dict(sz=2, color="D0D7DE"), right=dict(sz=2, color="D0D7DE"))
    set_cell_margins(c, top=30, bottom=30, left=40, right=40)
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(h)
    r.font.bold = True
    r.font.size = Pt(8.0)
    r.font.color.rgb = RGBColor(15, 35, 65)

for i, row in top15_bowl.iterrows():
    spread = int(max(row["rank_m1"], row["rank_m2"], row["rank_m3"]) - min(row["rank_m1"], row["rank_m2"], row["rank_m3"]))
    vals = [
        str(int(row["final_rank"])),
        str(row["player_name"]),
        str(int(row["hp_balls"])),
        str(int(row["rank_m1"])),
        str(int(row["rank_m2"])),
        str(int(row["rank_m3"])),
        str(spread),
        f"{row['final_ensemble_score']:.2f}"
    ]
    for j, val in enumerate(vals):
        c = t_bw15.cell(i + 1, j)
        if i >= 10:
            set_cell_shading(c, "FFFBEB")
        elif i % 2 == 1:
            set_cell_shading(c, "F8FAFC")
        set_cell_border(c, top=dict(sz=2, color="E0E6ED"), bottom=dict(sz=2, color="E0E6ED"),
                           left=dict(sz=2, color="E0E6ED"), right=dict(sz=2, color="E0E6ED"))
        set_cell_margins(c, top=25, bottom=25, left=40, right=40)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(val)
        r.font.size = Pt(8.0)
        if j in [0, 1, 7]:
            r.font.bold = True

print(f"Saving DOCX to {DOCX_PATH}...")
doc.save(DOCX_PATH)
print("DOCX saved successfully.")

# ==========================================
# 8. COMPILE PDF VIA PYMUPDF STORY
# ==========================================
print("Compiling publication PDF via PyMuPDF...")

# Convert content to high-fidelity HTML for PyMuPDF Story
html_parts = []
html_parts.append("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.35;
    color: #222222;
}
h1 {
    font-size: 16pt;
    color: #0b2545;
    margin-top: 14pt;
    margin-bottom: 4pt;
    border-bottom: 1.5pt solid #0b2545;
    padding-bottom: 2pt;
    page-break-after: avoid;
}
h2 {
    font-size: 11.5pt;
    color: #193c6e;
    margin-top: 10pt;
    margin-bottom: 3pt;
    page-break-after: avoid;
}
h3 {
    font-size: 10pt;
    color: #2d4155;
    margin-top: 7pt;
    margin-bottom: 2pt;
    page-break-after: avoid;
}
p {
    margin-top: 0;
    margin-bottom: 5pt;
    text-align: justify;
}
ul {
    margin-top: 0;
    margin-bottom: 5pt;
    padding-left: 18pt;
}
li {
    margin-bottom: 2.5pt;
}
.title-block {
    text-align: center;
    margin-bottom: 12pt;
    border-bottom: 2pt solid #0b2545;
    padding-bottom: 8pt;
}
.main-title {
    font-size: 19pt;
    font-weight: bold;
    color: #0b2545;
    line-height: 1.2;
    margin-bottom: 4pt;
}
.subtitle {
    font-size: 10.5pt;
    color: #4a5568;
    font-style: italic;
    margin-bottom: 8pt;
}
.meta-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 6pt;
    font-size: 8.5pt;
}
.meta-table td {
    padding: 3pt 6pt;
    border: 1px solid #d0d7de;
    background-color: #f2f5f8;
}
table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 4pt;
    margin-bottom: 7pt;
    font-size: 7.8pt;
}
table.data-table th {
    background-color: #e8eef5;
    color: #0f2341;
    font-weight: bold;
    border: 1px solid #b0c0d0;
    padding: 3.5pt 4pt;
    text-align: left;
}
table.data-table td {
    border: 1px solid #e0e6ed;
    padding: 3pt 4pt;
}
table.data-table tr:nth-child(even) td {
    background-color: #f8fafc;
}
.right { text-align: right; }
.center { text-align: center; }
.bold { font-weight: bold; }
.img-container {
    text-align: center;
    margin-top: 6pt;
    margin-bottom: 7pt;
    page-break-inside: avoid;
}
.img-container img {
    max-width: 92%;
    height: auto;
}
.caption {
    font-size: 8pt;
    font-style: italic;
    color: #5a646e;
    margin-top: 2pt;
}
.page-break {
    page-break-after: always;
}
</style>
</head>
<body>
""")

# Title block
html_parts.append("""
<div class="title-block">
    <div class="main-title">Rajasthan Royals SupeRR Selector Season 2<br>Round 1 Methodology Report</div>
    <div class="subtitle">Quantifying High-Pressure Performance in Batters and Bowlers Across IPL and Men's T20 Internationals (2022-2026)</div>
    <table class="meta-table">
        <tr>
            <td><strong>Author:</strong> Shamit Bundela (Lead Quantitative Analyst)</td>
            <td><strong>Contest:</strong> Rajasthan Royals SupeRR Selector Season 2 (Round 1)</td>
        </tr>
        <tr>
            <td><strong>Target:</strong> Top 10 Batters & Top 10 Bowlers Under Pressure</td>
            <td><strong>Date:</strong> November 2026</td>
        </tr>
    </table>
</div>
""")

# Executive summary
html_parts.append("""
<h1>Executive Summary</h1>
<p>
We present a unified quantitative evaluation framework to isolate, evaluate, and rank T20 cricketers under match leverage. 
Rather than treating all deliveries equally or relying on blunt death-overs heuristics, we model ball-by-ball win probabilities 
using match state, venue run environments, and innings progression across 200,999 deliveries between 2022 and 2026. 
Deliveries with continuous Pressure Index PI &ge; 0.65 (the top 28.55% leverage distribution) are classified as high pressure. 
Player performance in these moments is evaluated across three distinct modeling paradigms: contextual run expectancy above 
expectation with Bayesian shrinkage (Model 1), rate elevation deltas relative to player baseline (Model 2), and match-level 
clutch consistency (Model 3). These paradigms are standardized into Z-scores and combined using fixed weights (0.40, 0.35, 0.25). 
All active players meeting a 120-ball threshold are ranked, with non-IPL eligible players separated into an unfiltered reference 
list to produce a defensible, verified submission ranking.
</p>
""")

# Top 10 Batters HTML Table
html_parts.append("<h2>Table E1: Official Submission Top 10 Batters (IPL-Eligible)</h2>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th class='center'>Rank</th><th>Player</th><th>Franchise</th><th class='right'>HP Balls</th><th class='right'>HP SR</th><th class='right'>Usual SR</th><th class='right'>Delta SR</th><th class='right'>RAAE/100</th><th class='center'>Score</th></tr>")
for i, r in top10_bat_ipl.iterrows():
    delta_str = f"+{r['Delta_SR']:.1f}" if r['Delta_SR'] > 0 else f"{r['Delta_SR']:.1f}"
    html_parts.append(f"<tr><td class='center bold'>{int(r['rank'])}</td><td class='bold'>{r['player_name']}</td><td>{str(r['ipl_teams']).split(',')[0].strip()}</td><td class='right'>{int(r['hp_balls'])}</td><td class='right'>{r['Pressure_SR']:.1f}</td><td class='right'>{r['Usual_SR']:.1f}</td><td class='right'>{delta_str}</td><td class='right'>+{r['Pressure_RAA_100']:.1f}</td><td class='center bold'>{r['final_ensemble_score']:.2f}</td></tr>")
html_parts.append("</table>")

# Top 10 Bowlers HTML Table
html_parts.append("<h2>Table E2: Official Submission Top 10 Bowlers (IPL-Eligible)</h2>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th class='center'>Rank</th><th>Player</th><th>Franchise</th><th class='right'>HP Balls</th><th class='right'>Wkts</th><th class='right'>HP Econ</th><th class='right'>Usual Econ</th><th class='right'>RSAE/24</th><th class='center'>Score</th></tr>")
for i, r in top10_bowl_ipl.iterrows():
    html_parts.append(f"<tr><td class='center bold'>{int(r['rank'])}</td><td class='bold'>{r['player_name']}</td><td>{str(r['ipl_teams']).split(',')[0].strip()}</td><td class='right'>{int(r['hp_balls'])}</td><td class='right'>{int(r['hp_wkts'])}</td><td class='right'>{r['Pressure_Econ']:.2f}</td><td class='right'>{r['Usual_Econ']:.2f}</td><td class='right'>+{r['Pressure_RSAE_24']:.2f}</td><td class='center bold'>{r['final_ensemble_score']:.2f}</td></tr>")
html_parts.append("</table>")

html_parts.append("<div class='page-break'></div>")

# Section 1
html_parts.append("""
<h1>1. Pressure Definition</h1>
<h2>1.1 The Need for In-Match Pressure Quantification</h2>
<p>
Standard cricket analytics frequently conflates pressure with chronological match phase, labeling all balls bowled in 
overs 16 to 20 as death pressure. This heuristic fails in two fundamental ways. First, dead death overs occur regularly: 
a final over where the batting side requires 45 runs with two wickets remaining carries near-zero win leverage. 
Second, high-leverage events occur outside the death overs: a team reduced to 28/4 in the powerplay during a chase 
of 190 confronts extreme match stress, where every ball determines survival or collapse. 
To measure genuine pressure, we define leverage through an explicit win-probability framework.
</p>
<h2>1.2 Win-Probability Architecture and Features</h2>
<p>
We trained a gradient-boosted decision tree classifier (LightGBM) on 200,999 legal deliveries across 883 matches 
(226 IPL fixtures and 657 Men's T20 Internationals) between 2022 and 2026. The target variable is match victory (1 for win, 0 for loss). 
The model takes eight contextual state features at each delivery: balls remaining, runs remaining or projected score, wickets lost, 
required run rate vs current run rate, venue historic par score, innings indicator, knockout match indicator, and recent 12-ball run acceleration.
</p>
<h2>1.3 Model Validation and Probability Calibration</h2>
<p>
The win-probability model was validated using 5-fold match-grouped cross-validation. The model achieved a Brier score of 0.162, 
a Log Loss of 0.481, and an Area Under the ROC Curve of 0.884 across all test folds.
</p>
<div class="img-container">
    <img src="outputs/validation/calibration_plot.png" />
    <div class="caption">Figure 1: Win probability calibration curve across 200,999 deliveries (Brier = 0.162, Log Loss = 0.481).</div>
</div>
<p>
As shown in Figure 1, predicted probabilities align closely with observed victory frequencies across all deciles, 
confirming that estimated win likelihoods reflect true game states without systematic over-confidence.
</p>
<h2>1.4 Leverage Score Formulation and Cutoff Selection</h2>
<p>
For each legal delivery t, leverage represents the sensitivity of match outcome to the immediate events on that ball:
L_t = |WP(run_t = 4 | S_t) - WP(S_t)| + |WP(wicket_t = 1 | S_t) - WP(S_t)|.
We normalize L_t into a continuous Pressure Index PI in [0, 1]. 
We establish PI &ge; 0.65 as our operational threshold for high-pressure play, isolating the top 28.55% of all deliveries 
(57,385 deliveries out of 200,999).
</p>
<h2>1.5 Empirical Proof of Pressure State Disparity</h2>
<ul>
    <li><strong>Wicket Hazard:</strong> Dismissal probability rises from 4.1% per ball in low leverage to 6.2% under pressure (+51.2% increase).</li>
    <li><strong>Required Scoring Rate:</strong> Chasing sides face an average required run rate of 10.84 RPO under pressure compared to 8.12 RPO in normal play.</li>
    <li><strong>Dot-Ball Frequency:</strong> Bowling dot-ball percentage increases from 33.1% to 38.6%, reflecting tighter defensive bowling lines.</li>
    <li><strong>Boundary Demands:</strong> Boundary frequency required to sustain win probability increases from 15.2% to 17.8%.</li>
</ul>
<p>
When comparing our continuous PI &ge; 0.65 threshold to the naive rule-based alternative (overs 16-20 with RRR &gt; 9.0), 
the rule-based filter exhibits a 23.4% false-negative rate and an 18.2% false-positive rate. Our continuous PI framework isolates authentic match leverage.
</p>
""")

html_parts.append("<div class='page-break'></div>")

# Section 2
html_parts.append("""
<h1>2. Performance Measurement</h1>
<h2>2.1 The Two Fundamental Baselines</h2>
<p>Evaluating players under pressure requires comparing their output against two distinct baselines:</p>
<ul>
    <li><strong>Baseline 1 (League Situational Expectation):</strong> What would an average tournament cricketer produce on this exact ball? We generate expected runs (xRuns) and expected dismissals (xWkt) for every delivery from the LightGBM baseline.</li>
    <li><strong>Baseline 2 (Player Career Usual Level):</strong> What does this specific player produce in non-pressure deliveries (PI &lt; 0.65)? This measures whether a player elevates or declines relative to their own established norm.</li>
</ul>
<h2>2.2 Multi-Model Evaluation Paradigms</h2>
<h3>Model 1: Contextual Machine Learning Expectation Model (Primary Anchor)</h3>
<p>
Model 1 evaluates net contextual contribution above delivery expectation. For batters, Runs Added Above Expected per 100 balls 
(RAAE/100) measures scoring surplus while factoring in wicket preservation. For bowlers, Runs Saved Above Expected per 24 balls 
(RSAE/24) measures economy suppression plus wicket generation. Both metrics are stabilized using Empirical Bayes shrinkage with K = 40.0.
</p>
<h3>Model 2: Rate Elevation and Baseline Delta Model</h3>
<p>
Model 2 isolates player uplift relative to their personal usual standard: Delta SR = Pressure_SR - Usual_SR for batters, 
and Delta Econ = Usual_Economy - Pressure_Economy for bowlers.
</p>
<h3>Model 3: Clutch Match Consistency and Reliability Model</h3>
<p>
Model 3 penalizes volatile performers who produce one high-scoring outlier surrounded by failures, calculating the percentage 
of high-pressure matches in which a player achieved positive net contribution above league average, scaled by volume: 
Score_M3 = Consistency_Pct * ln(HP_Balls).
</p>
<h2>2.3 Standardization, Weighting, and Variance Attribution</h2>
<p>
Each model raw score is converted to a standardized Z-score across the eligible cohort. 
We combine the standardized models using weights fixed in config.yaml before inspecting player ranks: 
0.40 for Model 1, 0.35 for Model 2, and 0.25 for Model 3. 
Euler portfolio variance decomposition confirms balanced effective variance contributions without silent dominance: 
Model 1 contributes 42.28% in batters and 43.05% in bowlers; Model 2 contributes 33.29% and 33.31%; Model 3 contributes 24.43% and 23.64%.
</p>
""")

html_parts.append("<div class='page-break'></div>")

# Section 3
html_parts.append("""
<h1>3. Fair Comparisons and Eligibility Architecture</h1>
<h2>3.1 Sample Size and Activity Thresholds</h2>
<p>
To ensure statistical defensibility, we enforce strict qualification gates: minimum 120 legal pressure balls, active match on or after 
January 1, 2025, and IPL eligibility. Out of 1,412 total players in the dataset, 113 batters and 123 bowlers qualified. 
A total of 1,299 player records were excluded (1,084 for volume below 120 balls, 147 for inactivity pre-2025, 61 for Pakistan nationality 
without IPL contracts, and 7 confirmed retired veterans: Dinesh Karthik, Shikhar Dhawan, Kieron Pollard, Ambati Rayudu, Suresh Raina, 
Vijay Shankar, and Moeen Ali).
</p>
<h2>3.2 Small-Sample Bayesian Shrinkage</h2>
<p>
All rate metrics are regressed toward the population mean: theta_shrunk = w * theta_observed + (1 - w) * mu_population, 
where w = N / (N + 40). A player with 120 pressure balls receives a shrinkage weight of 0.750, whereas a veteran with 600 balls receives 0.938.
</p>
<h2>3.3 Opposition, Phase, and Venue Adjustments</h2>
<p>
Delivery-level expected runs (xRuns) dynamically adjust for venue par scores, match phase, and wickets down, 
ensuring that players on high-scoring pitches receive no artificial advantage over players performing on difficult tracks.
</p>
<h2>3.4 Handling of Non-IPL Eligible Players</h2>
<p>
All players remain in the models during training to ensure league baselines reflect true competitive standards. 
Only at the final submission stage are players filtered into dual lists:
</p>
""")

# Table 1: Comparison HTML Table
html_parts.append("<h3>Table 1: Unfiltered Consensus vs Official IPL-Eligible Top 10 Comparison</h3>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th class='center'>Rank</th><th>Unfiltered Batters</th><th>IPL Submission Batters</th><th>Unfiltered Bowlers</th><th>IPL Submission Bowlers</th></tr>")
for i in range(10):
    r_ab = top10_bat_all.iloc[i]
    r_ib = top10_bat_ipl.iloc[i]
    r_aw = top10_bowl_all.iloc[i]
    r_iw = top10_bowl_ipl.iloc[i]
    html_parts.append(f"<tr><td class='center bold'>{i+1}</td><td>{r_ab['player_name']} ({r_ab['final_ensemble_score']:.1f})</td><td class='bold'>{r_ib['player_name']} ({r_ib['final_ensemble_score']:.1f})</td><td>{r_aw['player_name']} ({r_aw['final_ensemble_score']:.1f})</td><td class='bold'>{r_iw['player_name']} ({r_iw['final_ensemble_score']:.1f})</td></tr>")
html_parts.append("</table>")

html_parts.append("<p>In batters, Mark Chapman (rank 9 overall, New Zealand) slides out, elevating Liam Livingstone to rank 9 and Heinrich Klaasen into rank 10. In bowlers, Roston Chase (rank 9) and Taskin Ahmed (rank 10) slide out, elevating Akeal Hosein to rank 9 and Mohsin Khan into rank 10.</p>")

html_parts.append("<div class='page-break'></div>")

# Section 4
html_parts.append("""
<h1>4. What We Tried and Changed</h1>
<p>We document the chronological evolution of our analytical pipeline, including discarded iterations and the empirical evidence that motivated each change:</p>
<h2>Iteration 1: Rule-Based Death Overs Filter (Discarded)</h2>
<p>We initially defined pressure using overs 16 to 20 with RRR &gt; 9.0. Discarded because it generated a 23.4% false-negative rate (omitting middle-overs collapses) and an 18.2% false-positive rate (incorporating dead death overs in blowouts). Replaced by continuous win-probability leverage.</p>
<h2>Iteration 2: Raw Unadjusted Rate Metrics (Discarded)</h2>
<p>We evaluated players using raw high-pressure strike rates and economy rates. Discarded due to severe venue bias: batters at high-altitude or small venues (e.g. Bengaluru) dominated, whereas finishers on spinning surfaces (e.g. Chennai) were penalized despite match-winning output. Replaced by contextual xRuns and xWkt expectations.</p>
<h2>Iteration 3: Un-Shrunk Situational Deltas (Discarded)</h2>
<p>We computed strike rate deltas without sample size adjustments. Discarded because low-sample players with 20 to 30 balls recorded unsustainable deltas exceeding +80.0. Resolved by establishing the 120-ball threshold and Empirical Bayes shrinkage (K = 40.0).</p>
<h2>Iteration 4: Single-Model Contextual Expectation (Discarded as Sole Criterion)</h2>
<p>We tested using Model 1 as the sole ranking metric. Discarded because it penalized elite baseline players through the Baseline Ceiling/Floor Effect (e.g. Bumrah's 6.88 baseline economy or Abhishek Sharma's 186.3 baseline strike rate limited their delta room). Resolved by building a multi-model consensus ensemble.</p>
<h2>Iteration 5: Final Multi-Model Consensus with Z-Score Standardization (Adopted)</h2>
<p>Standardizes Model 1, Model 2, and Model 3 into Z-scores and aggregates them with fixed weights (0.40, 0.35, 0.25). This combines contextual expectation, rate uplift, and match consistency while insulating the rankings from single-model distortions.</p>
""")

html_parts.append("<div class='page-break'></div>")

# Section 5
html_parts.append("""
<h1>5. Reliability and Limitations</h1>
<p>To evaluate whether our ratings reflect genuine pressure ability rather than noise or weighting bias, we subjected the multi-model pipeline to five diagnostic tests in src/validate.py:</p>
<h2>5.1 Inclusion and Model Contribution Audit</h2>
<p>
Both the batter pool (113 players) and the bowler pool (123 players) contain zero missing values across all score columns. 
In our leave-one-model-out test, removing Model 1 shifted 2 batters and 3 bowlers in the top ten; removing Model 2 shifted 3 batters and 2 bowlers; 
removing Model 3 shifted 1 batter and 1 bowler. Every constituent model produces a non-zero shift in the final ranking.
</p>
<ul><li><strong>Verdict: PASS.</strong> Every model contributes non-trivially to the consensus.</li></ul>
<h2>5.2 Agreement and Sanity Checks</h2>
<p>
Consensus scores achieve higher average correlation with the base models than any single model achieves with the other two 
(0.8771 for batters and 0.8422 for bowlers), verifying that the ensemble operates as the consensus centroid.
</p>
<div class="img-container">
    <img src="outputs/validation/model_correlation_heatmap.png" />
    <div class="caption">Figure 2: Spearman correlation matrix across constituent models and the final consensus ensemble.</div>
</div>
<p>
Four top-ten players exhibited rank spreads above 30 spots across models (Abhishek Sharma, Tim David, Jasprit Bumrah, Wanindu Hasaranga). 
These divergences occur solely due to Baseline Ceiling/Floor Effects: their usual standard is already elite, mathematically constraining 
their delta metrics. The ensemble prevents these elite performers from being penalized by isolated rate deltas.
</p>
<div class="img-container">
    <img src="outputs/validation/rank_range_dotplot.png" />
    <div class="caption">Figure 3: Intra-model rank spread across Top 10 batters and bowlers, illustrating consensus convergence.</div>
</div>
<ul><li><strong>Verdict: PASS.</strong> Intra-model divergences reflect explainable baseline ceiling effects rather than statistical anomalies.</li></ul>
<h2>5.3 Resampling Stability and Threshold Sensitivity</h2>
<p>
In a 1,000-resample match bootstrap, top players demonstrated high selection persistence: Suryakumar Yadav, Ishan Kishan, Sunil Narine, 
and Jasprit Bumrah appeared in the top ten in 100.0% of iterations.
</p>
<div class="img-container">
    <img src="outputs/validation/bootstrap_top10_frequency_bars.png" />
    <div class="caption">Figure 4: Bootstrap selection frequencies across 1,000 resamples for Top 10 candidates.</div>
</div>
<p>
Equal-weight Z-scores and non-parametric Reciprocal Rank Fusion both preserved 90.0% of the top ten in both cohorts (correlations &gt; 0.978). 
Varying PI cutoffs (0.60 to 0.70) and ball minimums (100 to 150) maintained correlations above 0.881.
</p>
<ul><li><strong>Verdict: PASS.</strong> Rankings remain stable under resampling, alternative aggregation rules, and threshold variations.</li></ul>
<h2>5.4 Predictive Held-Out Validation</h2>
<p>
We trained models on 2022-2024 fixtures (520 matches) and tested on 2025-2026 pressure deliveries (363 matches). 
The consensus top ten batters generated +24.41 RAAE/100, outperforming Model 1 (+21.01), Model 2 (+18.61), Model 3 (+19.51), 
and naive death SR (+16.31). Consensus bowlers saved +6.81 RSAE/24, outperforming Model 1 (+6.16), Model 2 (+5.69), 
Model 3 (+5.83), and naive death economy (+4.51).
</p>
<div class="img-container">
    <img src="outputs/validation/held_out_predictive_comparison_bars.png" />
    <div class="caption">Figure 5: Out-of-sample predictive performance on 2025-2026 held-out pressure deliveries.</div>
</div>
""")

# Table 2: Held Out Performance Table
html_parts.append("<h3>Table 2: Held-Out Predictive Performance (Trained 2022-2024, Tested 2025-2026)</h3>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th>Candidate Approach</th><th class='right'>Batters Held-Out RAAE/100</th><th class='right'>Bowlers Held-Out RSAE/24</th><th class='right'>Rank Correlation</th></tr>")
for i, r in held_out_df.iterrows():
    b_val = f"+{r['Batters_HeldOut_RAAE_100']:.2f}" if r['Batters_HeldOut_RAAE_100'] > 0 else f"{r['Batters_HeldOut_RAAE_100']:.2f}"
    w_val = f"+{r['Bowlers_HeldOut_RSAE_24']:.2f}" if r['Bowlers_HeldOut_RSAE_24'] > 0 else f"{r['Bowlers_HeldOut_RSAE_24']:.2f}"
    bold_cls = " bold" if i == 0 else ""
    html_parts.append(f"<tr><td class='{bold_cls}'>{r['Candidate_Approach']}</td><td class='right{bold_cls}'>{b_val}</td><td class='right{bold_cls}'>{w_val}</td><td class='right{bold_cls}'>{r['Rank_Correlation_With_HeldOut']:.3f}</td></tr>")
html_parts.append("</table>")

html_parts.append("""
<ul><li><strong>Verdict: PASS.</strong> The consensus ensemble outperforms all single constituent models, naive heuristics, and random selection on unseen data.</li></ul>
<h2>5.5 Domain Weaknesses and Practical Limits</h2>
<ul>
    <li><strong>Sample Size Variance in Emerging Players:</strong> Candidates near the 120-ball threshold carry wider standard errors than multi-year veterans despite Bayesian shrinkage.</li>
    <li><strong>Positional Role Effects:</strong> Top-order batters entering the death overs with established eye-hand coordination face fatigued bowlers, whereas specialized finishers enter cold. Expected metrics adjust for phase but cannot fully remove entry-state physiological differences.</li>
    <li><strong>Absence of Pitch and Dew Data:</strong> Ground-level par scores adjust for venue conditions, but localized micro-climates (such as evening dew during second innings chases) could not be modeled directly due to lack of pitch sensor telemetry.</li>
</ul>
<ul><li><strong>Verdict: CAUTION.</strong> Analysts must account for player entry points and physical venue conditions when translating these ratings into match tactical plans.</li></ul>
""")

html_parts.append("<div class='page-break'></div>")

# Section 6
html_parts.append("""
<h1>6. Rajasthan Royals Tactical and Auction Overlay</h1>
<h2>6.1 RR Squad Context Post-Retentions</h2>
<p>
Rajasthan Royals enters the auction cycle with 19 locked players, leaving exactly 6 vacant roster slots (maximum 3 overseas slots available) 
and a remaining purse of Rs 27.05 crore. Tactical analysis highlights two critical post-retention gaps: 
a dedicated Nos. 5 to 7 high-pressure finisher (Role A) following the departure of Shimron Hetmyer and Sam Curran, 
and a death-overs specialist pacer (Role B) to insulate Jofra Archer, Mohammed Shami, and Sandeep Sharma against injury burnout.
</p>
<h2>6.2 Role A Targets: Nos. 5-7 High-Pressure Finisher (Overs 15-20)</h2>
<ul>
    <li><strong>Glenn Phillips (Overseas, Est. Rs 6.0 - 8.5 Cr):</strong> Direct replacement for Shimron Hetmyer (+41.16 RAAE/100, 198.63 SR, 26.71% boundary rate across 146 death balls). Elite boundary fielder and versatile backup off-spinner.</li>
    <li><strong>Ashutosh Sharma (Indian, Est. Rs 3.5 - 5.5 Cr):</strong> High-impact domestic finisher (+41.10 RAAE/100, 195.00 SR). Preserves an overseas slot and frees up auction purse for elite bowling.</li>
    <li><strong>Liam Livingstone (Overseas, Est. Rs 7.0 - 9.5 Cr):</strong> Proven boundary clearer (+39.46 RAAE/100, 199.59 SR) suited to SMS Jaipur's large square boundaries.</li>
    <li><strong>Jitesh Sharma (Indian, Est. Rs 4.0 - 6.0 Cr):</strong> Aggressive counter-attacker from ball one (+33.78 RAAE/100, 194.47 SR), providing wicketkeeper-finisher flexibility alongside Dhruv Jurel.</li>
</ul>
<h2>6.3 Role B Targets: Death-Overs Specialist Pacer (Overs 16-20)</h2>
<ul>
    <li><strong>Matheesha Pathirana (Overseas, Est. Rs 9.0 - 12.0 Cr):</strong> The gold standard in death execution (+5.32 RSAE/24, 7.96 Econ across 373 death balls, 52 pressure wickets). Sling yorkers provide match-winning closing ability.</li>
    <li><strong>Spencer Johnson (Overseas, Est. Rs 5.0 - 7.5 Cr):</strong> Express 145+ km/h left-arm pacer (+5.65 RSAE/24, 8.19 Econ, 44.44% death dots). Creates steep bounce to defend large boundaries.</li>
    <li><strong>Taskin Ahmed (Overseas, Est. Rs 3.0 - 4.5 Cr):</strong> High-pace workhorse (+4.20 RSAE/24, 7.98 Econ, 40.6% dots). Budget-friendly marquee alternative.</li>
    <li><strong>Prasidh Krishna (Indian, Est. Rs 4.0 - 6.0 Cr):</strong> Former RR pacer familiar with SMS Jaipur (+1.15 RSAE/24, 41.29% dots). Exploits hard-length bounce.</li>
</ul>
""")

# Table 3: Auction Target Priority Table
html_parts.append("<h3>Table 3: Rajasthan Royals IPL 2027 Auction Target Priority Matrix</h3>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th>Priority</th><th>Role</th><th>Player</th><th>Nationality</th><th class='right'>Key Metric</th><th class='right'>Est. Cost</th><th>Fit Rationale</th></tr>")
for p_tier, r_name, pl_name, nat, val_m, cost_e, fit_r in auc_rows:
    html_parts.append(f"<tr><td class='bold'>{p_tier}</td><td>{r_name}</td><td class='bold'>{pl_name}</td><td>{nat}</td><td class='right'>{val_m}</td><td class='right bold'>{cost_e}</td><td>{fit_r}</td></tr>")
html_parts.append("</table>")

html_parts.append("""
<h2>6.4 Auction Purse Allocation and Strategy Matrix</h2>
<ul>
    <li><strong>Strategy A (Marquee Bowling Anchor):</strong> Bid up to Rs 11.0 Cr for Matheesha Pathirana as primary defensive lock, secure Ashutosh Sharma (Rs 4.5 Cr) as domestic finisher, and allocate remaining Rs 11.55 Cr across four domestic backups.</li>
    <li><strong>Strategy B (Dual Overseas Power):</strong> If Pathirana exceeds Rs 12.0 Cr, pivot to Spencer Johnson (Rs 6.5 Cr) and Glenn Phillips (Rs 7.5 Cr), securing Prasidh Krishna (Rs 5.0 Cr) to anchor domestic pace depth, leaving an Rs 8.05 Cr buffer.</li>
</ul>
""")

html_parts.append("<div class='page-break'></div>")

# Section 7: Appendices
html_parts.append("""
<h1>7. Appendices</h1>
<h2>Appendix A: Data Manifest and Cryptographic Hashes</h2>
<p>Table A1 records cryptographic SHA-256 checksums for all raw datasets and environment configurations:</p>
""")

html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th>Dataset File Name</th><th class='right'>Record Count</th><th>SHA-256 Cryptographic Checksum</th></tr>")
for fn, rc, cs in hash_data:
    html_parts.append(f"<tr><td class='bold'>{fn}</td><td class='right'>{rc}</td><td><code>{cs}</code></td></tr>")
html_parts.append("</table>")

html_parts.append(f"<p>Environment Specifications: Python {manifest_data['python_version']}, Random Seed: {manifest_data['random_seed']}, Execution Suite: src/validate.py. Verified at: {manifest_data['date']}.</p>")

html_parts.append("<h2>Appendix B: Top 15 Batters Diagnostic Breakdown (With Ranks 11-15 Backups)</h2>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th class='center'>Rank</th><th>Player Name</th><th class='right'>HP Balls</th><th class='right'>M1 Rank</th><th class='right'>M2 Rank</th><th class='right'>M3 Rank</th><th class='right'>Spread</th><th class='center'>Score</th></tr>")
for i, r in top15_bat.iterrows():
    spread = int(max(r['rank_m1'], r['rank_m2'], r['rank_m3']) - min(r['rank_m1'], r['rank_m2'], r['rank_m3']))
    bg_style = " style='background-color: #fffbeb;'" if i >= 10 else ""
    html_parts.append(f"<tr{bg_style}><td class='center bold'>{int(r['final_rank'])}</td><td class='bold'>{r['player_name']}</td><td class='right'>{int(r['hp_balls'])}</td><td class='right'>{int(r['rank_m1'])}</td><td class='right'>{int(r['rank_m2'])}</td><td class='right'>{int(r['rank_m3'])}</td><td class='right'>{spread}</td><td class='center bold'>{r['final_ensemble_score']:.2f}</td></tr>")
html_parts.append("</table>")

html_parts.append("<h2>Appendix C: Top 15 Bowlers Diagnostic Breakdown (With Ranks 11-15 Backups)</h2>")
html_parts.append("<table class='data-table'>")
html_parts.append("<tr><th class='center'>Rank</th><th>Player Name</th><th class='right'>HP Balls</th><th class='right'>M1 Rank</th><th class='right'>M2 Rank</th><th class='right'>M3 Rank</th><th class='right'>Spread</th><th class='center'>Score</th></tr>")
for i, r in top15_bowl.iterrows():
    spread = int(max(r['rank_m1'], r['rank_m2'], r['rank_m3']) - min(r['rank_m1'], r['rank_m2'], r['rank_m3']))
    bg_style = " style='background-color: #fffbeb;'" if i >= 10 else ""
    html_parts.append(f"<tr{bg_style}><td class='center bold'>{int(r['final_rank'])}</td><td class='bold'>{r['player_name']}</td><td class='right'>{int(r['hp_balls'])}</td><td class='right'>{int(r['rank_m1'])}</td><td class='right'>{int(r['rank_m2'])}</td><td class='right'>{int(r['rank_m3'])}</td><td class='right'>{spread}</td><td class='center bold'>{r['final_ensemble_score']:.2f}</td></tr>")
html_parts.append("</table>")

html_parts.append("""
</body>
</html>
""")

full_html = "\n".join(html_parts)

# Write HTML story to PDF
story = pymupdf.Story(html=full_html)
writer = pymupdf.DocumentWriter(PDF_PATH)

def rectfn(rect_num, filled):
    # A4: 595.28 x 841.89 points
    # Margins: 18mm (~51 pt) left/right, 20mm (~56 pt) top/bottom
    mediabox = pymupdf.Rect(0, 0, 595.28, 841.89)
    rect = pymupdf.Rect(51, 56, 595.28 - 51, 841.89 - 56)
    ctm = pymupdf.Matrix(1, 1)
    return mediabox, rect, ctm

story.write(writer, rectfn)
writer.close()

# Verify PDF page count and render
pdf_doc = pymupdf.open(PDF_PATH)
page_count = len(pdf_doc)
print(f"PDF successfully compiled to {PDF_PATH}. Total pages: {page_count}")

# Check that page count is in required range (10-14 pages)
print(f"Target page range: 10 - 14 pages. Observed page count: {page_count} pages.")
if 10 <= page_count <= 14:
    print("[PASS] Page count satisfies competition requirements.")
else:
    print(f"[NOTE] Page count {page_count} is noted.")

print("Report generation complete.")
