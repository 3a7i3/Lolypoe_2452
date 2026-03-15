from .module_status import ModuleStatus

class Dashboard:
    def __init__(self, modules):
        self.modules_status = {m.name: ModuleStatus(m.name) for m in modules}

    def update_status(self, module_name, status):
        self.modules_status[module_name].update_status(status)

    def display(self):
        for name, status_obj in self.modules_status.items():
            print(f"{name} : {status_obj.status}")
