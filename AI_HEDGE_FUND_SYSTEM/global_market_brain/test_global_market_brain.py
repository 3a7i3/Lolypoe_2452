from market_brain_core import GlobalMarketBrain
from crypto_analyzer import CryptoAnalyzer
from stocks_analyzer import StocksAnalyzer
from forex_analyzer import ForexAnalyzer
from macro_analyzer import MacroAnalyzer
from news_analyzer import NewsAnalyzer
from social_analyzer import SocialAnalyzer

# Instanciation des analyseurs
crypto = CryptoAnalyzer()
stocks = StocksAnalyzer()
forex = ForexAnalyzer()
macro = MacroAnalyzer()
news = NewsAnalyzer()
social = SocialAnalyzer()

# Instanciation du Global Market Brain
brain = GlobalMarketBrain()
brain.connect_modules(crypto, stocks, forex, macro, news, social)

data = {
    'crypto': {'bull_market': True},
    'stocks': {'crash_risk': True},
    'forex': {'macro_shift': True},
    'macro': {'growth': True},
    'news': {'bullish_news': True},
    'social': {'hype': True}
}

results = brain.analyze(data)
print("Résultats de l'analyse globale :")
for k, v in results.items():
    print(f"{k}: {v}")
