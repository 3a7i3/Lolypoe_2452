class NewsAnalyzer:
    def analyze(self, data):
        # Analyse des news
        if data.get('crash_headline'):
            return 'alert'
        if data.get('bullish_news'):
            return 'positive'
        return 'neutral'
