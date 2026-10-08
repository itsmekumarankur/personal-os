import os
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory_store import MAX_FILE_BYTES, MAX_FILES, MemoryStore, MemoryToolError  # noqa: E402


@pytest.fixture
def mem(tmp_path):
    return MemoryStore(tmp_path / "mem").user("ankur")


def test_empty_memory_lists_nothing_and_creates_no_folder(tmp_path):
    store = MemoryStore(tmp_path / "mem")
    m = store.user("someone")
    assert "0B\t/memories" in m.view("/memories")
    assert m.files() == {} and m.snapshot() == ""
    assert not (tmp_path / "mem" / "someone").exists()          # a lookup does not create a folder


def test_create_and_view_with_line_numbers(mem):
    assert mem.create("/memories/profile.md", "- a\n- b\n- c") == "File created successfully at: /memories/profile.md"
    out = mem.view("/memories/profile.md")
    assert out.startswith("Here's the content of /memories/profile.md with line numbers:")
    assert "     2\t- b" in out
    assert "     3\t- c" in mem.view("/memories/profile.md", [3, 3]) and "- a" not in mem.view("/memories/profile.md", [3, -1])[60:]
    listing = mem.view("/memories")
    assert "/memories/profile.md" in listing


def test_nested_files_show_in_directory_listing(mem):
    mem.create("/memories/projects/loan.md", "- rust")
    assert "/memories/projects/" in mem.view("/memories")
    assert "/memories/projects/loan.md" in mem.view("/memories")


def test_create_rules(mem):
    mem.create("/memories/a.md", "x")
    with pytest.raises(MemoryToolError, match="already exists"):
        mem.create("/memories/a.md", "y")
    with pytest.raises(MemoryToolError, match=r"\.md or \.txt"):
        mem.create("/memories/a.py", "x")
    with pytest.raises(MemoryToolError, match="larger than"):
        mem.create("/memories/big.md", "x" * (MAX_FILE_BYTES + 1))


def test_file_count_limit(mem):
    for i in range(MAX_FILES):
        mem.create(f"/memories/f{i}.md", "x")
    with pytest.raises(MemoryToolError, match="Memory is full"):
        mem.create("/memories/one-too-many.md", "x")


@pytest.mark.parametrize("text", [
    "card 4111 1111 1111 1111",
    "my password: hunter2",
    "api_key = abcdef123456",
    "key sk-ant-abcdefghijklmnopqrstuvwxyz",
    "PAN ABCDE1234F",
    "id 1234 5678 9012",
])
def test_secret_looking_text_is_refused_everywhere(mem, text):
    with pytest.raises(MemoryToolError, match="Refused"):
        mem.create("/memories/x.md", text)
    mem.create("/memories/ok.md", "- line one\n")
    with pytest.raises(MemoryToolError, match="Refused"):
        mem.str_replace("/memories/ok.md", "line one", text)
    with pytest.raises(MemoryToolError, match="Refused"):
        mem.insert("/memories/ok.md", 0, text)


def test_ordinary_numbers_are_fine(mem):
    mem.create("/memories/ok.md", "- 16 years in fintech\n- born 1985\n- phone-free evenings after 8")


def test_str_replace(mem):
    mem.create("/memories/p.md", "- city: Pune\n- team: 5\n- team lead\n")
    mem.str_replace("/memories/p.md", "Pune", "Chennai")
    assert "Chennai" in mem.view("/memories/p.md")
    with pytest.raises(MemoryToolError, match="did not appear verbatim"):
        mem.str_replace("/memories/p.md", "Delhi", "x")
    with pytest.raises(MemoryToolError, match=r"Multiple occurrences.*lines: 2, 3"):
        mem.str_replace("/memories/p.md", "team", "squad")


