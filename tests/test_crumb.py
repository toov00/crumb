import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

@pytest.fixture(autouse=True)
def isolated_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CRUMB_DIR", str(tmp_path))
    import crumb
    monkeypatch.setattr(crumb, "DATA_DIR", tmp_path)
    monkeypatch.setattr(crumb, "DATA_FILE", tmp_path / "crumbs.json")
    return tmp_path

import crumb as c_mod

def test_load_empty(isolated_data_dir):
    assert c_mod.load() == []

def test_save_and_load(isolated_data_dir):
    crumbs = [{"id": 1, "content": "echo hi", "description": "", "tags": [], "created_at": "2026-03-14T10:00:00"}]
    c_mod.save(crumbs)
    assert c_mod.load() == crumbs

def test_next_id_empty():
    assert c_mod.next_id([]) == 1

def test_next_id_existing():
    crumbs = [{"id": 3}]
    assert c_mod.next_id(crumbs) == 4

def run_cmd(args: list[str]):
    parser = c_mod.build_parser()
    parsed = parser.parse_args(args)
    parsed.func(parsed)

def test_add_basic(isolated_data_dir, capsys):
    run_cmd(["add", "docker ps -a"])
    crumbs = c_mod.load()
    assert len(crumbs) == 1
    assert crumbs[0]["content"] == "docker ps -a"
    assert crumbs[0]["tags"] == []
    assert crumbs[0]["description"] == ""

def test_add_with_tags(isolated_data_dir):
    run_cmd(["add", "ls -la", "--tag", "shell", "unix"])
    crumbs = c_mod.load()
    assert crumbs[0]["tags"] == ["shell", "unix"]

def test_add_with_desc(isolated_data_dir):
    run_cmd(["add", "ls -la", "--desc", "list all files"])
    crumbs = c_mod.load()
    assert crumbs[0]["description"] == "list all files"

def test_add_strips_hash_from_tags(isolated_data_dir):
    run_cmd(["add", "ls", "--tag", "#shell"])
    crumbs = c_mod.load()
    assert crumbs[0]["tags"] == ["shell"]

def test_add_increments_id(isolated_data_dir):
    run_cmd(["add", "echo one"])
    run_cmd(["add", "echo two"])
    crumbs = c_mod.load()
    assert crumbs[0]["id"] == 1
    assert crumbs[1]["id"] == 2

def test_search_finds_match(isolated_data_dir, capsys):
    run_cmd(["add", "docker ps -a", "--tag", "docker"])
    run_cmd(["add", "git log"])
    run_cmd(["search", "docker"])
    out = capsys.readouterr().out
    assert "docker ps -a" in out
    assert "git log" not in out

def test_search_matches_tags(isolated_data_dir, capsys):
    run_cmd(["add", "ffmpeg -i in out", "--tag", "media"])
    run_cmd(["search", "media"])
    out = capsys.readouterr().out
    assert "ffmpeg" in out

def test_search_matches_desc(isolated_data_dir, capsys):
    run_cmd(["add", "ls -la", "--desc", "list hidden files"])
    run_cmd(["search", "hidden"])
    out = capsys.readouterr().out
    assert "ls -la" in out

def test_search_no_results(isolated_data_dir, capsys):
    run_cmd(["add", "echo hello"])
    run_cmd(["search", "zzznomatch"])
    out = capsys.readouterr().out
    assert "No crumbs found" in out

def test_search_case_insensitive(isolated_data_dir, capsys):
    run_cmd(["add", "Docker ps -a"])
    run_cmd(["search", "docker"])
    out = capsys.readouterr().out
    assert "Docker ps -a" in out

def test_list_empty(isolated_data_dir, capsys):
    run_cmd(["list"])
    out = capsys.readouterr().out
    assert "No crumbs yet" in out

def test_list_all(isolated_data_dir, capsys):
    run_cmd(["add", "cmd one"])
    run_cmd(["add", "cmd two"])
    run_cmd(["list"])
    out = capsys.readouterr().out
    assert "cmd one" in out
    assert "cmd two" in out

def test_list_filter_tag(isolated_data_dir, capsys):
    run_cmd(["add", "git log", "--tag", "git"])
    run_cmd(["add", "docker ps", "--tag", "docker"])
    run_cmd(["list", "--tag", "git"])
    out = capsys.readouterr().out
    assert "git log" in out
    assert "docker ps" not in out

def test_list_n(isolated_data_dir, capsys):
    for i in range(5):
        run_cmd(["add", f"cmd {i}"])
    run_cmd(["list", "-n", "2"])
    out = capsys.readouterr().out
    assert out.count("[") == 2

def test_delete_existing(isolated_data_dir, capsys):
    run_cmd(["add", "to delete"])
    run_cmd(["delete", "1"])
    assert c_mod.load() == []
    out = capsys.readouterr().out
    assert "deleted" in out

def test_delete_nonexistent(isolated_data_dir, capsys):
    with pytest.raises(SystemExit):
        run_cmd(["delete", "999"])

def test_tags_output(isolated_data_dir, capsys):
    run_cmd(["add", "cmd", "--tag", "shell"])
    run_cmd(["add", "cmd2", "--tag", "shell"])
    run_cmd(["add", "cmd3", "--tag", "git"])
    run_cmd(["tags"])
    out = capsys.readouterr().out
    assert "#shell" in out
    assert "#git" in out
    assert "2" in out

def test_tags_empty(isolated_data_dir, capsys):
    run_cmd(["tags"])
    out = capsys.readouterr().out
    assert "No tags" in out

def test_export_stdout(isolated_data_dir, capsys):
    run_cmd(["add", "echo hi", "--tag", "shell"])
    run_cmd(["export"])
    out = capsys.readouterr().out
    assert "echo hi" in out
    assert "#shell" in out
    assert "```" in out

def test_export_file(isolated_data_dir, tmp_path):
    run_cmd(["add", "echo hi"])
    out_file = str(tmp_path / "out.md")
    run_cmd(["export", "--out", out_file])
    content = Path(out_file).read_text()
    assert "echo hi" in content
    assert "crumb export" in content
    