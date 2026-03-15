class SocialAnalyzer:
    def analyze(self, data):
        # Analyse des tendances sociales
        if data.get('panic'):
            return 'panic_detected'
        if data.get('hype'):
            return 'hype_detected'
        return 'calm'
