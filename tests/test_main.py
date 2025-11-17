from src.main import run

def test_run_executes():
    result = run()
    assert result is not None
    assert isinstance(result, dict)

