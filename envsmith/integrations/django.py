"""
Django integration for envsmith.

Doctest:
>>> from envsmith.integrations.django import load_envsmith
>>> callable(load_envsmith)
True
"""
def load_envsmith(schema_path: str = "schema.yaml"):
    from envsmith.core import EnvSmith
    import builtins
    settings = EnvSmith(schema_path=schema_path)
    for k, v in settings.items():
        setattr(builtins, k, v)
