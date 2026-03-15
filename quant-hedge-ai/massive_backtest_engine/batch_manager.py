# batch_manager.py
class BatchManager:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size

    def create_batches(self, strategies):
        batches = []
        for i in range(0, len(strategies), self.batch_size):
            batch = strategies[i:i+self.batch_size]
            batches.append(batch)
        return batches
