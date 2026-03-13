import pandas as pd
from core.strategy_engine import generate_trade_signal
from utils.logger import logger

def run_backtest(data, start_idx=50):
    """Lance un backtest sur les donnees historiques."""
    try:
        results = []
        
        logger.info(f"Backtest: {len(data)} candles")
        
        for i in range(start_idx, len(data)):
            subset = data[:i]
            signal = generate_trade_signal(subset)
            
            results.append({
                'date': data.index[i],
                'signal': signal,
                'price': data['CLOSE'].iloc[i]
            })
        
        results_df = pd.DataFrame(results)
        
        # Statistiques
        buy_count = (results_df['signal'] == 'BUY').sum()
        sell_count = (results_df['signal'] == 'SELL').sum()
        hold_count = (results_df['signal'] == 'HOLD').sum()
        
        logger.info(f"Backtest results: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}")
        
        return results_df
    except Exception as e:
        logger.error(f"Erreur backtest: {e}")
        return None
