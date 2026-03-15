class DashboardPanel:
    def __init__(self, modules):
        self.modules = modules

    def display(self):
        for module in self.modules:
            print(f"{module.name}: {module.status}")
