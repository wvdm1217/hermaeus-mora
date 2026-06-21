from typer.testing import CliRunner

from hermaeus_mora.cli import app
from hermaeus_mora.config import settings

runner = CliRunner()


def test_cli_new_and_list(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    # Empty list
    result_list_empty = runner.invoke(app, ["list"])
    assert "No entries found." in result_list_empty.stdout

    # View empty
    result_view_empty = runner.invoke(app, ["view"])
    assert result_view_empty.exit_code == 1
    assert "No entries to view." in result_view_empty.stdout

    # Edit empty
    result_edit_empty = runner.invoke(app, ["edit"])
    assert result_edit_empty.exit_code == 1
    assert "No entries to edit." in result_edit_empty.stdout

    # Rm non-existent
    result_rm_empty = runner.invoke(app, ["rm", "999"], input="y\n")
    assert result_rm_empty.exit_code == 1
    assert "Entry with ID 999 not found." in result_rm_empty.stdout

    # Simulate not having an editor so it falls back to typer prompt
    monkeypatch.delenv("EDITOR", raising=False)

    # Run without subcommand (should invoke new)
    result_main = runner.invoke(app, [], input="My Main Entry\nMain content.\n")
    assert result_main.exit_code == 0

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

    # Run view specific ID
    result_view_id = runner.invoke(app, ["view", "1"])
    assert result_view_id.exit_code == 0
    assert "This is my journal content." in result_view_id.stdout

    # Run view missing ID
    result_view_missing = runner.invoke(app, ["view", "999"])
    assert result_view_missing.exit_code == 1
    assert "Entry with ID 999 not found." in result_view_missing.stdout

    # Run edit specific ID
    result_edit = runner.invoke(app, ["edit", "1"], input="Updated content\n")
    assert result_edit.exit_code == 0
    assert "Updated entry" in result_edit.stdout

    # Run edit missing ID
    result_edit_missing = runner.invoke(app, ["edit", "999"])
    assert result_edit_missing.exit_code == 1
    assert "Entry with ID 999 not found." in result_edit_missing.stdout

    # Run view again to see updated
    result_view2 = runner.invoke(app, ["view", "1"])
    assert "Updated content" in result_view2.stdout

    # Test changing ID in edit (simulate via prompt modification trick,
    # actually since the mock prompt just appends to existing file,
    # it appends another frontmatter block. Wait, this will cause error
    # because frontmatter regex parses the first block.)
    # Our prompt fallback just appends, so it won't break the original frontmatter.
    # We will test the EDITOR mock for the ID change.
    runner.invoke(app, ["edit", "1"], input="---\nbad_yaml\n")

    # Run rm
    result_rm = runner.invoke(app, ["rm", "1"], input="y\n")
    assert result_rm.exit_code == 0
    assert "Deleted entry 1" in result_rm.stdout

    # Rm failure to delete (mock storage.delete_entry to return False)
    # create new to delete
    runner.invoke(app, ["new"], input="Delete Me\ncontent\n")
    import hermaeus_mora.storage

    monkeypatch.setattr(hermaeus_mora.storage, "delete_entry", lambda x: False)
    # The list is empty because we deleted entry 1 earlier.
    result_rm_fail = runner.invoke(app, ["rm", "1"], input="y\n")
    assert "Failed to delete entry 1" in result_rm_fail.stdout


def test_cli_editor(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    # Use a dummy editor that just writes a string to the passed file
    # We'll use a python one-liner as the editor to test shlex parsing
    editor_script = (
        "import sys; p = sys.argv[-1]; "
        "open(p, 'w').write('---\\nid: 0\\ntitle: Editor\\n---\\nEditor text')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script}"')

    result = runner.invoke(app, ["new"], input="Title\n")
    assert result.exit_code == 0
    assert "Saved entry 0" in result.stdout

    result_view = runner.invoke(app, ["view", "0"])
    assert "Editor text" in result_view.stdout

    # Now edit and change the ID
    editor_script_2 = (
        "import sys; p = sys.argv[-1]; "
        "open(p, 'w').write('---\\nid: 999\\ntitle: Editor\\n---\\nEditor text 2')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script_2}"')

    result_edit = runner.invoke(app, ["edit", "0"])
    assert result_edit.exit_code == 0
    assert "Warning: ID was changed" in result_edit.stdout
    assert "Updated entry 0" in result_edit.stdout

    # Test parse error
    editor_script_err = (
        "import sys; p = sys.argv[-1]; open(p, 'w').write('No frontmatter')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script_err}"')
    result_err = runner.invoke(app, ["edit", "0"])
    assert result_err.exit_code == 1
    assert "Error updating entry" in result_err.output


def test_cli_list_with_tag(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    editor_script_idea = (
        "import sys; p = sys.argv[-1]; "
        "open(p, 'w').write('---\\nid: 1\\ntitle: Idea Entry\\n"
        "tags: [idea]\\n---\\nContent')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script_idea}"')
    runner.invoke(app, ["new"], input="Idea\n")

    editor_script_work = (
        "import sys; p = sys.argv[-1]; "
        "open(p, 'w').write('---\\nid: 2\\ntitle: Work Entry\\n"
        "tags: [work]\\n---\\nContent')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script_work}"')
    runner.invoke(app, ["new"], input="Work\n")

    # List all
    res_all = runner.invoke(app, ["list"])
    assert "Idea Entry" in res_all.stdout
    assert "Work Entry" in res_all.stdout

    # List with tag
    res_idea = runner.invoke(app, ["list", "--tag", "IDEA"])
    assert "Idea Entry" in res_idea.stdout
    assert "Work Entry" not in res_idea.stdout

    res_work = runner.invoke(app, ["list", "--tag", "work"])
    assert "Work Entry" in res_work.stdout
    assert "Idea Entry" not in res_work.stdout

    res_none = runner.invoke(app, ["list", "--tag", "notfound"])
    assert "No entries found." in res_none.stdout

    editor_script_long = (
        "import sys; p = sys.argv[-1]; "
        "open(p, 'w').write('---\\nid: 3\\ntitle: Long Tag Entry\\n"
        "tags: [very_long_tag_that_should_be_truncated]\\n---\\nContent')"
    )
    monkeypatch.setenv("EDITOR", f'python -c "{editor_script_long}"')
    runner.invoke(app, ["new"], input="Long\n")

    res_long = runner.invoke(app, ["list"])
    assert "very_long_tag_tha..." in res_long.stdout
