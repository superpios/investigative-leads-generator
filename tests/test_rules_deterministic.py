import yaml
from pathlib import Path


def test_rules_file_exists_and_valid():
    path = Path("rules/rules_v0.1.yaml")
    assert path.exists()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "version" in data
    assert "rules" in data
    for rule in data["rules"]:
        assert "id" in rule
        assert "note" in rule
        assert "non dimostra alcun illecito" in rule["note"].lower()
