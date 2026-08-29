#!/usr/bin/env python3
"""
apply_rules.py – Motore deterministico di applicazione regole.

Fail-closed sul contenuto, ma gli input obbligatori mancanti/illeggibili/sono
scartati producono un manifest di esecuzione con stato "failed" e fanno
uscire il processo con codice diverso da zero (così un input rotto è
distinguibile da un risultato pari a zero).

Allineato a REGOLE_SEGNALAZIONE.md v0.1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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

# File di input attesi (obbligatori) e relative colonne obbligatorie.
EXPECTED_INPUTS = {
    "incarichi.csv": {"person_name", "entity_id", "year"},
    "affidamenti_diretti.csv": {"awardee", "entity_id", "award_date", "procedure_type"},
    "cig_enti.csv": {"cig", "subject_id"},
}

# Regola -> file di input che la alimenta.
RULE_FILE = {
    "REGOLA-001": "incarichi.csv",
    "REGOLA-002": "affidamenti_diretti.csv",
    "REGOLA-003": "cig_enti.csv",
}


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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_regola_001(df: pd.DataFrame, threshold: int) -> tuple[list[dict], int]:
    """Concentrazione nominativi su enti diversi – stesso anno solare."""
    required = {"person_name", "entity_id", "year"}
    if not required.issubset(df.columns):
        return ([], 0)

    df = df.copy()
    df["person_name"] = df["person_name"].str.strip().str.upper()
    df["entity_id"] = df["entity_id"].str.strip()
    df["year"] = df["year"].str.strip()

    df = df[(df["person_name"] != "") & (df["entity_id"] != "") & (df["year"] != "")]
    n_valid = len(df)
    if df.empty:
        return ([], n_valid)

    leads = []
    for year, g_year in df.groupby("year"):
        counts = g_year.groupby("person_name")["entity_id"].nunique().reset_index(name="n_entities")
        hits = counts[counts["n_entities"] >= threshold]

        for _, row in hits.iterrows():
            name = row["person_name"]
            n = int(row["n_entities"])
            key = f"{name}|{year}"
            lead_id = stable_id("REGOLA-001", key, str(year))

            subset = g_year[g_year["person_name"] == name]
            sources = [
                {
                    "source_dataset": r.get("source_dataset", ""),
                    "source_record_id": r.get("source_record_id", ""),
                    "source_url": r.get("source_url", ""),
                    "entity_id": r.get("entity_id", ""),
                }
                for _, r in subset.iterrows()
            ]

            leads.append(
                {
                    "id": lead_id,
                    "title": f"Nominativo presente in {n} incarichi su enti diversi – anno {year}",
                    "observed_facts": [
                        f"Nominativo normalizzato: {name}",
                        f"Numero di enti distinti: {n}",
                        f"Anno solare: {year}",
                        f"Soglia della regola: >= {threshold}",
                    ],
                    "sources": sources,
                    "period": str(year),
                    "rule_id": "REGOLA-001",
                    "why_worth_checking": (
                        f"Concentrazione di {n} incarichi su enti diversi "
                        f"nello stesso anno solare (soglia >= {threshold})."
                    ),
                    "what_cannot_be_claimed": WHAT_CANNOT,
                    "disclaimer": DISCLAIMER,
                }
            )
    return (leads, n_valid)


def _parse_dates(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")


def apply_regola_002(df: pd.DataFrame, threshold: int) -> tuple[list[dict], int]:
    """Affidamenti diretti ripetuti dallo stesso ente – 12 mesi mobili.

    La finestra è calcolata rispetto alla data massima presente nei dati
    (deterministico: stesso input -> stesso output).
    """
    required = {"awardee", "entity_id", "award_date", "procedure_type"}
    if not required.issubset(df.columns):
        return ([], 0)

    df = df.copy()
    df["awardee"] = df["awardee"].str.strip().str.upper()
    df["entity_id"] = df["entity_id"].str.strip()
    df["procedure_type"] = df["procedure_type"].str.strip().str.lower()
    df["award_date"] = df["award_date"].str.strip()

    df = df[df["procedure_type"].str.contains("dirett", na=False)]
    df = df[(df["awardee"] != "") & (df["entity_id"] != "") & (df["award_date"] != "")]

    n_valid = len(df)
    if df.empty:
        return ([], n_valid)

    dt = _parse_dates(df["award_date"])
    df = df.assign(_dt=dt)
    dfv = df[df["_dt"].notna()].copy()
    if dfv.empty:
        return ([], n_valid)

    max_date = dfv["_dt"].max()
    w_start = max_date - pd.Timedelta(days=365)
    dfw = dfv[dfv["_dt"] >= w_start]

    window = f"{w_start.date()}..{max_date.date()}"
    leads = []
    for entity, g in dfw.groupby("entity_id"):
        counts = g.groupby("awardee").size().reset_index(name="n_awards")
        hits = counts[counts["n_awards"] >= threshold]

        for _, row in hits.iterrows():
            awardee = row["awardee"]
            n = int(row["n_awards"])
            key = f"{awardee}|{entity}|{max_date.date()}"
            lead_id = stable_id("REGOLA-002", key, window)

            subset = g[g["awardee"] == awardee]
            sources = [
                {
                    "source_dataset": r.get("source_dataset", ""),
                    "source_record_id": r.get("source_record_id", ""),
                    "source_url": r.get("source_url", ""),
                    "award_date": r.get("award_date", ""),
                }
                for _, r in subset.iterrows()
            ]

            leads.append(
                {
                    "id": lead_id,
                    "title": (
                        f"Aggiudicatario riceve {n} affidamenti diretti "
                        f"dallo stesso ente – 12 mesi mobili (fino al {max_date.date()})"
                    ),
                    "observed_facts": [
                        f"Aggiudicatario: {awardee}",
                        f"Ente: {entity}",
                        f"Numero di affidamenti diretti: {n}",
                        f"Finestra di osservazione: 12 mesi mobili fino al {max_date.date()}",
                        f"Soglia della regola: >= {threshold}",
                    ],
                    "sources": sources,
                    "period": window,
                    "rule_id": "REGOLA-002",
                    "why_worth_checking": (
                        f"Lo stesso aggiudicatario riceve {n} affidamenti diretti "
                        f"dallo stesso ente nei 12 mesi mobili fino al {max_date.date()} "
                        f"(soglia >= {threshold})."
                    ),
                    "what_cannot_be_claimed": WHAT_CANNOT,
                    "disclaimer": DISCLAIMER,
                }
            )
    return (leads, n_valid)


def apply_regola_003(df: pd.DataFrame, threshold: int) -> tuple[list[dict], int]:
    """CIG/CUP collegati a più enti senza spiegazione esplicita nella fonte.

    Usa la relazione disponibile (CIG/ente). Segnala solo quando la fonte non
    fornisce alcuna spiegazione del collegamento multiplo.
    """
    cig_col = "cig" if "cig" in df.columns else None
    cup_col = "cup" if "cup" in df.columns else None
    if cig_col is None and cup_col is None:
        return ([], 0)

    subject_col = None
    for c in ["subject_id", "awardee", "person_name", "organization"]:
        if c in df.columns:
            subject_col = c
            break
    if subject_col is None:
        return ([], 0)

    expl_col = "explanation" if "explanation" in df.columns else None

    df = df.copy()
    for c in [x for x in [cig_col, cup_col, subject_col] if x]:
        df[c] = df[c].astype(str).str.strip()

    code_col = cig_col or cup_col
    mask = (df[code_col] != "") & (df[subject_col] != "")
    n_valid = int(mask.sum())
    d = df[mask].copy()
    if d.empty:
        return ([], n_valid)

    leads = []
    for col in [cig_col, cup_col]:
        if col is None:
            continue
        for code, g in d[d[col] != ""].groupby(col):
            n_entities = g[subject_col].nunique()

            if expl_col is not None:
                explained = (g["explanation"].astype(str).str.strip() != "").any()
            else:
                explained = False
            if explained:
                continue

            if n_entities >= threshold:
                subset = g
                sources = [
                    {
                        "source_dataset": r.get("source_dataset", ""),
                        "source_record_id": r.get("source_record_id", ""),
                        "source_url": r.get("source_url", ""),
                        "subject": r.get(subject_col, ""),
                        "explanation": r.get("explanation", ""),
                    }
                    for _, r in subset.iterrows()
                ]
                leads.append(
                    {
                        "id": stable_id("REGOLA-003", f"{col}|{code}", "full"),
                        "title": (
                            f"{col.upper()} collegato a {n_entities} enti distinti "
                            f"senza spiegazione esplicita nella fonte"
                        ),
                        "observed_facts": [
                            f"{col.upper()}: {code}",
                            f"Numero di enti distinti: {n_entities}",
                            f"Soglia della regola: >= {threshold}",
                            "La fonte non fornisce spiegazione esplicita del collegamento multiplo",
                        ],
                        "sources": sources,
                        "period": "intero periodo coperto dal dataset",
                        "rule_id": "REGOLA-003",
                        "why_worth_checking": (
                            f"Lo stesso {col.upper()} risulta collegato a {n_entities} enti "
                            f"distinti senza spiegazione esplicita nella fonte "
                            f"(soglia >= {threshold})."
                        ),
                        "what_cannot_be_claimed": WHAT_CANNOT,
                        "disclaimer": DISCLAIMER,
                    }
                )
    return (leads, n_valid)


def compute_metadata(input_dir: Path, dfs: dict[str, pd.DataFrame]) -> dict[str, str]:
    dates: list[pd.Timestamp] = []
    acq: list[pd.Timestamp] = []

    if "affidamenti_diretti.csv" in dfs:
        dt = _parse_dates(dfs["affidamenti_diretti.csv"]["award_date"])
        dates.extend(dt.dropna().tolist())
    if "incarichi.csv" in dfs:
        yrs = pd.to_numeric(dfs["incarichi.csv"]["year"], errors="coerce").dropna().astype(int)
        if not yrs.empty:
            dates.append(pd.Timestamp(year=int(yrs.max()), month=1, day=1))
    if "cig_enti.csv" in dfs:
        pa = _parse_dates(dfs["cig_enti.csv"].get("acquisition_date", pd.Series([""])))
        acq.extend(pa.dropna().tolist())

    for name in dfs:
        pa = _parse_dates(dfs[name].get("acquisition_date", pd.Series([""])))
        acq.extend(pa.dropna().tolist())

    data_through = max(dates).date().isoformat() if dates else "0000-01-01"
    if acq:
        snapshot_created_at = max(acq).date().isoformat()
    else:
        snapshot_created_at = data_through

    files = sorted((input_dir / f).read_bytes() for f in EXPECTED_INPUTS if (input_dir / f).exists())
    explorer_sha = hashlib.sha256(b"".join(files)).hexdigest()

    return {
        "data_through": data_through,
        "snapshot_created_at": snapshot_created_at,
        "explorer_sha": explorer_sha,
    }


def build_manifest(status: str, files_info: list[dict], leads_count: int, errors: list[str],
                   meta: dict[str, str]) -> dict[str, Any]:
    return {
        "status": status,
        "errors": errors,
        "inputs": files_info,
        "leads_count": leads_count,
        "data_through": meta["data_through"],
        "snapshot_created_at": meta["snapshot_created_at"],
        "explorer_sha256": meta["explorer_sha"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Motore deterministico e fail-closed di piste investigative."
    )
    parser.add_argument("--input", required=True, type=Path, help="Cartella data/input")
    parser.add_argument("--output", required=True, type=Path, help="Cartella data/leads")
    parser.add_argument("--rules", required=True, type=Path, help="File YAML regole")
    args = parser.parse_args()

    rules_doc = load_rules(args.rules)
    args.output.mkdir(parents=True, exist_ok=True)

    # --- Validazione input obbligatori (manifest + fail) ---
    files_info: list[dict] = []
    errors: list[str] = []
    overall_ok = True
    dfs: dict[str, pd.DataFrame] = {}

    for name, req in EXPECTED_INPUTS.items():
        p = args.input / name
        info = {
            "file": name,
            "present": False,
            "readable": False,
            "rows": 0,
            "sha256": "",
            "required_columns": sorted(req),
            "required_columns_present": False,
            "rows_used": 0,
            "rows_discarded": 0,
            "status": "ok",
            "error": None,
        }
        if not p.exists():
            info["status"] = "failed"
            info["error"] = f"file obbligatorio mancante: {name}"
            overall_ok = False
            errors.append(info["error"])
            files_info.append(info)
            continue
        try:
            info["sha256"] = file_sha256(p)
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            info["readable"] = True
            info["present"] = True
            info["rows"] = len(df)
            missing = req - set(df.columns)
            if missing:
                info["status"] = "failed"
                info["error"] = f"colonne obbligatorie mancanti in {name}: {sorted(missing)}"
                overall_ok = False
                errors.append(info["error"])
            else:
                info["required_columns_present"] = True
                dfs[name] = df
        except Exception as e:  # noqa: BLE001
            info["status"] = "failed"
            info["error"] = f"file illeggibile {name}: {e}"
            overall_ok = False
            errors.append(info["error"])
        files_info.append(info)

    if not overall_ok:
        meta = compute_metadata(args.input, dfs) if dfs else {
            "data_through": "0000-01-01",
            "snapshot_created_at": "0000-01-01",
            "explorer_sha": "",
        }
        manifest = build_manifest("failed", files_info, 0, errors, meta)
        with open(args.output / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print("INPUT NON VALIDO – pipeline interrotta (manifest scritto).")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # --- Esecuzione regole ---
    meta = compute_metadata(args.input, dfs)
    all_leads: list[dict] = []

    for rule in rules_doc.get("rules", []):
        if not rule.get("enabled", False):
            continue
        rid = rule["id"]
        threshold = rule.get("threshold")
        fname = RULE_FILE.get(rid)
        if fname is None or fname not in dfs:
            continue

        df = dfs[fname]
        if rid == "REGOLA-001":
            leads, n_valid = apply_regola_001(df, threshold)
        elif rid == "REGOLA-002":
            leads, n_valid = apply_regola_002(df, threshold)
        elif rid == "REGOLA-003":
            leads, n_valid = apply_regola_003(df, threshold)
        else:
            continue

        all_leads.extend(leads)
        for info in files_info:
            if info["file"] == fname:
                info["rows_used"] = n_valid
                info["rows_discarded"] = info["rows"] - n_valid

    seen = set()
    unique_leads = []
    for lead in sorted(all_leads, key=lambda x: x["id"]):
        if lead["id"] not in seen:
            seen.add(lead["id"])
            unique_leads.append(lead)

    for lead in unique_leads:
        lead["data_through"] = meta["data_through"]
        lead["snapshot_created_at"] = meta["snapshot_created_at"]
        lead["explorer_sha"] = meta["explorer_sha"]

    out_json = args.output / "leads_v0.1.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(unique_leads, f, ensure_ascii=False, indent=2)

    for lead in unique_leads:
        md_path = args.output / f"{lead['id']}.md"
        facts = "\n".join(f"- {f}" for f in lead["observed_facts"])
        sources = "\n".join(
            f"- {s.get('source_dataset', '')} / {s.get('source_record_id', '')}"
            + (f" / {s['source_url']}" if s.get("source_url") else "")
            for s in lead["sources"]
        )
        cannot = "\n".join(f"- {c}" for c in lead["what_cannot_be_claimed"])

        content = f"""# {lead['title']}


**ID**: {lead['id']}
**Regola**: {lead['rule_id']}
**Periodo**: {lead['period']}
**Data di copertura (data_through)**: {lead['data_through']}
**Snapshot creato il (snapshot_created_at)**: {lead['snapshot_created_at']}
**SHA Explorer (explorer_sha)**: {lead['explorer_sha']}


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

    manifest = build_manifest("ok", files_info, len(unique_leads), [], meta)
    with open(args.output / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Motore completato. Piste generate: {len(unique_leads)}")
    print(f"Output JSON: {out_json}")
    print(f"Manifest: {args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
