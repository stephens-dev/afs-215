from Checkout import Checkout


def test_init_Checkout():
    Checkout()
def test_add_item():
    test = Checkout()
    test.add_item('y', 9)
    test.add_item('tea', 20)
def test_price_total():
    test = Checkout()
    test.add_item('y', 9)
    test.add_item('tea', 20)
    assert test.cal_total() == 29
def test_discount():
    test = Checkout()
    test.add_item('y', 9)
    test.add_item('tea', 20)
    assert test.discount()

