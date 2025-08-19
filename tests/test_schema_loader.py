import tempfile
import yaml
import json
from envsmith.schema_loader import load_schema

def test_load_yaml_schema():
    d = {"FOO": {"type": "str"}}
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+") as f:
        yaml.dump(d, f)
        f.flush()
        schema = load_schema(f.name)
        assert schema == d

def test_load_json_schema():
    d = {"FOO": {"type": "str"}}
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+") as f:
        json.dump(d, f)
        f.flush()
        schema = load_schema(f.name)
        assert schema == d
