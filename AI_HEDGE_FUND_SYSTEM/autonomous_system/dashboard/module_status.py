class ModuleStatus:
    def __init__(self, module_name):
        self.name = module_name
        self.status = "healthy"  # healthy / error / stopped

    def update_status(self, new_status):
        self.status = new_status
