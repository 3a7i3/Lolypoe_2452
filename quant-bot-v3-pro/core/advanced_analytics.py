import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from utils.logger import logger
import warnings
warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    """Module d'analyse avancee pour quant trading bot."""
    
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.model_trained = False
    
    # ===== 1. IA PREDICTIVE =====
    def predict_price(self, data, periods_ahead=5):
        """
        Predit le prix futur en utilisant RandomForest.
        
        Args:
            data: DataFrame avec OHLCV data
            periods_ahead: Nombre de periodes a predire
        
        Returns:
            list: Prix predits pour les N prochaines periodes
        """
        try:
            if len(data) < 50:
                logger.warning("Donnees insuffisantes pour prediction")
                return None
            
            # Preparer les features
            df = data.copy()
            
            # Normaliser les colonnes (majuscules ou minuscules)
            close_col = 'CLOSE' if 'CLOSE' in df.columns else 'Close'
            
            df['Return'] = df[close_col].pct_change()
            df['MA20'] = df[close_col].rolling(20).mean()
            df['MA50'] = df[close_col].rolling(50).mean()
            df['Volatility'] = df[close_col].rolling(20).std()
            df['RSI'] = self._calculate_rsi(df[close_col])
            
            # Supprimer NaN
            df = df.dropna()
            
            if len(df) < 50:
                logger.warning("Donnees insuffisantes apres preprocessing")
                return None
            
            # Features pour le modele
            feature_cols = [close_col, 'MA20', 'MA50', 'Volatility', 'RSI', 'Return']
            X = df[feature_cols].values
            y = df[close_col].shift(-1).values[:-1]
            X = X[:-1]
            
            # Normaliser
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrainer le modele
            self.model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
            self.model.fit(X_scaled, y)
            self.model_trained = True
            
            # Predictions
            last_data = X_scaled[-1].reshape(1, -1)
            predictions = []
            current_data = last_data.copy()
            
            for _ in range(periods_ahead):
                pred = self.model.predict(current_data)[0]
                predictions.append(float(pred))
                # Mettre a jour pour la prochaine prediction
                current_data = self._shift_features(current_data, pred)
            
            logger.info(f"Predictions generees: {predictions}")
            return predictions
        
        except Exception as e:
            logger.error(f"Erreur prediction: {e}")
            return None
    
    # ===== 2. DETECTION DE TENDANCE =====
    def detect_trend(self, data):
        """
        Detecte la tendance actuelle (UPTREND, DOWNTREND, SIDEWAYS).
        
        Args:
            data: DataFrame avec OHLCV data
        
        Returns:
            dict: {'trend': str, 'strength': float, 'details': dict}
        """
        try:
            if len(data) < 50:
                return {'trend': 'UNKNOWN', 'strength': 0.0, 'details': {}}
            
            df = data.copy()
            
            # Normaliser les colonnes
            close_col = 'CLOSE' if 'CLOSE' in df.columns else 'Close'
            high_col = 'HIGH' if 'HIGH' in df.columns else 'High'
            low_col = 'LOW' if 'LOW' in df.columns else 'Low'
            
            close = df[close_col].values
            
            # ADX-like calculation
            high_low = df[high_col] - df[low_col]
            high_close = abs(df[high_col] - df[close_col].shift(1))
            low_close = abs(df[low_col] - df[close_col].shift(1))
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            # Tendance simple basee sur SMA
            sma20 = df[close_col].rolling(20).mean().iloc[-1]
            sma50 = df[close_col].rolling(50).mean().iloc[-1]
            sma200 = df[close_col].rolling(200).mean().iloc[-1] if len(df) >= 200 else sma50
            
            current_price = close[-1]
            
            # Determination tendance
            if sma20 > sma50 > sma200:
                trend = "UPTREND"
                strength = (sma20 - sma200) / sma200
            elif sma20 < sma50 < sma200:
                trend = "DOWNTREND"
                strength = abs((sma20 - sma200) / sma200)
            else:
                trend = "SIDEWAYS"
                strength = 0.3
            
            # Force de tendance (0-1)
            strength = min(abs(strength) * 100, 1.0)
            
            return {
                'trend': trend,
                'strength': float(strength),
                'details': {
                    'current_price': float(current_price),
                    'sma20': float(sma20),
                    'sma50': float(sma50),
                    'sma200': float(sma200),
                    'atr': float(atr)
                }
            }
        
        except Exception as e:
            logger.error(f"Erreur detection tendance: {e}")
            return {'trend': 'UNKNOWN', 'strength': 0.0, 'details': {}}
    
    # ===== 3. ANALYSE VOLATILITE =====
    def calculate_volatility(self, data, period=20):
        """
        Calcule la volatilite (ATR et ecart-type).
        
        Args:
            data: DataFrame avec OHLCV data
            period: Periode de calcul (par defaut 20)
        
        Returns:
            dict: {'atr': float, 'std_dev': float, 'volatility_level': str}
        """
        try:
            if len(data) < period:
                return {'atr': 0, 'std_dev': 0, 'volatility_level': 'UNKNOWN'}
            
            df = data.copy()
            
            # Normaliser les colonnes
            close_col = 'CLOSE' if 'CLOSE' in df.columns else 'Close'
            high_col = 'HIGH' if 'HIGH' in df.columns else 'High'
            low_col = 'LOW' if 'LOW' in df.columns else 'Low'
            
            # ATR (Average True Range)
            high_low = df[high_col] - df[low_col]
            high_close = abs(df[high_col] - df[close_col].shift(1))
            low_close = abs(df[low_col] - df[close_col].shift(1))
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
            
            # Std Dev des returns
            returns = df[close_col].pct_change()
            std_dev = returns.rolling(period).std().iloc[-1]
            
            # Classification volatilite
            atr_pct = (atr / df[close_col].iloc[-1]) * 100
            if atr_pct > 2:
                level = "HIGH"
            elif atr_pct > 1:
                level = "MEDIUM"
            else:
                level = "LOW"
            
            return {
                'atr': float(atr),
                'std_dev': float(std_dev),
                'atr_percent': float(atr_pct),
                'volatility_level': level
            }
        
        except Exception as e:
            logger.error(f"Erreur calcul volatilite: {e}")
            return {'atr': 0, 'std_dev': 0, 'volatility_level': 'ERROR'}
    
    # ===== 4. BACKTESTING =====
    def run_backtest(self, data, signal_func, initial_capital=10000):
        """
        Effectue un backtest sur donnees historiques.
        
        Args:
            data: DataFrame avec donnees historiques
            signal_func: Fonction qui genere les signaux de trading
            initial_capital: Capital initial (par defaut 10000)
        
        Returns:
            dict: Resultats du backtest (trades, ROI, drawdown, etc.)
        """
        try:
            if len(data) < 50:
                logger.warning("Donnees historiques insuffisantes")
                return None
            
            df = data.copy().reset_index(drop=True)
            
            # Normaliser les colonnes
            close_col = 'CLOSE' if 'CLOSE' in df.columns else 'Close'
            
            capital = initial_capital
            position = False
            entry_price = 0
            trades = []
            equity = [capital]
            
            for i in range(50, len(df)):
                current_data = df.iloc[i-50:i+1]
                signal = signal_func(current_data)
                current_price = df.loc[i, close_col]
                
                # BUY
                if signal == "BUY" and not position:
                    entry_price = current_price
                    position = True
                    trades.append({'type': 'BUY', 'price': entry_price, 'index': i})
                
                # SELL
                elif signal == "SELL" and position:
                    pnl = (current_price - entry_price) * (capital / entry_price)
                    capital += pnl
                    position = False
                    trades.append({'type': 'SELL', 'price': current_price, 'index': i, 'pnl': pnl})
                
                equity.append(capital)
            
            # Metriques
            equity_array = np.array(equity)
            total_return = ((capital - initial_capital) / initial_capital) * 100
            max_equity = np.max(equity_array)
            min_equity = np.min(equity_array)
            max_drawdown = ((max_equity - min_equity) / max_equity) * 100
            
            num_trades = len([t for t in trades if t['type'] == 'SELL'])
            winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
            win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
            
            logger.info(f"Backtest: ROI={total_return:.2f}%, Trades={num_trades}, Win Rate={win_rate:.1f}%")
            
            return {
                'initial_capital': initial_capital,
                'final_capital': float(capital),
                'total_return_percent': float(total_return),
                'max_drawdown_percent': float(max_drawdown),
                'num_trades': num_trades,
                'winning_trades': winning_trades,
                'win_rate': float(win_rate),
                'trades': trades,
                'equity_curve': equity
            }
        
        except Exception as e:
            logger.error(f"Erreur backtesting: {e}")
            return None
    
    # ===== 5. AUTO OPTIMISATION =====
    def optimize_strategy(self, data, signal_func):
        """
        Optimise les parametres de strategie (SMA, RSI, MACD).
        
        Args:
            data: DataFrame avec donnees historiques
            signal_func: Fonction de signal (non utilisee, on teste differentes params)
        
        Returns:
            dict: Meilleurs parametres et performance
        """
        try:
            if len(data) < 100:
                logger.warning("Donnees insuffisantes pour optimisation")
                return None
            
            best_return = -999
            best_params = {}
            results = []
            
            # Grille de parametres a tester
            sma_shorts = [10, 15, 20, 25]
            sma_longs = [40, 50, 60, 70]
            rsi_lowers = [25, 30, 35]
            rsi_uppers = [65, 70, 75]
            
            logger.info("Optimisation en cours...")
            count = 0
            total = len(sma_shorts) * len(sma_longs) * len(rsi_lowers) * len(rsi_uppers)
            
            for sma_s in sma_shorts:
                for sma_l in sma_longs:
                    if sma_s >= sma_l:
                        continue
                    for rsi_l in rsi_lowers:
                        for rsi_u in rsi_uppers:
                            if rsi_l >= rsi_u:
                                continue
                            
                            count += 1
                            # Tester cette combinaison
                            result = self._backtest_params(data, sma_s, sma_l, rsi_l, rsi_u)
                            results.append(result)
                            
                            if result['roi'] > best_return:
                                best_return = result['roi']
                                best_params = {
                                    'sma_short': sma_s,
                                    'sma_long': sma_l,
                                    'rsi_lower': rsi_l,
                                    'rsi_upper': rsi_u
                                }
                            
                            if count % 10 == 0:
                                logger.debug(f"Optimisation: {count}/{total}")
            
            logger.info(f"Optimisation completee. Meilleurs params: {best_params}, ROI={best_return:.2f}%")
            
            return {
                'best_params': best_params,
                'best_roi': float(best_return),
                'top_results': sorted(results, key=lambda x: x['roi'], reverse=True)[:5]
            }
        
        except Exception as e:
            logger.error(f"Erreur optimisation: {e}")
            return None
    
    # ===== METHODES PRIVEES =====
    
    def _calculate_rsi(self, prices, period=14):
        """Calcule RSI."""
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _shift_features(self, current_data, pred_price):
        """Actualise les features pour la prochaine prediction."""
        return current_data  # Simpliste pour demo
    
    def _backtest_params(self, data, sma_s, sma_l, rsi_l, rsi_u):
        """Backtest avec parametres specifiques."""
        df = data.copy()
        
        # Normaliser colonnes
        close_col = 'CLOSE' if 'CLOSE' in df.columns else 'Close'
        
        df['SMA_s'] = df[close_col].rolling(sma_s).mean()
        df['SMA_l'] = df[close_col].rolling(sma_l).mean()
        df['RSI'] = self._calculate_rsi(df[close_col])
        df = df.dropna()
        
        capital = 10000
        position = False
        
        for i in range(1, len(df)):
            if df['SMA_s'].iloc[i] > df['SMA_l'].iloc[i] and df['RSI'].iloc[i] < rsi_l:
                if not position:
                    entry = df[close_col].iloc[i]
                    position = True
            elif df['SMA_s'].iloc[i] < df['SMA_l'].iloc[i] and df['RSI'].iloc[i] > rsi_u:
                if position:
                    exit_price = df[close_col].iloc[i]
                    pnl = (exit_price - entry) / entry
                    capital *= (1 + pnl)
                    position = False
        
        roi = ((capital - 10000) / 10000) * 100
        return {'sma_s': sma_s, 'sma_l': sma_l, 'rsi_l': rsi_l, 'rsi_u': rsi_u, 'roi': roi}
