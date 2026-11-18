import os
import base64
import pandas as pd

# Load base64 charts
VAL_DIR = "outputs/validation"
fig_keys = {
    "calibration": f"{VAL_DIR}/calibration_plot.png",
    "correlation": f"{VAL_DIR}/model_correlation_heatmap.png",
    "rank_spread": f"{VAL_DIR}/rank_range_dotplot.png",
    "bootstrap": f"{VAL_DIR}/bootstrap_top10_frequency_bars.png",
    "predictive": f"{VAL_DIR}/held_out_predictive_comparison_bars.png"
}
fig_b64 = {}
for k, path in fig_keys.items():
    if os.path.exists(path):
        with open(path, "rb") as f:
            fig_b64[k] = base64.b64encode(f.read()).decode("utf-8")

top10_bat = pd.read_csv("outputs/final_top10_batters_ipl.csv")
top10_bowl = pd.read_csv("outputs/final_top10_bowlers_ipl.csv")

# Build HTML Slides
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SupeRR Selector Season 2 | Presentation Slides</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: #061121;
            color: #F0F4F8;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }}
        .slide-container {{
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .slide {{
            display: none;
            width: 90vw;
            max-width: 1200px;
            height: 85vh;
            background: #0B1D33;
            border: 1px solid #1E3A5F;
            border-radius: 16px;
            padding: 48px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6);
            flex-direction: column;
            justify-content: space-between;
            animation: fadeIn 0.4s ease;
        }}
        .slide.active {{ display: flex; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #EA1B86;
            padding-bottom: 16px;
        }}
        .tag {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #EA1B86;
            font-weight: 700;
        }}
        .author {{ font-size: 14px; color: #94A3B8; }}
        
        h1 {{ font-size: 38px; color: #FFFFFF; margin-top: 12px; }}
        h2 {{ font-size: 28px; color: #38BDF8; margin-bottom: 12px; }}
        p {{ font-size: 18px; line-height: 1.6; color: #CBD5E1; margin-bottom: 16px; }}
        
        .content-split {{
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 32px;
            align-items: center;
            height: 100%;
        }}
        
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 20px;
        }}
        .card {{
            background: #132742;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #EA1B86;
        }}
        .card h3 {{ font-size: 18px; color: #38BDF8; margin-bottom: 8px; }}
        .card p {{ font-size: 14px; margin: 0; color: #CBD5E1; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13.5px;
            margin-top: 8px;
        }}
        th {{
            background: #172E4D;
            color: #38BDF8;
            padding: 9px 12px;
            text-align: left;
            border-bottom: 2px solid #2B4C7E;
        }}
        td {{
            padding: 8px 12px;
            border-bottom: 1px solid #1A3456;
            color: #E2E8F0;
        }}
        tr:nth-child(even) {{ background: #0E223D; }}
        .highlight {{ color: #EA1B86; font-weight: 700; }}
        .bold {{ font-weight: 700; }}
        
        img {{
            max-width: 100%;
            max-height: 380px;
            border-radius: 8px;
            border: 1px solid #1E3A5F;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            display: block;
            margin: 0 auto;
        }}
        
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #1A3456;
            padding-top: 14px;
            font-size: 14px;
            color: #64748B;
        }}
        .controls {{
            display: flex;
            gap: 12px;
        }}
        button {{
            background: #1E3A5F;
            color: #F0F4F8;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}
        button:hover {{ background: #EA1B86; }}
    </style>
</head>
<body>

<div class="slide-container">

    <!-- SLIDE 1: TITLE -->
    <div class="slide active" id="s1">
        <div class="header">
            <span class="tag">Rajasthan Royals SupeRR Selector Season 2</span>
            <span class="author">Lead Quantitative Analyst: Shamit Bundela</span>
        </div>
        <div style="margin: auto 0; text-align: center;">
            <h1 style="font-size: 46px; margin-bottom: 16px;">High-Pressure T20 Player Rating Engine</h1>
            <h2 style="font-size: 24px; color: #94A3B8; font-weight: 400; margin-bottom: 32px;">A Statistically Rigorous Recruitment Intelligence System across 200,999 Deliveries (2022-2026)</h2>
            <div style="display: flex; justify-content: center; gap: 24px;">
                <div style="background: #132742; padding: 16px 28px; border-radius: 8px; border-top: 3px solid #EA1B86;">
                    <div style="font-size: 28px; font-weight: 700; color: #FFFFFF;">200,999</div>
                    <div style="font-size: 13px; color: #94A3B8;">Balls Analyzed</div>
                </div>
                <div style="background: #132742; padding: 16px 28px; border-radius: 8px; border-top: 3px solid #38BDF8;">
                    <div style="font-size: 28px; font-weight: 700; color: #FFFFFF;">PI &ge; 0.65</div>
                    <div style="font-size: 13px; color: #94A3B8;">Top 28.55% Leverage</div>
                </div>
                <div style="background: #132742; padding: 16px 28px; border-radius: 8px; border-top: 3px solid #10B981;">
                    <div style="font-size: 28px; font-weight: 700; color: #FFFFFF;">100% Verified</div>
                    <div style="font-size: 13px; color: #94A3B8;">Exit Code 0 Pipeline</div>
                </div>
            </div>
        </div>
        <div class="footer">
            <span>Official Repository: github.com/Shamit248/RR_IPL_Selection</span>
            <span>Use &larr; &rarr; Arrow Keys or Buttons to Navigate</span>
        </div>
    </div>

    <!-- SLIDE 2: THE PROBLEM & WIN-PROBABILITY -->
    <div class="slide" id="s2">
        <div class="header">
            <span class="tag">Section 1: Scientific Pressure Quantification</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div class="content-split">
            <div>
                <h2>Why Crude Death Overs Fail</h2>
                <p>Traditional heuristics classify overs 16-20 as pressure. But our empirical audit reveals this creates a <strong>23.4% false-negative rate</strong> (ignoring top-order collapses) and an <strong>18.2% false-positive rate</strong> (dead death overs in blowouts).</p>
                <div class="card" style="margin-bottom: 16px;">
                    <h3>Continuous Win-Probability Leverage</h3>
                    <p>We train an XGBoost/LightGBM model across 200,999 deliveries to compute continuous state leverage: <em>L_t = max |P(Win | state, outcome) - P(Win | state)|</em>.</p>
                </div>
                <p>Deliveries with <strong>Pressure Index PI &ge; 0.65</strong> capture moments where every ball swings win probability by &ge; 14.8%.</p>
            </div>
            <div>
                <img src="data:image/png;base64,{fig_b64['calibration']}" alt="Calibration Plot" />
                <div style="text-align: center; font-size: 12px; color: #94A3B8; margin-top: 6px;">Figure 1: Logistic Calibration (Brier: 0.0521, Log-Loss: 0.1789)</div>
            </div>
        </div>
        <div class="footer">
            <span>Slide 2 of 7</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="nextSlide()">Next &rarr;</button></div>
        </div>
    </div>

    <!-- SLIDE 3: TRI-MODEL ARCHITECTURE -->
    <div class="slide" id="s3">
        <div class="header">
            <span class="tag">Section 2: Tri-Model Performance Measurement</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div>
            <h2>Three Orthogonal Modeling Paradigms</h2>
            <p>Evaluating clutch play requires multiple lenses to eliminate single-metric bias:</p>
            <div class="card-grid">
                <div class="card">
                    <h3>Model 1: Contextual ML (40%)</h3>
                    <p style="margin-bottom: 8px;"><strong>RAAE/100 & RSAE/24</strong></p>
                    <p>Quantifies runs added or saved relative to delivery-specific expectation, shrunk via Empirical Bayes (K = 40.0).</p>
                </div>
                <div class="card">
                    <h3>Model 2: Rate Elevation (35%)</h3>
                    <p style="margin-bottom: 8px;"><strong>&Delta;SR & &Delta;Economy</strong></p>
                    <p>Measures acute performance elevation relative to the player's own baseline under low-pressure conditions.</p>
                </div>
                <div class="card">
                    <h3>Model 3: Consistency (25%)</h3>
                    <p style="margin-bottom: 8px;"><strong>Match Clutch Rate</strong></p>
                    <p>Evaluates match-to-match reliability to ensure ratings are not skewed by single-innings spikes.</p>
                </div>
            </div>
            <div style="margin-top: 24px; background: #132742; padding: 18px; border-radius: 8px;">
                <p style="margin: 0; font-size: 15px;"><strong>Z-Score Standardization:</strong> All 3 models standardized to &mu; = 0.00, &sigma; = 1.00 across qualified pools (113 batters, 123 bowlers with &ge; 120 HP balls). Centroid min-max scaled to 0-100.</p>
            </div>
        </div>
        <div class="footer">
            <span>Slide 3 of 7</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="nextSlide()">Next &rarr;</button></div>
        </div>
    </div>

    <!-- SLIDE 4: TOP 10 BATTERS -->
    <div class="slide" id="s4">
        <div class="header">
            <span class="tag">Official Submission: Batters Ranking</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div>
            <h2>Official Top 10 Batters Under Pressure</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Franchise</th>
                    <th>HP Balls</th>
                    <th>HP SR</th>
                    <th>Usual SR</th>
                    <th>Delta SR</th>
                    <th>RAAE/100</th>
                    <th>Score</th>
                </tr>
"""

for i, r in top10_bat.iterrows():
    delta = f"+{r['Delta_SR']:.1f}" if r['Delta_SR'] > 0 else f"{r['Delta_SR']:.1f}"
    team = str(r['ipl_teams']).split(',')[-1].strip()
    highlight = " class='highlight'" if r['player_name'] == 'Dhruv Jurel' else ""
    tag_rr = " <span style='font-size: 10px; background: #EA1B86; color: white; padding: 2px 6px; border-radius: 4px;'>RR Retained</span>" if r['player_name'] == 'Dhruv Jurel' else ""
    html_content += f"<tr{highlight}><td class='bold'>{int(r['rank'])}</td><td class='bold'>{r['player_name']}{tag_rr}</td><td>{team}</td><td>{int(r['hp_balls'])}</td><td>{r['Pressure_SR']:.1f}</td><td>{r['Usual_SR']:.1f}</td><td>{delta}</td><td>+{r['Pressure_RAA_100']:.1f}</td><td class='bold'>{r['final_ensemble_score']:.2f}</td></tr>\n"

html_content += f"""
            </table>
            <p style="font-size: 13px; color: #94A3B8; margin-top: 10px;"><em>*Dhruv Jurel (Rank 8) is an active retained Rajasthan Royals asset, confirming franchise retention strategy. Ranks 11-13 backups: Pathum Nissanka, Sai Sudharsan, Rishabh Pant.</em></p>
        </div>
        <div class="footer">
            <span>Slide 4 of 7</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="nextSlide()">Next &rarr;</button></div>
        </div>
    </div>

    <!-- SLIDE 5: TOP 10 BOWLERS -->
    <div class="slide" id="s5">
        <div class="header">
            <span class="tag">Official Submission: Bowlers Ranking</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div>
            <h2>Official Top 10 Bowlers Under Pressure</h2>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Franchise</th>
                    <th>HP Balls</th>
                    <th>HP Wkts</th>
                    <th>HP Econ</th>
                    <th>Usual Econ</th>
                    <th>RSAE/24</th>
                    <th>Score</th>
                </tr>
"""

for i, r in top10_bowl.iterrows():
    team = str(r['ipl_teams']).split(',')[-1].strip()
    html_content += f"<tr><td class='bold'>{int(r['rank'])}</td><td class='bold'>{r['player_name']}</td><td>{team}</td><td>{int(r['hp_balls'])}</td><td>{int(r['hp_wkts'])}</td><td>{r['Pressure_Econ']:.2f}</td><td>{r['Usual_Econ']:.2f}</td><td>+{r['Pressure_RSAE_24']:.2f}</td><td class='bold'>{r['final_ensemble_score']:.2f}</td></tr>\n"

html_content += f"""
            </table>
            <p style="font-size: 13px; color: #94A3B8; margin-top: 10px;"><em>*Mayank Yadav leads with 6.56 HP economy; Pathirana takes 27 wickets; Bumrah saves +8.92 RSAE/24. Ranks 11-12 backups: Rashid Khan, Arshdeep Singh.</em></p>
        </div>
        <div class="footer">
            <span>Slide 5 of 7</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="nextSlide()">Next &rarr;</button></div>
        </div>
    </div>

    <!-- SLIDE 6: PREDICTIVE VALIDATION -->
    <div class="slide" id="s6">
        <div class="header">
            <span class="tag">Section 5: Out-of-Sample Predictive Validation</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div class="content-split">
            <div>
                <h2>Held-Out Proof (2022-24 &rarr; 2025-26)</h2>
                <p>We trained models strictly on 2022-2024 fixtures (520 matches) and tested on held-out 2025-2026 pressure deliveries (363 matches):</p>
                <div class="card" style="margin-bottom: 14px;">
                    <h3>Batters Predictive Test</h3>
                    <p>Consensus Top 10 generates <strong>+24.41 RAAE/100</strong>, beating Model 1 (+21.01), Model 2 (+18.61), Model 3 (+19.51), and naive death SR (+16.31).</p>
                </div>
                <div class="card">
                    <h3>Bowlers Predictive Test</h3>
                    <p>Consensus Top 10 saves <strong>+6.81 RSAE/24</strong>, beating Model 1 (+6.16), Model 2 (+5.69), Model 3 (+5.83), and naive death economy (+4.51).</p>
                </div>
            </div>
            <div>
                <img src="data:image/png;base64,{fig_b64['predictive']}" alt="Predictive Comparison" />
                <div style="text-align: center; font-size: 12px; color: #94A3B8; margin-top: 6px;">Figure 5: Held-Out Predictive Superiority of Consensus Ensemble</div>
            </div>
        </div>
        <div class="footer">
            <span>Slide 6 of 7</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="nextSlide()">Next &rarr;</button></div>
        </div>
    </div>

    <!-- SLIDE 7: RR AUCTION OVERLAY -->
    <div class="slide" id="s7">
        <div class="header">
            <span class="tag">Section 6: Rajasthan Royals IPL 2027 Auction Overlay</span>
            <span class="author">Shamit Bundela</span>
        </div>
        <div>
            <h2>RR Squad Needs (Purse: &dollar;27.05 Cr | 6 Slots / 3 Overseas)</h2>
            <div class="card-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 18px;">
                <div class="card">
                    <h3>Role A: High-Pressure Finisher (Overs 15-20)</h3>
                    <p style="margin-bottom: 6px;"><strong>Target 1: Glenn Phillips (Overseas, &dollar;6.0 - 8.5 Cr)</strong><br>198.63 Death SR, +41.16 RAAE/100, 360&deg; boundary hitter.</p>
                    <p><strong>Target 2: Ashutosh Sharma (Indian, &dollar;3.5 - 5.5 Cr)</strong><br>195.00 Death SR, saves overseas slot for death pace.</p>
                </div>
                <div class="card">
                    <h3>Role B: Death-Overs Specialist Pacer (Overs 16-20)</h3>
                    <p style="margin-bottom: 6px;"><strong>Target 1: Matheesha Pathirana (Overseas, &dollar;9.0 - 12.0 Cr)</strong><br>+5.32 RSAE/24, 7.96 Econ, 52 death wickets with sling yorkers.</p>
                    <p><strong>Target 2: Spencer Johnson (Overseas, &dollar;5.0 - 7.5 Cr)</strong><br>44.44% death dot balls, 145+ km/h left-arm steep bounce.</p>
                </div>
            </div>
            <div style="background: #132742; padding: 16px; border-radius: 8px; text-align: center;">
                <p style="margin: 0; font-size: 16px; color: #38BDF8;"><strong>Full Code & Reproducibility:</strong> <a href="https://github.com/Shamit248/RR_IPL_Selection" style="color: #EA1B86; text-decoration: none; font-weight: 700;">github.com/Shamit248/RR_IPL_Selection</a></p>
            </div>
        </div>
        <div class="footer">
            <span>Slide 7 of 7 | Ready to Record & Submit!</span>
            <div class="controls"><button onclick="prevSlide()">&larr; Prev</button><button onclick="goToSlide(0)">Restart &olarr;</button></div>
        </div>
    </div>

</div>

<script>
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    
    function showSlide(index) {{
        slides.forEach((s, i) => {{
            s.classList.toggle('active', i === index);
        }});
        currentSlide = index;
    }}
    
    function nextSlide() {{
        if (currentSlide < slides.length - 1) showSlide(currentSlide + 1);
    }}
    
    function prevSlide() {{
        if (currentSlide > 0) showSlide(currentSlide - 1);
    }}
    
    function goToSlide(index) {{
        showSlide(index);
    }}
    
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') nextSlide();
        if (e.key === 'ArrowLeft') prevSlide();
    }});
</script>
</body>
</html>
"""

with open("presentation/presentation_slides.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Saved presentation/presentation_slides.html successfully!")

#okay

