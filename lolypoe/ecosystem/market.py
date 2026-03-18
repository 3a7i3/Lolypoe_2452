class ArtificialMarket:
    def __init__(self, price=100):
        self.price = price
        self.history = [price]

    def update_price(self, buy_orders, sell_orders):
        imbalance = buy_orders - sell_orders
        self.price += 0.01 * imbalance
        if self.price < 1:
            self.price = 1
        self.history.append(self.price)
        return self.price
