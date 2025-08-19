"""
Example Django integration with envsmith
"""
# settings.py
from envsmith.integrations.django import load_envsmith
load_envsmith(schema_path="schema.yaml")
