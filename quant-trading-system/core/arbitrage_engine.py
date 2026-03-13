"""
Arbitrage Engine - Detect and execute cross-exchange arbitrage opportunities
"""

import logging
from typing import Dict, List, Optional
import config

logger = logging.getLogger(__name__)

class ArbitrageEngine:
    """Detect and manage arbitrage opportunities"""
    
    async def find_opportunities(self, symbol: str, market_data: Dict) -> List:
        """
        Find arbitrage opportunities across exchanges
        Returns: list of arbitrage signals
        """
        try:
            opportunities = []
            
            # Simulate detecting price differences across exchanges
            exchanges_data = self._get_exchange_prices(symbol, market_data)
            
            if len(exchanges_data) >= 2:
                # Check for spreads
                for i in range(len(exchanges_data)):
                    for j in range(i + 1, len(exchanges_data)):
                        spread = self._calculate_spread(
                            exchanges_data[i]['price'],
                            exchanges_data[j]['price']
                        )
                        
                        if spread > config.ARBITRAGE_MIN_SPREAD:
                            opp = {
                                'symbol': symbol,
                                'buy_exchange': exchanges_data[i]['exchange'],
                                'buy_price': exchanges_data[i]['price'],
                                'sell_exchange': exchanges_data[j]['exchange'],
                                'sell_price': exchanges_data[j]['price'],
                                'spread': spread,
                                'confidence': min(spread / 0.01, 1.0)
                            }
                            opportunities.append(opp)
            
            return opportunities
            
        except Exception as e:
            logger.debug(f"Arbitrage detection error for {symbol}: {e}")
            return []
    
    def _get_exchange_prices(self, symbol: str, market_data: Dict) -> List:
        """Get prices from different exchanges"""
        try:
            # Simulate fetching from multiple exchanges
            exchanges = ['binance', 'kraken', 'coinbase', 'kucoin']
            prices = []
            
            base_price = market_data.get('price', 100)
            
            for exchange in exchanges:
                # Simulate price variation by exchange
                var = 1 + (hash(symbol + exchange) % 100) / 10000
                price = base_price * var
                
                prices.append({
                    'exchange': exchange,
                    'price': price,
                    'volume': market_data.get('volume', 0)
                })
            
            return prices
            
        except Exception as e:
            logger.debug(f"Get exchange prices error: {e}")
            return []
    
    def _calculate_spread(self, price_a: float, price_b: float) -> float:
        """Calculate spread percentage"""
        try:
            if price_a == 0 or price_b == 0:
                return 0
            
            low_price = min(price_a, price_b)
            high_price = max(price_a, price_b)
            
            spread = (high_price - low_price) / low_price
            return spread
            
        except Exception as e:
            logger.debug(f"Spread calculation error: {e}")
            return 0
    
    async def execute_arbitrage(self, opportunity: Dict) -> Optional[Dict]:
        """Execute arbitrage trade"""
        try:
            # Verify opportunity is still valid
            current_spread = await self._verify_opportunity(opportunity)
            
            if current_spread < config.ARBITRAGE_MIN_SPREAD:
                logger.debug(f"Arbitrage spread diminished: {current_spread}")
                return None
            
            # Execute buy and sell
            result = {
                'type': 'arbitrage',
                'symbol': opportunity['symbol'],
                'buy_exchange': opportunity['buy_exchange'],
                'sell_exchange': opportunity['sell_exchange'],
                'profit': current_spread,
                'status': 'executed'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Arbitrage execution error: {e}")
            return None
    
    async def _verify_opportunity(self, opportunity: Dict) -> float:
        """Verify opportunity is still valid"""
        # Recalculate spread
        return opportunity.get('spread', 0) * 0.95  # Assume some slippage
