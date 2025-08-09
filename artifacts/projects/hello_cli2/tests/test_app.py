from hello_cli2 import app

def test_run():
    assert app.run() == "hello"
