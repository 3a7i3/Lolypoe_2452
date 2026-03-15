class ResultsCollector:
    def collect(self, results):
        valid_results = []
        for r in results:
            if r is not None:
                valid_results.append(r)
        return valid_results
