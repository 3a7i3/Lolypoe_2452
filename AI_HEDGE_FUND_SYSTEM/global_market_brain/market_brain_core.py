class GlobalMarketBrain:
    def __init__(self):
        self.crypto = None
        self.stocks = None
        self.forex = None
        self.macro = None
        self.news = None
        self.social = None

    def connect_modules(self, crypto, stocks, forex, macro, news, social):
        self.crypto = crypto
        self.stocks = stocks
        self.forex = forex
        self.macro = macro
        self.news = news
        self.social = social

    def analyze(self, data):
        # Fusionne les analyses de chaque module
        results = {}
        if self.crypto:
            results['crypto'] = self.crypto.analyze(data.get('crypto', {}))
        if self.stocks:
            results['stocks'] = self.stocks.analyze(data.get('stocks', {}))
        if self.forex:
            results['forex'] = self.forex.analyze(data.get('forex', {}))
        if self.macro:
            results['macro'] = self.macro.analyze(data.get('macro', {}))
        if self.news:
            results['news'] = self.news.analyze(data.get('news', {}))
        if self.social:
            results['social'] = self.social.analyze(data.get('social', {}))
        return results
