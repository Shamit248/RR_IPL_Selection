"""
build_complete_report.py
========================
Builds the final submission-grade Round 1 Methodology Report for
Rajasthan Royals SupeRR Selector Season 2.

Author: Shamit Bundela
Date: November 2026

Generates:
  1. report/SupeRR_Round1_Report.docx (via python-docx)
  2. report/SupeRR_Round1_Report.pdf (via pymupdf.Story)

Strictly adheres to all contest constraints, style rules, and data sources.
"""

import os
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

# Data paths
VAL_DIR = "./outputs/validation"
OUT_DIR = "./outputs"

# Banned words check
BANNED_WORDS = [
    "delve", "leverage", "robust", "holistic", "crucial",
    "it is important to note", "in today's", "this section will",
    "comprehensive", "seamless", "cutting-edge"
]

def check_banned_tokens(text, context_name=""):
    lower = text.lower()
    for b in BANNED_WORDS:
        # Check leverage only as verb (e.g., "to leverage", "leveraging", "leveraged", "leverages")
        if b == "leverage":
            if re.search(r'\b(leveraging|leveraged|leverages|to leverage)\b', lower):
                raise ValueError(f"Banned verb usage of 'leverage' found in {context_name}")
        else:
            if b in lower:
                raise ValueError(f"Banned phrase '{b}' found in {context_name}")
    if "—" in text:
        raise ValueError(f"Banned em dash '—' found in {context_name}")

print("Initializing data loaders...")

# Load core datasets
top10_bat_ipl = pd.read_csv(f"{OUT_DIR}/final_top10_batters_ipl.csv")
top10_bowl_ipl = pd.read_csv(f"{OUT_DIR}/final_top10_bowlers_ipl.csv")
top10_bat_all = pd.read_csv(f"{OUT_DIR}/final_top10_batters_all.csv")
top10_bowl_all = pd.read_csv(f"{OUT_DIR}/final_top10_bowlers_all.csv")
top15_bat = pd.read_csv(f"{OUT_DIR}/top15_ensemble_batters.csv")
top15_bowl = pd.read_csv(f"{OUT_DIR}/top15_ensemble_bowlers.csv")
auction_targets = pd.read_csv(f"{OUT_DIR}/rr_2027_auction_targets.csv")

# Load validation CSVs
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
