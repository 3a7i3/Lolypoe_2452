import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='[BacktestEngine] %(message)s')

class BacktestEngine:
    def __init__(self, initial_capital=10000, fee=0.001, slippage=0.001):
        self.initial_capital = initial_capital
        self.fee = fee
        self.slippage = slippage

    # -------------------
    # Backtest simple (long only)
    # -------------------
    def run_backtest(self, df, signal_col='signal', price_col='close'):
        """
        df: DataFrame avec features et colonne 'signal'
        signal_col: 1 = buy, 0 = hold, -1 = sell
        """
        df = df.copy()
        df['position'] = df[signal_col].shift(1).fillna(0)
        df['returns'] = df[price_col].pct_change()
        df['strategy_returns'] = df['position'] * df['returns']
        # appliquer fees + slippage
        df['strategy_returns'] -= abs(df['position'].diff()) * (self.fee + self.slippage)
        df['equity'] = self.initial_capital * (1 + df['strategy_returns']).cumprod()
        return df

    # -------------------
    # Walk-Forward Backtesting (squelette)
    # -------------------
    def walk_forward_test(self, df, train_size, test_size, step_size=None, signal_func=None, price_col='close', signal_col='signal'):
        """
        Découpe l'historique en fenêtres train/test glissantes et applique le backtest sur chaque split.
        - train_size, test_size, step_size : int (nb de lignes) ou float (proportion)
        - signal_func : fonction pour générer les signaux sur la période test (optionnel)
        """
        n = len(df)
        # Conversion float -> int si besoin
        def to_int(val, total):
            return int(val * total) if isinstance(val, float) and val < 1 else int(val)
        train_n = to_int(train_size, n)
        test_n = to_int(test_size, n)
        step_n = to_int(step_size, n) if step_size is not None else test_n
        results = []
        metrics_list = []
        start = 0
        split_id = 0
        while start + train_n + test_n <= n:
            split_id += 1
            train_idx = (start, start + train_n)
            test_idx = (start + train_n, start + train_n + test_n)
            df_train = df.iloc[train_idx[0]:train_idx[1]].copy()
            df_test = df.iloc[test_idx[0]:test_idx[1]].copy()
            # Générer les signaux sur la période test si signal_func fourni
            if signal_func is not None:
                df_test[signal_col] = signal_func(df_train, df_test)
            # Sinon, on suppose que les signaux sont déjà présents
            df_bt = self.run_backtest(df_test, signal_col=signal_col, price_col=price_col)
            metrics = self.compute_metrics(df_bt)
            metrics['split'] = split_id
            metrics['train_range'] = (df_train.index[0], df_train.index[-1]) if not df_train.empty else (None, None)
            metrics['test_range'] = (df_test.index[0], df_test.index[-1]) if not df_test.empty else (None, None)
            metrics_list.append(metrics)
            results.append({
                'split': split_id,
                'train_idx': train_idx,
                'test_idx': test_idx,
                'metrics': metrics,
                'backtest_df': df_bt
            })
            start += step_n
        # Résumé global : moyenne des métriques
        if metrics_list:
            summary = {k: np.mean([m[k] for m in metrics_list if isinstance(m[k], (int, float))]) for k in metrics_list[0] if k not in ['split','train_range','test_range']}
        else:
            summary = {}
        return {'splits': results, 'metrics': metrics_list, 'summary': summary}

    # -------------------
    # Metrics
    # -------------------
    def compute_metrics(self, df):
        total_return = df['equity'].iloc[-1] / self.initial_capital - 1
        returns = df['strategy_returns']
        sharpe = returns.mean() / (returns.std() + 1e-9) * np.sqrt(252)  # annualized
        drawdown = (df['equity'].cummax() - df['equity']).max()
        max_dd = drawdown / df['equity'].cummax().max()
        return {
            'total_return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_dd
        }

    # -------------------
    # Sauvegarde CSV
    # -------------------
    def save_backtest(self, df, symbol, strategy_name):
        filename = f"{symbol}_{strategy_name}_backtest.csv"
        df.to_csv(f'backtests/{filename}', index=False)
        logging.info(f"Backtest saved: {filename}")
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'win_ratio': win_ratio
        }

    def run_backtest(self, df, strategy):
        print("[BacktestEngine] Running backtest")
        return {"PnL": 0.0}
