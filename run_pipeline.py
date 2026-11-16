"""
run_pipeline.py
================
Master Execution Runner for the Rajasthan Royals IPL 2027
Pressure-Based Recruitment Intelligence System.

Usage:
    # 1. Quick Run: Generate Final Recruitment Rankings & Report (takes ~15-20s using existing metrics):
    python run_pipeline.py --recruitment

    # 2. Verify all generated recruitment tables and outputs:
    python run_pipeline.py --verify

    # 3. Full End-to-End Pipeline (from raw CSVs to final report):
    python run_pipeline.py --all

    # 4. Run a single specific stage:
    python run_pipeline.py --step final
"""

import sys
import os
import time
import subprocess
import argparse

PIPELINE_STEPS = {
    '1_audit': {
        'name': 'Phase 1: Full Dataset Audit',
        'script': 'phase1_audit.py',
        'desc': 'Audits the 6 raw CSV datasets and checks integrity.'
    },
    '2_pressure': {
        'name': 'Phases 2-7: Match State Reconstruction & Pressure Index',
        'script': 'pipeline_p2_matchstate_pressure.py',
        'desc': 'Reconstructs match state ball-by-ball and calculates the 6-variable Pressure Index.'
    },
    '3_metrics': {
        'name': 'Phase 8: Player Performance & Reliability Modeling',
        'script': 'pipeline_p3_player_metrics.py',
        'desc': 'Computes baseline vs pressure metrics and Bayesian reliability scores.'
    },
    '4_weakness': {
        'name': 'Phase 9: Model Validation & RR 2026 Weakness Analysis',
        'script': 'pipeline_p4_model_rr_weakness.py',
        'desc': 'Trains XGBoost/LogReg validation models and diagnoses 16 RR 2026 weaknesses.'
    },
    '5_fit': {
        'name': 'Phase 10: Player-Weakness Fit Scoring',
        'script': 'pipeline_p5_fit_rankings.py',
        'desc': 'Calculates weighted fit scores for all players against RR weaknesses.'
    },
    '6_charts': {
        'name': 'Phase 11: Charts & Publication Visualizations',
        'script': 'pipeline_p6_charts_report.py',
        'desc': 'Generates 10 high-resolution analytical charts and initial markdown summary.'
    },
    '7_status': {
        'name': 'Eligibility Layer: Player Status & Activity Classification',
        'script': 'build_player_status.py',
        'desc': 'Classifies 1,217 players into ACTIVE, RETIRED, UNKNOWN and determines IPL 2027 eligibility.'
    },
    '8_dual_rankings': {
        'name': 'Dual Rankings: Historical vs IPL 2027 Eligible',
        'script': 'generate_dual_rankings.py',
        'desc': 'Generates dual historical vs active eligible top 10 rankings.'
    },
    '9_uncapped': {
        'name': 'Dedicated Uncapped Indian Recruitment Intelligence',
        'script': 'build_uncapped_recruitment_system.py',
        'desc': 'Filters and ranks high-value uncapped Indian talents solving RR gaps.'
    },
    '10_final_rankings': {
        'name': 'Final Unified Capped & Uncapped Recruitment System',
        'script': 'build_final_recruitment_rankings.py',
        'desc': 'Builds the 8 core final recruitment CSVs including Top 20, Top 10s, and Value Matrix.'
    },
    '11_master_report': {
        'name': 'Master Final Report Update',
        'script': 'update_report_master_recruitment.py',
        'desc': 'Assembles the comprehensive 900+ line master executive report with all findings.'
    },
    '12_verify': {
        'name': 'Quality Assurance & Zero-NaN Verification',
        'script': 'verify_final_tables.py',
        'desc': 'Verifies data integrity, column types, and checks for zero NaNs across all final tables.'
    }
}

RECRUITMENT_STAGES = [
    '7_status',
    '8_dual_rankings',
    '9_uncapped',
    '10_final_rankings',
    '11_master_report',
    '12_verify'
]

ALL_STAGES = list(PIPELINE_STEPS.keys())