def test_insert(mem):
    mem.create("/memories/p.md", "- one\n- three\n")
    mem.insert("/memories/p.md", 1, "- two")
    assert mem.files()["/memories/p.md"] == "- one\n- two\n- three\n"
    mem.insert("/memories/p.md", 0, "# top")
    assert mem.files()["/memories/p.md"].startswith("# top\n- one")
    with pytest.raises(MemoryToolError, match="Invalid `insert_line`"):
        mem.insert("/memories/p.md", 99, "x")


def test_delete_and_rename(mem):
    mem.create("/memories/projects/a.md", "x")
    mem.rename("/memories/projects/a.md", "/memories/projects/b.md")
    assert list(mem.files()) == ["/memories/projects/b.md"]
    mem.create("/memories/c.md", "x")
    with pytest.raises(MemoryToolError, match="already exists"):
        mem.rename("/memories/c.md", "/memories/projects/b.md")
    mem.delete("/memories/projects")
    assert list(mem.files()) == ["/memories/c.md"]
    with pytest.raises(MemoryToolError, match="Cannot delete"):
        mem.delete("/memories")
    with pytest.raises(MemoryToolError, match="does not exist"):
        mem.delete("/memories/nope.md")
    with pytest.raises(MemoryToolError, match=r"\.md or \.txt"):
        mem.rename("/memories/c.md", "/memories/c.sh")


@pytest.mark.parametrize("path", [
    "/memories/../outside.md",
    "/memories/../../etc/passwd",
    "/etc/passwd",
    "memories/a.md",
    "/memories-evil/a.md",
    "/memoriesX",
    "/memories/.hidden.md",
    "/memories/a/../../b.md",
    "/memories/a\x00.md",
    "",
])
def test_path_tricks_are_rejected(mem, path):
    with pytest.raises(MemoryToolError):
        mem.create(path, "x")
    with pytest.raises(MemoryToolError):
        mem.view(path)


def test_symlink_cannot_lead_outside(mem, tmp_path):
    mem.create("/memories/a.md", "x")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("top secret")
    os.symlink(outside, mem.root / "link")
    with pytest.raises(MemoryToolError, match="escape"):
        mem.view("/memories/link/secret.md")


def test_users_are_isolated(tmp_path):
    store = MemoryStore(tmp_path / "mem")
    a, b = store.user("alice"), store.user("bob")
    a.create("/memories/profile.md", "- alice likes tea")
    assert b.files() == {}
    with pytest.raises(MemoryToolError):
        b.view("/memories/profile.md")
    for bad in ["../alice", "a/b", "", "x" * 65, "a b", "a.b"]:
        with pytest.raises(ValueError):
            store.user(bad)


def test_execute_validates_commands_and_parameters(mem):
    mem.create("/memories/a.md", "x")
    with pytest.raises(MemoryToolError, match="Unknown command"):
        mem.execute({"command": "rm -rf"})
    with pytest.raises(MemoryToolError, match="Missing parameter"):
        mem.execute({"command": "create", "path": "/memories/new.md"})
    with pytest.raises(MemoryToolError, match="Bad parameter"):
        mem.execute({"command": "insert", "path": "/memories/a.md", "insert_line": "x", "insert_text": "y"})
    assert "created" in mem.execute({"command": "create", "path": "/memories/b.md", "file_text": "x"})


def test_snapshot_is_cut_at_the_limit(mem):
    for i in range(5):
        mem.create(f"/memories/f{i}.md", "line " * 100)
    snap = mem.snapshot(max_chars=900)
    assert "[memory truncated" in snap and len(snap) < 1200


def test_clear(mem):
    mem.create("/memories/a.md", "x")
    mem.clear()
    assert mem.files() == {}


def test_concurrent_writers_do_not_lose_updates(mem):
    mem.create("/memories/log.md", "- start\n")
    threads = [threading.Thread(target=lambda i=i: mem.insert("/memories/log.md", 0, f"- item {i}")) for i in range(30)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    lines = mem.files()["/memories/log.md"].strip().split("\n")
    assert len(lines) == 31
