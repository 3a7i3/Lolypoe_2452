class ErrorLogger:
    def __init__(self, log_file="errors.log"):
        self.log_file = log_file

    def log(self, error_message):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(error_message + "\n")
