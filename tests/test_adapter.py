import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import adapt_explorer  # noqa: E402


def test_adapt_persona():
    df = pd.DataFrame(
        [
            {
                "subject_key": "MARIO ROSSI",
                "object_key": "COMUNE X",
                "period": "2025-03-01",
                "source_dataset": "ds",
                "source_record_id": "r1",
            }
        ]
    )
    out = adapt_explorer.adapt_persona(df)
    assert list(out.columns) == [
        "person_name",
        "entity_id",
        "year",
        "source_dataset",
        "source_record_id",
    ]
    assert out.iloc[0]["person_name"] == "MARIO ROSSI"
    assert out.iloc[0]["entity_id"] == "COMUNE X"
    assert out.iloc[0]["year"] == "2025"


def test_adapt_awards():
    df = pd.DataFrame(
        [
            {
                "subject_key": "AZ",
                "object_key": "ENT",
                "period": "2024-05-01",
                "source_dataset": "ds",
                "source_record_id": "r2",
            }
        ]
    )
    out = adapt_explorer.adapt_awards(df)
    assert out.iloc[0]["awardee"] == "AZ"
    assert out.iloc[0]["entity_id"] == "ENT"
    assert out.iloc[0]["award_date"] == "2024-05-01"
    assert out.iloc[0]["procedure_type"] == "affidamento diretto"


def test_adapt_cig():
    df = pd.DataFrame(
        [
            {
                "subject_key": "CIG1",
                "object_key": "ENT",
                "source_dataset": "ds",
                "source_record_id": "r3",
            }
        ]
    )
    out = adapt_explorer.adapt_cig(df)
    assert out.iloc[0]["cig"] == "CIG1"
    assert out.iloc[0]["subject_id"] == "ENT"
