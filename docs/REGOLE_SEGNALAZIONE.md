# Regole di segnalazione – Investigative Leads Generator

Documento obbligatorio. Tutte le regole sono estremamente conservative.

Ogni regola genera solo una “pista” (lead) che **merita verifica**.

Nessuna regola dimostra, suggerisce o implica illecito, spreco, frode, corruzione o responsabilità individuale.

Queste regole implementano in modo dichiarativo e riproducibile i principi di segnalazione conservativa descritti in questo documento.

## Principi vincolanti (non negoziabili)

1. Condizione precisa + soglia numerica + periodo di osservazione obbligatori.
2. Ogni pista deve contenere la nota fissa:
   «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»
3. Nessuna somma o confronto tra perimetri contabili diversi.
4. Nessuna risoluzione automatica di omonimie.
5. Nessuna etichetta valutativa (es. “sospetto”, “anomalo”, “favoritismo”).
6. Output sempre deterministico: stesso input → stesso output.
7. Provenienza completa di ogni record usato.

## Regole attive (versione 0.1 – estremamente caute)

### REGOLA-001 – Concentrazione nominativi su enti diversi
- **Condizione**: Stesso nominativo normalizzato compare in ≥ 5 incarichi distinti su enti diversi.
- **Soglia**: ≥ 5
- **Periodo di osservazione**: stesso anno solare
- **Fonte dati**: tabelle di relazione prodotte da investigative-explorer-dvns (schemas/ + data/relations/)
- **Nota obbligatoria**: «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»

### REGOLA-002 – Affidamenti diretti ripetuti dallo stesso ente
- **Condizione**: Stesso aggiudicatario riceve ≥ 8 affidamenti diretti dallo stesso ente.
- **Soglia**: ≥ 8
- **Periodo di osservazione**: 12 mesi mobili
- **Fonte dati**: tabelle di relazione relative ad affidamenti diretti
- **Nota obbligatoria**: «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»

### REGOLA-003 – CIG/CUP collegati a più soggetti in modo non spiegato dalla fonte
- **Condizione**: Stesso CIG o stesso CUP appare collegato a più soggetti e la fonte non fornisce spiegazione esplicita del collegamento multiplo.
- **Soglia**: ≥ 2 soggetti distinti non giustificati
- **Periodo di osservazione**: intero periodo coperto dal dataset
- **Nota obbligatoria**: «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»

### REGOLA-004 – Percentuale elevata di affidamenti diretti su un singolo ente
- **Condizione**: Percentuale di affidamenti diretti sul totale degli affidamenti osservati di un ente superiore a soglia documentata.
- **Soglia**: da dichiarare esplicitamente per ogni esecuzione (es. > 70 % – valore da calibrare solo su dati reali e documentato)
- **Periodo di osservazione**: anno solare o 12 mesi
- **Nota obbligatoria**: «Questo non dimostra alcun illecito. Indica solo una concentrazione che merita verifica.»

## Regole non ancora attive
Nessuna altra regola è abilitata in v0.1. Qualsiasi nuova regola richiede:
- aggiornamento di questo file
- test quantitativi contro falsi positivi
- validazione manuale di almeno 20 piste generate
- aggiornamento di docs/LIMITI.md

## Changelog regole
- 2026-08-28 – v0.1: prime 4 regole estremamente conservative.
