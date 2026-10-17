import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from click.testing import CliRunner

import switch_layout as app


@pytest.mark.parametrize(
    ("text", "expected", "direction"),
    [
        ("ghbdtn", "привет", "en-ru"),
        ("руддщ", "hello", "ru-en"),
        ("GHBDTN", "ПРИВЕТ", "en-ru"),
        ("Ghbdtn", "Привет", "en-ru"),
        ("руддщ!", "hello!", "ru-en"),
        ("123", None, None),
        ("", None, None),
        ("   ", None, None),
    ],
)
def test_convert_layout(text, expected, direction):
    if expected is None:
        with pytest.raises(ValueError):
            app.convert_layout(text)
    else:
        result = app.convert_layout(text)
        assert result == expected
        assert app.detect_direction(text) == direction


def test_format_stat():
    assert app.format_stat(2, 4, "abs") == "2"
    assert app.format_stat(2, 4, "rel") == "50.0%"
    assert app.format_stat(2, 4, None) == "2 (50.0%)"
    assert app.format_stat(0, 0, None) == "0 (0.0%)"


def test_database_stats():
    engine = create_engine("sqlite:///:memory:")
    app.Base.metadata.create_all(engine)
    with Session(engine) as session:
        assert app.get_stats(session) == (0, 0, 0)
        app.save_translation(session, "en-ru", 6)
        app.save_translation(session, "ru-en", 10)
        app.save_translation(session, "en-ru", 4)
        assert app.get_stats(session) == (2, 1, 10)


def test_stats_command_empty_database(monkeypatch, tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    app.Base.metadata.create_all(test_engine)
    monkeypatch.setattr(app, "engine", test_engine)
    result = CliRunner().invoke(app.cli, ["stats"])
    assert result.exit_code == 0
    assert "en-ru: 0 (0.0%)" in result.output
    assert "ru-en: 0 (0.0%)" in result.output
    assert "Самый длинный текст: 0 символов" in result.output


def test_convert_command_reads_and_writes_clipboard(monkeypatch, tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'cli.db'}")
    monkeypatch.setattr(app, "engine", test_engine)
    monkeypatch.setattr(app.pyperclip, "paste", lambda: "ghbdtn")
    copied = []
    monkeypatch.setattr(app.pyperclip, "copy", copied.append)
    result = CliRunner().invoke(app.cli, ["convert"])
    assert result.exit_code == 0
    assert result.output.strip() == "привет"
    assert copied == ["привет"]
    with Session(test_engine) as session:
        assert app.get_stats(session) == (1, 0, 6)
