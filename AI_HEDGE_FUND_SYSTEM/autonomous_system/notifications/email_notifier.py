class EmailNotifier:
    def __init__(self, smtp_server, from_addr, to_addr):
        self.smtp_server = smtp_server
        self.from_addr = from_addr
        self.to_addr = to_addr

    def notify(self, subject, message):
        # TODO: Implémenter l'envoi d'email réel
        print(f"[EMAIL] {subject}: {message}")
