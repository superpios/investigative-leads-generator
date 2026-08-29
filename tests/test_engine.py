import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from apply_rules import (  # noqa: E402
    apply_regola_001,
    apply_regola_002,
    apply_regola_003,
    stable_id,
    _derive_gen_date,
    WHAT_CANNOT,
    DISCLAIMER,
)


def _df(rows, cols):
    return pd.DataFrame(rows, columns=cols)


def test_regola_001_soglia():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4"],
        ["MARIO ROSSI", "E5", "2025", "inc", "a5"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id"])
    leads = apply_regola_001(df, 5, "same_calendar_year")
    assert len(leads) == 1
    assert leads[0]["rule_id"] == "REGOLA-001"
    assert leads[0]["disclaimer"] == DISCLAIMER
    assert leads[0]["what_cannot_be_claimed"] == WHAT_CANNOT


def test_regola_001_sotto_soglia():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id"])
    assert apply_regola_001(df, 5, "same_calendar_year") == []


def test_regola_001_fail_closed_colonne_mancanti():
    df = _df([["X", "E1"]], ["person_name", "entity_id"])
    assert apply_regola_001(df, 5, "same_calendar_year") == []


def test_regola_002_diretti():
    rows = [[f"AWARD", "ENT", f"2025-0{i}-01", "affidamento diretto", "s", f"r{i}"] for i in range(1, 9)]
    df = _df(rows, ["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id"])
    leads = apply_regola_002(df, 8, "12_months_rolling")
    assert len(leads) == 1
    assert leads[0]["rule_id"] == "REGOLA-002"


def test_regola_002_non_diretti():
    rows = [[f"AWARD", "ENT", f"2025-0{i}-01", "gara ordinaria", "s", f"r{i}"] for i in range(1, 9)]
    df = _df(rows, ["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id"])
    assert apply_regola_002(df, 8, "12_months_rolling") == []


def test_regola_003_cig():
    rows = [
        ["CIG1", "SUB1", "s", "t1"],
        ["CIG1", "SUB2", "s", "t2"],
    ]
    df = _df(rows, ["cig", "subject_id", "source_dataset", "source_record_id"])
    leads = apply_regola_003(df, 2, "full_dataset_coverage")
    assert len(leads) == 1
    assert leads[0]["rule_id"] == "REGOLA-003"
    assert leads[0]["period"] == "intero periodo coperto dal dataset"


def test_regola_003_fail_closed_senza_cig():
    df = _df([["SUB1", "s", "t1"]], ["subject_id", "source_dataset", "source_record_id"])
    assert apply_regola_003(df, 2, "full_dataset_coverage") == []


def test_determinismo_id_e_data():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4"],
        ["MARIO ROSSI", "E5", "2025", "inc", "a5"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id"])
    a = apply_regola_001(df, 5, "same_calendar_year")
    b = apply_regola_001(df, 5, "same_calendar_year")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    # generation_date e' assegnato da main() (determinismo via _derive_gen_date);
    # qui testiamo id e determinismo della logica di regola.
    assert a[0]["id"] == stable_id("REGOLA-001", "MARIO ROSSI|2025", "2025")


def test_derive_gen_date_senza_anno():
    leads = [{"period": "intero periodo coperto dal dataset"}]
    assert _derive_gen_date(leads) == "0000-01-01"


def test_derive_gen_date_max_anno():
    leads = [{"period": "2024"}, {"period": "2025"}]
    assert _derive_gen_date(leads) == "2025-01-01"


def test_regola_004_disabilitata():
    data = yaml.safe_load(
        open(Path(__file__).resolve().parent.parent / "rules" / "rules_v0.1.yaml", encoding="utf-8")
    )
    r004 = next(r for r in data["rules"] if r["id"] == "REGOLA-004")
    assert r004["enabled"] is False
