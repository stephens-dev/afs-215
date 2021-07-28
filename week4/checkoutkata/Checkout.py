class Checkout:
    def __init__(self):
        self.item = []
        self.price = []

    def add_item(self, item, price):
        self.item.append(item)
        self.price.append(price)
    def cal_total(self):
        total = 0
        for i in self.price:
            total += i
        return total
    def discount(self):
        total = 0
        for i in self.price:
            total += i
        return total
        dis = total - (total * .10)
        return dis