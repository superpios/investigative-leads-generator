import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import apply_rules  # noqa: E402
from apply_rules import (  # noqa: E402
    apply_regola_001,
    apply_regola_002,
    apply_regola_003,
    stable_id,
    WHAT_CANNOT,
    DISCLAIMER,
)

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "rules" / "rules_v0.1.yaml"


def _df(rows, cols):
    return pd.DataFrame(rows, columns=cols)


def _run_main(input_dir, output_dir, rules_path):
    old = sys.argv
    sys.argv = [
        "apply_rules.py",
        "--input", str(input_dir),
        "--output", str(output_dir),
        "--rules", str(rules_path),
    ]
    try:
        apply_rules.main()
    finally:
        sys.argv = old


def test_regola_001_soglia():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4"],
        ["MARIO ROSSI", "E5", "2025", "inc", "a5"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id"])
    leads, _ = apply_regola_001(df, 5)
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
    leads, _ = apply_regola_001(df, 5)
    assert leads == []


def test_regola_001_fail_closed_colonne_mancanti():
    df = _df([["X", "E1"]], ["person_name", "entity_id"])
    leads, _ = apply_regola_001(df, 5)
    assert leads == []


def test_regola_001_source_url_presente():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1", "http://s/a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2", "http://s/a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3", "http://s/a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4", "http://s/a4"],
        ["MARIO ROSSI", "E5", "2025", "inc", "a5", "http://s/a5"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id", "source_url"])
    leads, _ = apply_regola_001(df, 5)
    assert leads[0]["sources"][0]["source_url"] == "http://s/a1"


def test_regola_002_diretti():
    rows = [[f"AWARD", "ENT", f"2025-0{i}-01", "affidamento diretto", "s", f"r{i}"] for i in range(1, 9)]
    df = _df(rows, ["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id"])
    leads, _ = apply_regola_002(df, 8)
    assert len(leads) == 1
    assert leads[0]["rule_id"] == "REGOLA-002"
    assert ".." in leads[0]["period"]  # finestra 12 mesi mobili


def test_regola_002_finestra_esclude_dato_antico():
    rows = [
        ["AWARD", "ENT", "2020-01-01", "affidamento diretto", "s", "rold"],
        ["AWARD", "ENT", "2025-08-01", "affidamento diretto", "s", "r1"],
        ["AWARD", "ENT", "2025-08-05", "affidamento diretto", "s", "r2"],
        ["AWARD", "ENT", "2025-08-10", "affidamento diretto", "s", "r3"],
        ["AWARD", "ENT", "2025-08-15", "affidamento diretto", "s", "r4"],
        ["AWARD", "ENT", "2025-08-20", "affidamento diretto", "s", "r5"],
        ["AWARD", "ENT", "2025-08-25", "affidamento diretto", "s", "r6"],
        ["AWARD", "ENT", "2025-09-01", "affidamento diretto", "s", "r7"],
    ]
    df = _df(rows, ["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id"])
    leads, _ = apply_regola_002(df, 8)
    # il dato 2020 è fuori dalla finestra di 12 mesi => solo 7 nel periodo => 0 lead
    assert leads == []


def test_regola_002_non_diretti():
    rows = [[f"AWARD", "ENT", f"2025-0{i}-01", "gara ordinaria", "s", f"r{i}"] for i in range(1, 9)]
    df = _df(rows, ["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id"])
    leads, _ = apply_regola_002(df, 8)
    assert leads == []


def test_regola_003_cig_senza_spiegazione():
    rows = [
        ["CIG1", "SUB1", "s", "t1", ""],
        ["CIG1", "SUB2", "s", "t2", ""],
    ]
    df = _df(rows, ["cig", "subject_id", "source_dataset", "source_record_id", "explanation"])
    leads, _ = apply_regola_003(df, 2)
    assert len(leads) == 1
    assert leads[0]["rule_id"] == "REGOLA-003"
    assert leads[0]["period"] == "intero periodo coperto dal dataset"


def test_regola_003_cig_con_spiegazione_non_segnala():
    rows = [
        ["CIG1", "SUB1", "s", "t1", "collegamento spiegato nella fonte"],
        ["CIG1", "SUB2", "s", "t2", ""],
    ]
    df = _df(rows, ["cig", "subject_id", "source_dataset", "source_record_id", "explanation"])
    leads, _ = apply_regola_003(df, 2)
    assert leads == []


def test_regola_003_fail_closed_senza_cig():
    df = _df([["SUB1", "s", "t1", ""]], ["subject_id", "source_dataset", "source_record_id", "explanation"])
    leads, _ = apply_regola_003(df, 2)
    assert leads == []


def test_determinismo_id():
    rows = [
        ["MARIO ROSSI", "E1", "2025", "inc", "a1"],
        ["MARIO ROSSI", "E2", "2025", "inc", "a2"],
        ["MARIO ROSSI", "E3", "2025", "inc", "a3"],
        ["MARIO ROSSI", "E4", "2025", "inc", "a4"],
        ["MARIO ROSSI", "E5", "2025", "inc", "a5"],
    ]
    df = _df(rows, ["person_name", "entity_id", "year", "source_dataset", "source_record_id"])
    a, _ = apply_regola_001(df, 5)
    b, _ = apply_regola_001(df, 5)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a[0]["id"] == stable_id("REGOLA-001", "MARIO ROSSI|2025", "2025")


def test_manifest_ok_con_input_validi(tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    pd.DataFrame(
        [["MARIO", "E1", "2025", "ds", "r1", "u", "2025-01-01"]],
        columns=["person_name", "entity_id", "year", "source_dataset", "source_record_id", "source_url", "acquisition_date"],
    ).to_csv(inp / "incarichi.csv", index=False)
    pd.DataFrame(
        [["AW", "ENT", "2025-01-01", "affidamento diretto", "ds", "r2", "u", "2025-01-01"]],
        columns=["awardee", "entity_id", "award_date", "procedure_type", "source_dataset", "source_record_id", "source_url", "acquisition_date"],
    ).to_csv(inp / "affidamenti_diretti.csv", index=False)
    pd.DataFrame(
        [["C1", "SUB1", "", "ds", "r3", "u", "2025-01-01"]],
        columns=["cig", "subject_id", "explanation", "source_dataset", "source_record_id", "source_url", "acquisition_date"],
    ).to_csv(inp / "cig_enti.csv", index=False)

    out = tmp_path / "leads"
    _run_main(inp, out, RULES)
    manifest = json.load(open(out / "manifest.json", encoding="utf-8"))
    assert manifest["status"] == "ok"
    assert len(manifest["inputs"]) == 3
    assert manifest["explorer_sha256"]
    assert all(i["required_columns_present"] for i in manifest["inputs"])


def test_manifest_fail_input_mancante(tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()  # vuoto: file obbligatori mancanti
    out = tmp_path / "leads"
    with pytest.raises(SystemExit) as exc:
        _run_main(inp, out, RULES)
    assert exc.value.code == 1
    manifest = json.load(open(out / "manifest.json", encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert any("mancante" in e for e in manifest["errors"])
