# Strategy Reports: génération de rapports de stratégie
import os
import pandas as pd
import matplotlib.pyplot as plt
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class StrategyReports:
    def generate(self, strategies, output_dir="reports", fmt="pdf"):
        os.makedirs(output_dir, exist_ok=True)
        if fmt == "pdf":
            self._generate_pdf(strategies, output_dir)
        elif fmt == "md":
            self._generate_md(strategies, output_dir)
        elif fmt == "html":
            self._generate_html(strategies, output_dir)
        else:
            raise ValueError(f"Format non supporté: {fmt}")

    def _generate_pdf(self, strategies, output_dir):
        if FPDF is None:
            print("FPDF non installé, PDF non généré.")
            return
        pdf = FPDF()
        for strat in strategies:
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Stratégie: {strat['name']}", ln=True)
            pdf.cell(200, 10, txt=f"Score: {strat['score']:.4f}", ln=True)
            pdf.cell(200, 10, txt=f"Stats: {strat['stats']}", ln=True)
            # Courbe d'équité
            plt.figure(figsize=(6,2))
            plt.plot(strat['equity'])
            plt.title(f"Equity Curve - {strat['name']}")
            plt.tight_layout()
            img_path = os.path.join(output_dir, f"equity_{strat['name']}.png")
            plt.savefig(img_path)
            plt.close()
            pdf.image(img_path, x=10, y=None, w=180)
        pdf.output(os.path.join(output_dir, "strategy_report.pdf"))

    def _generate_md(self, strategies, output_dir):
        md_path = os.path.join(output_dir, "strategy_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            for strat in strategies:
                f.write(f"# Stratégie: {strat['name']}\n")
                f.write(f"Score: {strat['score']:.4f}\n\n")
                f.write(f"Stats: {strat['stats']}\n\n")
                plt.figure(figsize=(6,2))
                plt.plot(strat['equity'])
                plt.title(f"Equity Curve - {strat['name']}")
                plt.tight_layout()
                img_path = os.path.join(output_dir, f"equity_{strat['name']}.png")
                plt.savefig(img_path)
                plt.close()
                f.write(f"![Equity Curve]({img_path})\n\n")

    def _generate_html(self, strategies, output_dir):
        html_path = os.path.join(output_dir, "strategy_report.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("<html><head><title>Strategy Report</title></head><body>")
            for strat in strategies:
                f.write(f"<h2>Stratégie: {strat['name']}</h2>")
                f.write(f"<b>Score:</b> {strat['score']:.4f}<br>")
                f.write(f"<b>Stats:</b> {strat['stats']}<br>")
                plt.figure(figsize=(6,2))
                plt.plot(strat['equity'])
                plt.title(f"Equity Curve - {strat['name']}")
                plt.tight_layout()
                img_path = os.path.join(output_dir, f"equity_{strat['name']}.png")
                plt.savefig(img_path)
                plt.close()
                f.write(f'<img src="{img_path}" width="600"><br><br>')
            f.write("</body></html>")
