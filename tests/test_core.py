import os
import pytest
from envsmith.core import EnvSmith

def test_envsmith_load(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    schema = {"FOO": {"type": "str", "required": True}}
    s = EnvSmith(schema=schema)
    assert s["FOO"] == "bar"

def test_envsmith_export():
    schema = {"FOO": {"type": "str", "required": True}}
    env = {"FOO": "bar"}
    s = EnvSmith(schema=schema, env=env)
    assert "FOO" in s.export("json")
    assert "FOO" in s.export("yaml")
