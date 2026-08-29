#!/usr/bin/env python3
"""
apply_rules.py – Motore deterministico di applicazione regole.

Fail-closed. Nessuna inferenza. Solo conteggi esatti.

Allineato a REGOLE_SEGNALAZIONE.md v0.1.

"""

from __future__ import annotations


import argparse

import hashlib

import json

from pathlib import Path

from typing import Any


import pandas as pd

import yaml


DISCLAIMER = (
    "Questo non dimostra alcun illecito. "
    "Indica solo una concentrazione che merita verifica."
)

WHAT_CANNOT = [
    "Nessuna responsabilità individuale",
    "Nessun illecito, frode, corruzione o spreco",
    "Nessuna risoluzione di omonimie",
    "Nessun confronto tra perimetri contabili diversi",
]


def load_rules(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "rules" not in data:
        raise ValueError("File regole non valido: manca chiave 'rules'")
    return data


def stable_id(rule_id: str, key: str, period: str) -> str:
    raw = f"{rule_id}|{key}|{period}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()[:10]
    return f"LEAD-{rule_id}-{h}"


def read_csv_safe(path: Path) -> pd.DataFrame | None:
    """Legge un CSV solo se presente e non vuoto. Fail-closed."""
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def apply_regola_001(df: pd.DataFrame, threshold: int, period: str) -> list[dict]:
    """Concentrazione nominativi su enti diversi – stesso anno solare."""
    required = {"person_name", "entity_id", "year"}
    if not required.issubset(df.columns):
        return []

    df = df.copy()
    df["person_name"] = df["person_name"].str.strip().str.upper()
    df["entity_id"] = df["entity_id"].str.strip()
    df["year"] = df["year"].str.strip()

    df = df[
        (df["person_name"] != "")
        & (df["entity_id"] != "")
        & (df["year"] != "")
    ]
    if df.empty:
        return []

    leads = []
    for year, g_year in df.groupby("year"):
        counts = (
            g_year.groupby("person_name")["entity_id"]
            .nunique()
            .reset_index(name="n_entities")
        )
        hits = counts[counts["n_entities"] >= threshold]

        for _, row in hits.iterrows():
            name = row["person_name"]
            n = int(row["n_entities"])
            key = f"{name}|{year}"
            lead_id = stable_id("REGOLA-001", key, str(year))

            subset = g_year[g_year["person_name"] == name]
            sources = []
            for _, r in subset.iterrows():
                sources.append(
                    {
                        "source_dataset": r.get("source_dataset", ""),
                        "source_record_id": r.get("source_record_id", ""),
                        "entity_id": r.get("entity_id", ""),
                    }
                )

            leads.append(
                {
                    "id": lead_id,
                    "title": f"Nominativo presente in {n} incarichi su enti diversi – anno {year}",
                    "observed_facts": [
                        f"Nominativo normalizzato: {name}",
                        f"Numero di enti distinti: {n}",
                        f"Anno solare: {year}",
                        f"Soglia della regola: ≥ {threshold}",
                    ],
                    "sources": sources,
                    "period": str(year),
                    "rule_id": "REGOLA-001",
                    "why_worth_checking": (
                        f"Concentrazione di {n} incarichi su enti diversi "
                        f"nello stesso anno solare (soglia ≥ {threshold})."
                    ),
                    "what_cannot_be_claimed": WHAT_CANNOT,
                    "generation_date": "",
                    "disclaimer": DISCLAIMER,
                }
            )
    return leads


def apply_regola_002(df: pd.DataFrame, threshold: int, period: str) -> list[dict]:
    """Affidamenti diretti ripetuti dallo stesso ente."""
    required = {"awardee", "entity_id", "award_date", "procedure_type"}
    if not required.issubset(df.columns):
        return []

    df = df.copy()
    df["awardee"] = df["awardee"].str.strip().str.upper()
    df["entity_id"] = df["entity_id"].str.strip()
    df["procedure_type"] = df["procedure_type"].str.strip().str.lower()

    df = df[df["procedure_type"].str.contains("dirett", na=False)]
    df = df[
        (df["awardee"] != "")
        & (df["entity_id"] != "")
        & (df["award_date"] != "")
    ]
    if df.empty:
        return []

    df["year"] = df["award_date"].str[:4]

    leads = []
    for (entity, year), g in df.groupby(["entity_id", "year"]):
        counts = (
            g.groupby("awardee")
            .size()
            .reset_index(name="n_awards")
        )
        hits = counts[counts["n_awards"] >= threshold]

        for _, row in hits.iterrows():
            awardee = row["awardee"]
            n = int(row["n_awards"])
            key = f"{awardee}|{entity}|{year}"
            lead_id = stable_id("REGOLA-002", key, str(year))

            subset = g[g["awardee"] == awardee]
            sources = []
            for _, r in subset.iterrows():
                sources.append(
                    {
                        "source_dataset": r.get("source_dataset", ""),
                        "source_record_id": r.get("source_record_id", ""),
                        "award_date": r.get("award_date", ""),
                    }
                )

            leads.append(
                {
                    "id": lead_id,
                    "title": (
                        f"Aggiudicatario riceve {n} affidamenti diretti "
                        f"dallo stesso ente – anno {year}"
                    ),
                    "observed_facts": [
                        f"Aggiudicatario: {awardee}",
                        f"Ente: {entity}",
                        f"Numero di affidamenti diretti: {n}",
                        f"Anno di riferimento: {year}",
                        f"Soglia della regola: ≥ {threshold}",
                    ],
                    "sources": sources,
                    "period": str(year),
                    "rule_id": "REGOLA-002",
                    "why_worth_checking": (
                        f"Lo stesso aggiudicatario riceve {n} affidamenti diretti "
                        f"dallo stesso ente (soglia ≥ {threshold})."
                    ),
                    "what_cannot_be_claimed": WHAT_CANNOT,
                    "generation_date": "",
                    "disclaimer": DISCLAIMER,
                }
            )
    return leads


def apply_regola_003(df: pd.DataFrame, threshold: int, period: str) -> list[dict]:
    """CIG/CUP collegati a più soggetti senza spiegazione esplicita nella fonte."""
    cig_col = "cig" if "cig" in df.columns else None
    cup_col = "cup" if "cup" in df.columns else None
    if cig_col is None and cup_col is None:
        return []

    subject_col = None
    for c in ["subject_id", "awardee", "person_name", "organization"]:
        if c in df.columns:
            subject_col = c
            break
    if subject_col is None:
        return []

    leads = []
    for col in [cig_col, cup_col]:
        if col is None:
            continue
        df2 = df.copy()
        df2[col] = df2[col].str.strip()
        df2[subject_col] = df2[subject_col].str.strip()
        df2 = df2[(df2[col] != "") & (df2[subject_col] != "")]
        if df2.empty:
            continue

        counts = (
            df2.groupby(col)[subject_col]
            .nunique()
            .reset_index(name="n_subjects")
        )
        hits = counts[counts["n_subjects"] >= threshold]

        for _, row in hits.iterrows():
            code = row[col]
            n = int(row["n_subjects"])
            key = f"{col}|{code}"
            lead_id = stable_id("REGOLA-003", key, "full")

            subset = df2[df2[col] == code]
            sources = []
            for _, r in subset.iterrows():
                sources.append(
                    {
                        "source_dataset": r.get("source_dataset", ""),
                        "source_record_id": r.get("source_record_id", ""),
                        "subject": r.get(subject_col, ""),
                    }
                )

            leads.append(
                {
                    "id": lead_id,
                    "title": (
                        f"{col.upper()} collegato a {n} soggetti distinti "
                        f"senza spiegazione esplicita nella fonte"
                    ),
                    "observed_facts": [
                        f"{col.upper()}: {code}",
                        f"Numero di soggetti distinti: {n}",
                        f"Soglia della regola: ≥ {threshold}",
                        "La fonte non fornisce spiegazione esplicita del collegamento multiplo",
                    ],
                    "sources": sources,
                    "period": "intero periodo coperto dal dataset",
                    "rule_id": "REGOLA-003",
                    "why_worth_checking": (
                        f"Lo stesso {col.upper()} risulta collegato a {n} soggetti "
                        f"distinti senza spiegazione esplicita nella fonte "
                        f"(soglia ≥ {threshold})."
                    ),
                    "what_cannot_be_claimed": WHAT_CANNOT,
                    "generation_date": "",
                    "disclaimer": DISCLAIMER,
                }
            )
    return leads


def _derive_gen_date(leads: list[dict]) -> str:
    """Data di riferimento deterministica: anno massimo presente nei periodi."""
    years = []
    for lead in leads:
        p = str(lead.get("period", ""))
        if p.isdigit():
            years.append(int(p))
    if years:
        return f"{max(years)}-01-01"
    return "0000-01-01"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Motore deterministico e fail-closed di piste investigative."
    )
    parser.add_argument("--input", required=True, type=Path, help="Cartella data/input")
    parser.add_argument("--output", required=True, type=Path, help="Cartella data/leads")
    parser.add_argument("--rules", required=True, type=Path, help="File YAML regole")
    parser.add_argument(
        "--generation-date",
        default=None,
        help="Data di riferimento (YYYY-MM-DD); se omessa deriva deterministicamente dai dati",
    )
    args = parser.parse_args()

    rules_doc = load_rules(args.rules)
    args.output.mkdir(parents=True, exist_ok=True)

    all_leads: list[dict] = []

    csv_files = list(args.input.glob("*.csv"))
    if not csv_files:
        print("Nessun file CSV in data/input/. Nessuna pista generata (fail-closed).")
        print("Copia le tabelle relations/ dell'Explorer e riprova.")
        return

    for rule in rules_doc.get("rules", []):
        if not rule.get("enabled", False):
            continue

        rid = rule["id"]
        threshold = rule.get("threshold")
        period = rule.get("period", "")

        for csv_path in csv_files:
            df = read_csv_safe(csv_path)
            if df is None:
                continue

            if rid == "REGOLA-001":
                all_leads.extend(apply_regola_001(df, threshold, period))
            elif rid == "REGOLA-002":
                all_leads.extend(apply_regola_002(df, threshold, period))
            elif rid == "REGOLA-003":
                all_leads.extend(apply_regola_003(df, threshold, period))
            # REGOLA-004 resta disabilitata

    seen = set()
    unique_leads = []
    for lead in sorted(all_leads, key=lambda x: x["id"]):
        if lead["id"] not in seen:
            seen.add(lead["id"])
            unique_leads.append(lead)

    # Data di generazione deterministica (mai datetime.now): deriva dai dati
    # o da --generation-date. Stesso input -> stesso output.
    gen_date = args.generation_date or _derive_gen_date(unique_leads)
    for lead in unique_leads:
        lead["generation_date"] = gen_date

    out_json = args.output / "leads_v0.1.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(unique_leads, f, ensure_ascii=False, indent=2)

    for lead in unique_leads:
        md_path = args.output / f"{lead['id']}.md"
        facts = "\n".join(f"- {f}" for f in lead["observed_facts"])
        sources = "\n".join(
            f"- {s.get('source_dataset', '')} / {s.get('source_record_id', '')}"
            for s in lead["sources"]
        )
        cannot = "\n".join(f"- {c}" for c in lead["what_cannot_be_claimed"])

        content = f"""# {lead['title']}


**ID**: {lead['id']}
**Regola**: {lead['rule_id']}
**Periodo**: {lead['period']}
**Data generazione**: {lead['generation_date']}


## Fatti osservati
{facts}


## Fonti e record precisi
{sources}


## Perché merita verifica
{lead['why_worth_checking']}


## Cosa non si può affermare
{cannot}


---
**Disclaimer obbligatorio**
{lead['disclaimer']}
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Motore completato. Piste generate: {len(unique_leads)}")
    print(f"Output JSON: {out_json}")
    print("Vedi docs/REGOLE_SEGNALAZIONE.md e docs/LIMITI.md.")
    if not unique_leads:
        print(
            "Nessuna pista emessa (comportamento atteso se i dati non superano le soglie "
            "o se mancano i campi obbligatori – fail-closed)."
        )


if __name__ == "__main__":
    main()
