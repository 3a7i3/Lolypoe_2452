"""
Market Scanner - Scan des cryptocurrencies
"""

import yfinance as yf
import pandas as pd
from config import SYMBOLS, PRIMARY_INTERVAL, MIN_VOLUME
from utils.logger import logger

def scan_market():
    """Scanne le marche pour tous les symboles."""
    market_data = {}
    
    for symbol in SYMBOLS:
        try:
            logger.info(f"Scanning {symbol}...")
            data = fetch_market_data(symbol, interval=PRIMARY_INTERVAL, period='6mo')
            
            if data is not None and not data.empty and len(data) > 0:
                # Verifier le volume
                recent_volume = data['Volume'].iloc[-1]
                if recent_volume >= MIN_VOLUME:
                    market_data[symbol] = data
                else:
                    logger.warning(f"Volume trop faible pour {symbol}: {recent_volume}")
            else:
                logger.warning(f"Pas de donnees pour {symbol}")
        
        except Exception as e:
            logger.error(f"Erreur scan {symbol}: {e}")
    
    logger.info(f"Scan complete: {len(market_data)}/{len(SYMBOLS)} symboles")
    return market_data

def fetch_market_data(symbol, interval='1h', period='6mo'):
    """Recupere les donnees de marche avec yfinance."""
    try:
        data = yf.download(
            tickers=symbol,
            interval=interval,
            period=period,
            progress=False
        )
        
        if data is None or data.empty:
            logger.warning(f"Donnees vides pour {symbol}")
            return None
        
        # Flatten MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Normaliser colonnes
        data.columns = data.columns.str.upper()
        
        # Verifier colonnes attendues
        required_cols = ['CLOSE', 'HIGH', 'LOW', 'VOLUME']
        if not all(col in data.columns for col in required_cols):
            logger.warning(f"Colonnes manquantes {symbol}: {data.columns.tolist()}")
            return None
        
        # Renommer pour consistency
        data = data.rename(columns={
            'CLOSE': 'Close',
            'HIGH': 'High',
            'LOW': 'Low',
            'OPEN': 'Open',
            'VOLUME': 'Volume'
        })
        
        return data
    
    except Exception as e:
        logger.error(f"Erreur fetching {symbol}: {e}")
        return None

def get_price_change(symbol, data, period=24):
    """Calcule le changement de prix sur N hours."""
    if len(data) < period:
        return None
    
    current_price = data['Close'].iloc[-1]
    past_price = data['Close'].iloc[-period]
    price_change = ((current_price - past_price) / past_price) * 100
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'price_change': price_change,
        'high_24h': data['High'].iloc[-period:].max(),
        'low_24h': data['Low'].iloc[-period:].min()
    }

def get_top_gainers(market_data, top_n=5):
    """Recupere les top gainers."""
    gainers = []
    for symbol, data in market_data.items():
        change = get_price_change(symbol, data, 24)
        if change:
            gainers.append(change)
    
    gainers = sorted(gainers, key=lambda x: x['price_change'], reverse=True)
    return gainers[:top_n]

def get_top_losers(market_data, top_n=5):
    """Recupere les top losers."""
    losers = []
    for symbol, data in market_data.items():
        change = get_price_change(symbol, data, 24)
        if change:
            losers.append(change)
    
    losers = sorted(losers, key=lambda x: x['price_change'])
    return losers[:top_n]
