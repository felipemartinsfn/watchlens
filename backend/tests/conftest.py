"""
conftest.py — runs before any test imports.
Sets DATABASE_URL to in-memory SQLite so the app uses it from the start.
"""
import os
# Use a shared in-memory SQLite DB so all connections see the same data
os.environ["DATABASE_URL"] = "sqlite:///file:testdb?mode=memory&cache=shared&uri=true"
os.environ["ENVIRONMENT"] = "testing"
