class ErrorVisualizer:
    def __init__(self):
        self.errors = []

    def add_error(self, error):
        self.errors.append(error)

    def show_errors(self):
        for error in self.errors:
            print(f"[ERROR] {error}")
