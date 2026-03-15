class SMSNotifier:
    def __init__(self, provider_api_key, phone_number):
        self.provider_api_key = provider_api_key
        self.phone_number = phone_number

    def notify(self, message):
        # TODO: Implémenter l'envoi SMS réel
        print(f"[SMS] {self.phone_number}: {message}")
