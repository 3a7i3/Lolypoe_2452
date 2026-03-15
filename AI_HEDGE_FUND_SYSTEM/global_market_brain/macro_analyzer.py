class MacroAnalyzer:
    def analyze(self, data):
        # Analyse macroéconomique
        if data.get('recession_risk'):
            return 'recession_warning'
        if data.get('growth'):
            return 'expansion'
        return 'neutral'