def run_script(step_key):
    step = PIPELINE_STEPS[step_key]
    script_path = step['script']
    print("\n" + "=" * 78)
    print(f"▶ RUNNING: {step['name']}")
    print(f"  Script: {script_path}")
    print(f"  Target: {step['desc']}")
    print("=" * 78)

    if not os.path.exists(script_path):
        print(f"❌ Error: Script file '{script_path}' not found in current directory!")
        return False

    t0 = time.time()
    try:
        proc = subprocess.run([sys.executable, script_path], check=True)
        elapsed = time.time() - t0
        print(f"✅ COMPLETED: {step['name']} in {elapsed:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {step['name']} with return code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Rajasthan Royals IPL 2027 Pressure-Based Recruitment Intelligence System Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --recruitment   # Run fast recruitment & ranking pipeline (~15s)
  python run_pipeline.py --verify        # Verify all final CSV tables for zero NaNs
  python run_pipeline.py --all           # Run entire end-to-end pipeline from raw CSVs
  python run_pipeline.py --step 10_final_rankings  # Run a single step
        """
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--all', action='store_true', help="Run full end-to-end pipeline (Phases 1-12)")
    group.add_argument('--recruitment', action='store_true', help="Run recruitment & ranking pipeline (Stages 7-12)")
    group.add_argument('--verify', action='store_true', help="Run QA table verification check")
    group.add_argument('--step', type=str, choices=list(PIPELINE_STEPS.keys()), help="Run a specific pipeline step")

    args = parser.parse_args()

    # If no arguments provided, default to --recruitment with instructions
    if not (args.all or args.recruitment or args.verify or args.step):
        print("\n" + "=" * 78)
        print("RAJASTHAN ROYALS IPL 2027 RECRUITMENT INTELLIGENCE SYSTEM")
        print("=" * 78)
        print("No execution flag provided. Displaying help menu.\n")
        print("Quick Run Options:")
        print("  1. python run_pipeline.py --recruitment  (Runs recruitment ranking & reports in ~15s)")
        print("  2. python run_pipeline.py --verify       (Verifies table consistency and 0 NaNs)")
        print("  3. python run_pipeline.py --all          (Re-runs full end-to-end data processing)")
        print("  4. python run_pipeline.py --help         (View all options and available steps)\n")
        print("Running default fast recruitment & verification check now...\n")
        stages_to_run = RECRUITMENT_STAGES
    elif args.all:
        stages_to_run = ALL_STAGES
    elif args.recruitment:
        stages_to_run = RECRUITMENT_STAGES
    elif args.verify:
        stages_to_run = ['12_verify']
    elif args.step:
        stages_to_run = [args.step]

    total_start = time.time()
    for step_key in stages_to_run:
        success = run_script(step_key)
        if not success:
            print(f"\n⚠️  Pipeline halted at step: {step_key}")
            sys.exit(1)

    total_elapsed = time.time() - total_start
    print("\n" + "#" * 78)
    print(f"🎉 ALL REQUESTED PIPELINE STAGES COMPLETED SUCCESSFULLY in {total_elapsed:.1f}s!")
    print("#" * 78)
    print("\nKey Outputs Generated in 'results/':")
    print("  • results/rr_ipl2027_final_top10.csv           (Final Combined Top 10 Targets)")
    print("  • results/rr_ipl2027_top20.csv                 (Combined Top 20 Targets)")
    print("  • results/rr_ipl2027_capped_top10.csv          (Top 10 Capped Targets)")
    print("  • results/rr_ipl2027_uncapped_top10.csv        (Top 10 Uncapped Targets)")
    print("  • results/rr_ipl2027_role_targets.csv          (Exact Solutions for RR 2026 Weaknesses)")
    print("  • results/rr_ipl2027_value_upside_matrix.csv   (2x2 Value vs Upside Strategic Matrix)")
    print("  • results/final_report.md                      (Comprehensive Master Analytical Report)")
    print("=" * 78 + "\n")


if __name__ == '__main__':
    main()

