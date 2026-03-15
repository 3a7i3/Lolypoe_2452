# signal_builder.py
class SignalBuilder:
    def __init__(self, template, params):
        self.template = template
        self.params = params

    def build(self, data):
        """
        Applique le template et les params aux données pour générer le signal.
        """
        raise NotImplementedError
