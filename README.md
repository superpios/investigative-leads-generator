# Investigative Leads Generator · DVNS

Generator di **piste investigative conservative** a partire dalle tabelle di relazione prodotte da [investigative-explorer-dvns](https://github.com/superpios/investigative-explorer-dvns).

Ogni pista è un segnale quantitativo che **merita verifica**.
Nessuna pista dimostra, suggerisce o implica illecito, spreco, frode o responsabilità individuale.

Consuma le tabelle di relazione prodotte da [investigative-explorer-dvns](https://github.com/superpios/investigative-explorer-dvns) e produce piste conservative, deterministiche e revisionabili.

## Cosa fa
- Prende le tabelle di relazione dell'Explorer e le **adatta** nel formato atteso dal motore (`scripts/adapt_explorer.py`)
- Applica regole dichiarative estremamente caute (YAML)
- Produce piste in **JSON + Markdown** con provenienza completa
- È **completamente deterministico** (stesso input → stesso output)

## Cosa non fa
- Non stabilisce responsabilità, illeciti o sprechi
- Non risolve omonimie
- Non somma perimetri contabili diversi
- Non usa etichette valutative

---

## Come usarlo (guida passo-passo)

### 0. Prerequisiti
- Python 3.10+ installato
- Le tabelle di relazione dell'Explorer disponibili localmente in `<EXPLORE>/data/relations/`
  (se non le hai, clona/aggiorna `investigative-explorer-dvns` e genera le relazioni con i suoi script;
  i file attesi sono ad es. `persona_incarico_ente__incarichi_nominativi_shard.csv`,
  `awards__affidamenti_diretti.csv`, `cig_ente__affidamenti_diretti.csv`).

### 1. Installazione
```bash
git clone https://github.com/superpios/investigative-leads-generator
cd investigative-leads-generator
pip install -r requirements.txt
```

### 2. Adatta le tabelle dell'Explorer → input del generatore
Lo schema dell'Explorer (`subject_key`, `object_key`, `period`, …) è diverso da quello che il
motore si aspetta: `adapt_explorer.py` rinomina i campi in modo esplicito e revisionabile.

```bash
python scripts/adapt_explorer.py \
    --relations "<EXPLORE>/data/relations" \
    --output  data/input
```
Questo scrive in `data/input/` tre CSV normalizzati:
`incarichi.csv`, `affidamenti_diretti.csv`, `cig_enti.csv`.

### 3. Genera le piste
```bash
python scripts/apply_rules.py \
    --input  data/input \
    --output data/leads \
    --rules  rules/rules_v0.1.yaml
```
Oppure, equivalente, tramite il wrapper:
```bash
python scripts/generate_leads.py
```

### 4. Cosa ottieni
In `data/leads/`:
- `leads_v0.1.json` — tutte le piste (una lista di oggetti)
- `LEAD-<REGOLA>-<hash>.md` — una pagina Markdown per pista

Ogni pista contiene **sempre** tutti i campi di `docs/FORMATO_PISTA.md`
(`id`, `title`, `observed_facts`, `sources`, `period`, `rule_id`,
`why_worth_checking`, `what_cannot_be_claimed`, `generation_date`, `disclaimer`).
Esempio di `title`: *"Nominativo presente in 5 incarichi su enti diversi – anno 2025"*.

### 5. Opzioni
- `--generation-date YYYY-MM-DD`: forza la data di riferimento. Se omessa, viene **derivata
  deterministicamente** dai dati (anno massimo nei periodi osservati) — mai l'orario di esecuzione.
- Su dati reali dell'Explorer l'esecuzione produce poche piste (es. 7 nell'ultimo test:
  7 `REGOLA-002`, 0 `REGOLA-001`, 0 `REGOLA-003`); è voluto: le regole sono conservative.

---

## Comportamento importante
- **Deterministico**: stesso input → stesso output. `generation_date` deriva dai dati, non da `datetime.now()`.
- **Fail-closed**: se `data/input/` è vuoto o mancano colonne obbligatorie, **non viene emessa
  alcuna pista** (nessun errore, nessuna inferenza). Nessun dato lascia mai la macchina.

## Mappatura Explorer → generatore
| Tabella Explorer | → colonne generatore |
| --- | --- |
| `persona_incarico_ente__*` | `person_name=subject_key`, `entity_id=IPA (o object_key)`, `year=period[:4]` |
| `awards__affidamenti_diretti` | `awardee=subject_key`, `entity_id=IPA (o object_key)`, `award_date=period`, `procedure_type="affidamento diretto"` |
| `cig_ente__affidamenti_diretti` | `cig=subject_key`, `subject_id=IPA (o object_key)` |

La provenienza (`source_dataset`, `source_record_id`, `source_url`) è preservata in ogni pista.
Dettagli e logica in `scripts/adapt_explorer.py` e `docs/REGOLE_SEGNALAZIONE.md`.

## Documentazione
| File | Contenuto |
| --- | --- |
| `docs/REGOLE_SEGNALAZIONE.md` | Regole attive + principi vincolanti |
| `docs/FORMATO_PISTA.md` | Schema obbligatorio di ogni pista |
| `docs/LIMITI.md` | Limiti metodologici e interpretativi |
| `templates/lead_template.md` | Template illustrativo (il motore scrive il Markdown inline) |

## Licenza
GNU Affero General Public License v3.0
