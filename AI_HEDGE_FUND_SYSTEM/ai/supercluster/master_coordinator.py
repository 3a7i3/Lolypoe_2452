class MasterCoordinator:
    def __init__(self, nodes):
        self.nodes = nodes

    def distribute_research(self, df):
        results = []
        for node in self.nodes:
            res = node.run_research(df)
            results.extend(res)
        return results
