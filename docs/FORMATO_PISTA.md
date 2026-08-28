# Formato obbligatorio di una pista

Ogni pista deve contenere **tutti** i campi seguenti.
Assenza anche di uno solo dei campi → la pista non viene emessa.

## Campi obbligatori

- **id**: identificativo univoco e stabile (es. `LEAD-001-REGOLA-001-2026`)
- **title**: titolo neutro, solo fattuale (es. "Nominativo presente in 7 incarichi su enti diversi – anno 2025")
- **observed_facts**: elenco puntato di fatti osservati (solo numeri e riferimenti)
- **sources**: lista di `source_dataset` + `source_record_id` + URL o hash
- **period**: periodo di osservazione esatto
- **rule_id**: ID della regola che ha generato la pista
- **why_worth_checking**: frase fissa + motivazione quantitativa
- **what_cannot_be_claimed**: elenco esplicito di ciò che non si può affermare
- **generation_date**: data ISO di generazione
- **disclaimer**: testo fisso obbligatorio
  «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»

## Esempio minimo valido
Vedi `templates/lead_template.md`.
