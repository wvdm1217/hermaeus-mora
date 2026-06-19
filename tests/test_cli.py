from typer.testing import CliRunner

from hermaeus_mora.cli import app
from hermaeus_mora.config import settings

runner = CliRunner()


def test_cli_new_and_list(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    # Simulate not having an editor so it falls back to typer prompt
    monkeypatch.delenv("EDITOR", raising=False)

    # Run new
    # Typer prompt sequences:
    # 1. Title (optional)
    # 2. Enter your journal entry content
    result = runner.invoke(
        app, ["new"], input="My Test Entry\nThis is my journal content.\n"
    )
    assert result.exit_code == 0
    assert "Saved entry" in result.stdout

    # Run list
    result_list = runner.invoke(app, ["list"])
    assert result_list.exit_code == 0
    assert "My Test Entry" in result_list.stdout

    # Run view
    result_view = runner.invoke(app, ["view"])
    assert result_view.exit_code == 0
    assert "This is my journal content." in result_view.stdout

    # Run edit (fallback prompt for edit just appends right now in our naive mock,
    # but let's just test that the command succeeds)
    result_edit = runner.invoke(app, ["edit"], input="Updated content\n")
    assert result_edit.exit_code == 0
    assert "Updated entry" in result_edit.stdout

    # Run view again to see updated
    result_view2 = runner.invoke(app, ["view"])
    assert "Updated content" in result_view2.stdout

    # Run rm
    result_rm = runner.invoke(app, ["rm", "0"], input="y\n")
    assert result_rm.exit_code == 0
    assert "Deleted entry 0" in result_rm.stdout
