# Investigative Leads Generator · DVNS

Generator di **piste investigative conservative** a partire dalle tabelle di relazione prodotte da [investigative-explorer-dvns](https://github.com/superpios/investigative-explorer-dvns).

Ogni pista è un segnale quantitativo che **merita verifica**.
Nessuna pista dimostra, suggerisce o implica illecito, spreco, frode o responsabilità individuale.

**Progetto collegato** al repository madre [DoveVannoINostriSoldi](https://github.com/Italian-Builders-Org/DoveVannoINostriSoldi) (Fase 5 della ROADMAP).

## Cosa fa
- Legge le tabelle di relazione (formato definito in `schemas/` dell'Explorer)
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
# Copia le tabelle relations/ dall'Explorer in data/input/
python scripts/apply_rules.py --input data/input --output data/leads --rules rules/rules_v0.1.yaml
```

| File | Contenuto |
| --- | --- |
| docs/REGOLE_SEGNALAZIONE.md | Regole attive + principi vincolanti |
| docs/FORMATO_PISTA.md | Schema obbligatorio di ogni pista |
| docs/LIMITI.md | Limiti metodologici e interpretativi |

## Licenza
GNU Affero General Public License v3.0
