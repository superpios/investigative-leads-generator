# Investigative Leads Generator · DVNS

Generator di **piste investigative conservative** a partire dalle tabelle di relazione prodotte da [investigative-explorer-dvns](https://github.com/superpios/investigative-explorer-dvns).

Ogni pista è un segnale quantitativo che **merita verifica**.
Nessuna pista dimostra, suggerisce o implica illecito, spreco, frode o responsabilità individuale.

**Progetto collegato** al repository madre [DoveVannoINostriSoldi](https://github.com/Italian-Builders-Org/DoveVannoINostriSoldi) (Fase 5 della ROADMAP).

## Cosa fa
- Legge le tabelle di relazione (CSV) esportate da `investigative-explorer-dvns` (in `data/relations/` dell'Explorer); lo schema di ogni pista in uscita è in `docs/FORMATO_PISTA.md`
- Applica regole dichiarative estremamente caute (YAML)
- Produce piste in JSON + Markdown con provenienza completa
- È completamente deterministico (stesso input → stesso output)

## Cosa non fa
- Non stabilisce responsabilità, illeciti o sprechi
- Non risolve omonimie
- Non somma perimetri contabili diversi
- Non usa etichette valutative

## Avvio rapido
```bash
pip install -r requirements.txt
# 1) Adatta le tabelle di relazione dell'Explorer nel formato atteso dal generatore
python scripts/adapt_explorer.py --relations <EXPLORE>/data/relations --output data/input
# 2) Applica le regole (deterministico, fail-closed)
python scripts/apply_rules.py --input data/input --output data/leads --rules rules/rules_v0.1.yaml
```

| File | Contenuto |
| --- | --- |
| docs/REGOLE_SEGNALAZIONE.md | Regole attive + principi vincolanti |
| docs/FORMATO_PISTA.md | Schema obbligatorio di ogni pista |
| docs/LIMITI.md | Limiti metodologici e interpretativi |

## Note di implementazione
- **Determinismo**: `generation_date` è derivato dai dati (anno massimo nei periodi osservati), non dall'orario di esecuzione. Stesso input → stesso output, in conformità al principio 6 di `docs/REGOLE_SEGNALAZIONE.md`.
- **Fail-closed**: in assenza di file o di campi obbligatori non viene emessa alcuna pista (nessun errore, nessuna inferenza).

## Licenza
GNU Affero General Public License v3.0
