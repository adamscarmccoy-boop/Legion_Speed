import json
from pathlib import Path
from datetime import datetime
from outreach_schemas import PackReport, OutreachPacket

class ReportRenderer:
    def __init__(self, output_dir: str = "./outreach"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_html_report(self, report: PackReport) -> Path:
        """Generates a branded HTML report for the prospect."""
        
        prospect_dir = self.output_dir / report.prospect.slug
        prospect_dir.mkdir(parents=True, exist_ok=True)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Legion Intelligence: Audio Audit - {report.prospect.name}</title>
            <style>
                body {{
                    font-family: 'Inter', -apple-system, sans-serif;
                    background-color: #0d0d0d;
                    color: #f1f1f1;
                    margin: 0;
                    padding: 40px;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: #1a1a1a;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                    border: 1px solid #333;
                }}
                h1 {{
                    color: #ff3366;
                    font-size: 2.5em;
                    margin-top: 0;
                }}
                h2 {{
                    color: #fff;
                    border-bottom: 1px solid #444;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }}
                .stat-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .stat-box {{
                    background: #252525;
                    padding: 20px;
                    border-radius: 6px;
                    text-align: center;
                    border-left: 4px solid #ff3366;
                }}
                .stat-box.highlight {{
                    border-left: 4px solid #00ffcc;
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .stat-label {{
                    color: #aaa;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #333;
                }}
                th {{
                    background: #252525;
                    color: #aaa;
                    text-transform: uppercase;
                    font-size: 0.85em;
                }}
                .pass {{
                    color: #00ffcc;
                    font-weight: bold;
                }}
                .fail {{
                    color: #ff3366;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Legion Intelligence — Fire Test Audit</h1>
                <p>Target: <strong>{report.prospect.name}</strong> ({report.pack_name})</p>
                <p>Analyzed at: {report.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')} (Duration: {report.fire_test_duration_ms:.2f}ms)</p>
                
                <div class="stat-grid">
                    <div class="stat-box highlight">
                        <div class="stat-value">{report.alignment_pass_rate * 100:.1f}%</div>
                        <div class="stat-label">Baseline Pass Rate</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{report.avg_alignment * 100:.1f}%</div>
                        <div class="stat-label">Avg Alignment Score</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{report.forest_verdict.top_style_match}</div>
                        <div class="stat-label">Top Style Classification</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{report.forest_verdict.style_confidence * 100:.1f}%</div>
                        <div class="stat-label">Style Confidence</div>
                    </div>
                </div>

                <h2>Key Findings</h2>
                <ul>
                    {"".join(f"<li>{finding}</li>" for finding in report.key_findings)}
                </ul>

                <h2>Segment Breakdown (Top Matches)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Segment Name</th>
                            <th>Matched Baseline</th>
                            <th>Alignment Score</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(f'''
                        <tr>
                            <td>{seg.segment_name}</td>
                            <td>{seg.matched_baseline}</td>
                            <td>{seg.alignment_score * 100:.1f}%</td>
                            <td class="{'pass' if seg.pass_threshold else 'fail'}">{'PASS' if seg.pass_threshold else 'FAIL'}</td>
                        </tr>
                        ''' for seg in report.segment_breakdown[:10])}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        output_path = prospect_dir / f"{report.prospect.slug}_audit_report.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return output_path

    def generate_pdf_report(self, html_path: Path) -> Path:
        """
        Placeholder for PDF generation.
        In a real environment, you'd use pdfkit, weasyprint, or Playwright to print the HTML to PDF.
        """
        pdf_path = html_path.with_suffix(".pdf")
        # For now, just copy the HTML and rename as a placeholder
        # TODO: integrate Playwright or pdfkit here
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write(f"PDF Placeholder for {html_path.name}. Need pdfkit or similar to render.")
        
        return pdf_path

    def render_packet(self, report: PackReport) -> tuple[Path, Path]:
        """Renders both HTML and PDF reports."""
        html_path = self.generate_html_report(report)
        pdf_path = self.generate_pdf_report(html_path)
        print(f"[Renderer] Reports generated at: {html_path.parent}")
        return html_path, pdf_path

if __name__ == "__main__":
    print("ReportRenderer module ready.")
