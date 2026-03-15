class ModuleInterface:
    name: str

    def is_healthy(self) -> bool:
        raise NotImplementedError

    def get_logs(self) -> list:
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def restart(self):
        raise NotImplementedError

    def run_step(self):
        raise NotImplementedError
