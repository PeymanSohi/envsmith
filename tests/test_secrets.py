from envsmith.secrets import SecretProvider

def test_secret_provider():
    s = SecretProvider()
    assert s.get_secret("foo") == "secret-value-for-foo"
    assert s.get_local_secret("bar") == "local-secret-value-for-bar"
