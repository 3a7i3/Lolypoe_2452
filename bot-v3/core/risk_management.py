from core.logger import logger

MAX_TRADES = 5
trade_count = 0

# Trailing Stop Config
TRAILING_STOP_PERCENT = 0.05  # 5% de trailing stop

# Dictionnaire pour tracker les positions actives
active_positions = {}  # {symbol: {'entry_price': X, 'highest_price': X, 'stop_loss': X}}

def check_risk(signal):
    """Verifie les conditions de risque."""
    global trade_count
    
    if signal == "HOLD":
        return False
    
    if trade_count >= MAX_TRADES:
        logger.warning(f"Limite de trades atteinte: {MAX_TRADES}")
        return False
    
    return True

def increment_trade_count():
    """Incremente le compteur de trades."""
    global trade_count
    trade_count += 1

def reset_trade_count():
    """Reinitialise le compteur de trades."""
    global trade_count
    trade_count = 0

def open_position(symbol, entry_price):
    """
    Enregistre une nouvelle position avec trailing stop.
    """
    global active_positions
    stop_loss = entry_price * (1 - TRAILING_STOP_PERCENT)
    active_positions[symbol] = {
        'entry_price': entry_price,
        'highest_price': entry_price,
        'stop_loss': stop_loss
    }
    logger.info(f"Position ouverte: {symbol} @ {entry_price:.2f}, Stop Loss: {stop_loss:.2f}")

def update_trailing_stop(symbol, current_price):
    """
    Met a jour le trailing stop pour une position.
    Retourne True si le stop est declenche (fermer la position).
    """
    if symbol not in active_positions:
        return False
    
    position = active_positions[symbol]
    
    # Si nouveau high, relever le stop loss
    if current_price > position['highest_price']:
        position['highest_price'] = current_price
        new_stop = current_price * (1 - TRAILING_STOP_PERCENT)
        position['stop_loss'] = max(position['stop_loss'], new_stop)
        logger.debug(f"{symbol} - Nouveau high: {current_price:.2f}, Stop: {position['stop_loss']:.2f}")
    
    # Verifier si le prix est sous le stop loss
    if current_price <= position['stop_loss']:
        logger.warning(f"TRAILING STOP declenche: {symbol} @ {current_price:.2f}, Stop: {position['stop_loss']:.2f}")
        close_position(symbol)
        return True
    
    return False

def close_position(symbol):
    """Ferme une position."""
    global active_positions
    if symbol in active_positions:
        profit = ((active_positions[symbol]['highest_price'] - active_positions[symbol]['entry_price']) / 
                  active_positions[symbol]['entry_price'] * 100)
        logger.info(f"Position fermee: {symbol}, Profit: {profit:.2f}%")
        del active_positions[symbol]

def get_position_info(symbol):
    """Retourne les infos d'une position."""
    return active_positions.get(symbol, None)

def get_all_positions():
    """Retourne toutes les positions actives."""
    return active_positions.copy()
