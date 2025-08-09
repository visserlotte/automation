from hello_cli3 import app

def test_run():
    assert app.run() == "hello"
