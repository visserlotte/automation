from hello_cli import app

def test_run():
    assert app.run() == "hello"
