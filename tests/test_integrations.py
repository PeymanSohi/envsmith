def test_fastapi_import():
    from envsmith.integrations import fastapi
    assert hasattr(fastapi, "get_settings")

def test_django_import():
    from envsmith.integrations import django
    assert hasattr(django, "load_envsmith")
