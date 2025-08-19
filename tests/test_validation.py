import pytest
from envsmith.validation import validate_env

def test_validate_env_success():
    schema = {"FOO": {"type": "str", "required": True}}
    env = {"FOO": "bar"}
    result = validate_env(env, schema)
    assert result["FOO"] == "bar"

def test_validate_env_missing():
    schema = {"FOO": {"type": "str", "required": True}}
    env = {}
    with pytest.raises(ValueError):
        validate_env(env, schema)

def test_validate_env_type_cast():
    schema = {"FOO": {"type": "int", "required": True}}
    env = {"FOO": "123"}
    result = validate_env(env, schema)
    assert result["FOO"] == 123
