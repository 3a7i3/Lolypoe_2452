import pandas as pd
import matplotlib.pyplot as plt
import glob

# Interactive selection
import tkinter as tk
from tkinter import ttk

# Load latest equity curve CSV
files = glob.glob("results/equity_curves_gen_*.csv")
files.sort()
csv_path = files[-1]
df = pd.read_csv(csv_path)

markets = sorted(df['market'].unique())
ids = sorted(df['id'].unique())

# GUI
class EquityCurveSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Equity Curve Selector")
        self.geometry("400x200")
        self.market_var = tk.StringVar(value=markets[0])
        self.id_var = tk.StringVar(value=ids[0])
        ttk.Label(self, text="Marché:").pack()
        self.market_box = ttk.Combobox(self, values=markets, textvariable=self.market_var)
        self.market_box.pack()
        ttk.Label(self, text="Génome ID:").pack()
        self.id_box = ttk.Combobox(self, values=ids, textvariable=self.id_var)
        self.id_box.pack()
        ttk.Button(self, text="Afficher la courbe", command=self.plot_curve).pack(pady=10)
    def plot_curve(self):
        market = self.market_var.get()
        genome_id = self.id_var.get()
        curve = df[(df['market'] == market) & (df['id'] == genome_id)]
        plt.figure(figsize=(10,6))
        plt.plot(curve['step'], curve['capital'], label=f"{market} | id={genome_id[:6]}")
        plt.xlabel('Step')
        plt.ylabel('Capital')
        plt.title(f'Equity Curve: {market} | id={genome_id[:6]}')
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = EquityCurveSelector()
    app.mainloop()
