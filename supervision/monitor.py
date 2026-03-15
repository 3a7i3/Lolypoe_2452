class Monitor:
    def __init__(self, modules):
        self.modules = modules

    def check_all(self):
        status = {}
        for module in self.modules:
            status[module.name] = "healthy" if module.is_healthy() else "error"
        return status
