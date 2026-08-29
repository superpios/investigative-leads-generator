#!/usr/bin/env python3
"""Adattatore: trasforma le tabelle di relazione di investigative-explorer-dvns
nel formato di input atteso da scripts/apply_rules.py.

Mappatura documentata e revisionabile (vedi REGOLE_SEGNALAZIONE.md):
  persona_incarico_ente__incarichi_nominativi_shard.csv
     -> person_name = subject_key, entity_id = IPA (o object_key), year = period[:4]
  awards__affidamenti_diretti.csv
     -> awardee = subject_key, entity_id = IPA (o object_key), award_date = period,
        procedure_type = "affidamento diretto" (il dataset e' gia' filtrato)
  cig_ente__affidamenti_diretti.csv
     -> cig = subject_key, subject_id = IPA (o object_key)

La provenienza (source_dataset, source_record_id) e' preservata cosi' com'e'.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SOURCES = {
    "persona_incarico_ente__incarichi_nominativi_shard.csv": "incarichi.csv",
    "awards__affidamenti_diretti.csv": "affidamenti_diretti.csv",
    "cig_ente__affidamenti_diretti.csv": "cig_enti.csv",
}


def _src(df: pd.DataFrame) -> dict[str, object]:
    return {
        "source_dataset": df.get("source_dataset", ""),
        "source_record_id": df.get("source_record_id", ""),
    }


def _ent_id(df: pd.DataFrame) -> "pd.Series":
    # Identificativo stabile dell'ente: codice IPA se presente, altrimenti il nome (object_key)
    if "ipa" in df.columns:
        ipa = df["ipa"].astype(str).str.strip()
        obj = df["object_key"].astype(str).str.strip()
        return ipa.where(ipa != "", obj)
    return df["object_key"].astype(str).str.strip()


def adapt_persona(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["person_name"] = df["subject_key"]
    out["entity_id"] = _ent_id(df)
    out["year"] = df["period"].astype(str).str[:4]
    out["source_dataset"] = _src(df)["source_dataset"]
    out["source_record_id"] = _src(df)["source_record_id"]
    return out


def adapt_awards(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["awardee"] = df["subject_key"]
    out["entity_id"] = _ent_id(df)
    out["award_date"] = df["period"].astype(str)
    out["procedure_type"] = "affidamento diretto"
    out["source_dataset"] = _src(df)["source_dataset"]
    out["source_record_id"] = _src(df)["source_record_id"]
    return out


def adapt_cig(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["cig"] = df["subject_key"]
    out["subject_id"] = _ent_id(df)
    out["source_dataset"] = _src(df)["source_dataset"]
    out["source_record_id"] = _src(df)["source_record_id"]
    return out


ADAPTERS = {
    "persona_incarico_ente__incarichi_nominativi_shard.csv": adapt_persona,
    "awards__affidamenti_diretti.csv": adapt_awards,
    "cig_ente__affidamenti_diretti.csv": adapt_cig,
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Adatta le relazioni dell'Explorer al formato del generatore.")
    ap.add_argument("--relations", required=True, type=Path, help="Cartella data/relations dell'Explorer")
    ap.add_argument("--output", required=True, type=Path, help="Cartella data/input del generatore")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for src, dst in SOURCES.items():
        p = args.relations / src
        if not p.exists():
            print(f"salto (assente): {src}")
            continue
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        out = ADAPTERS[src](df)
        out.to_csv(args.output / dst, index=False)
        print(f"{src} -> {dst}: {len(out)} righe")


if __name__ == "__main__":
    main()
