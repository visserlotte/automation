import model_selector as ms


def test_choose_cheap():
    assert ms.choose_model("cheap") in ms.PRICES
