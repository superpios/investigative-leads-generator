> Nota: template illustrativo. Il motore (`scripts/apply_rules.py`) genera il Markdown inline; questo file documenta lo schema obbligatorio definito in `docs/FORMATO_PISTA.md`.

# {{ title }}

**ID**: {{ id }}
**Regola**: {{ rule_id }}
**Periodo**: {{ period }}
**Data di copertura (data_through)**: {{ data_through }}
**Snapshot creato il (snapshot_created_at)**: {{ snapshot_created_at }}
**SHA Explorer (explorer_sha)**: {{ explorer_sha }}

## Fatti osservati
{{ observed_facts }}

## Fonti e record precisi
{{ sources }}

## Perché merita verifica
{{ why_worth_checking }}

## Cosa non si può affermare
{{ what_cannot_be_claimed }}

---
**Disclaimer obbligatorio**
{{ disclaimer }}
