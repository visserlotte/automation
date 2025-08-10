from hello_cli4 import app


def test_run():
    assert app.run() == "hello"
