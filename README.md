# IPP 2024/2025 - Úloha 1: `parse.py` 

## 📌 Popis projektu

Skript `parse.py` slúži ako **filter**, ktorý číta vstupný program v jazyku **SOL25** zo štandardného vstupu a vypisuje jeho **abstraktný syntaktický strom (AST)** vo forme **XML** na štandardný výstup.

Pri spustení s argumentom `-h` alebo `--help` zobrazí stručný popis funkčnosti skriptu.

---

## 🧠 Analýza vstupného programu

### Lexikálna a syntaktická analýza

- Použitá knižnica: [`Lark`](https://github.com/lark-parser/lark)
- Gramatika je definovaná vo forme **ENBF**, pričom `Lark` vykoná parsing cez metódu `parse`.
- Výstupom je strom obsahujúci gramatické pravidlá a terminály.
- Lexikálne chyby sú detekované cez regulárne výrazy.
- Rekurzívne pravidlá sú definované tak, aby minimalizovali nežiadúce zanorenie.

### Abstraktný syntaktický strom (AST)

- Strom z `Lark` je transformovaný na **AST** pomocou triedy `Transformer`.
- Výsledná štruktúra je podobná **JSON** reprezentácii.

### Sémantická analýza

Prebieha pred samotnou XML serializáciou a zahŕňa:

- Kontrolu zasielania **triednych správ** (`check_class_message`)
  - Napr. overenie, že `read` je správne volaná na podtriede `String` (`is_subclass`)
- Detekciu **cyklickej dedičnosti** (`check_cyclic_inheritance`)
- Overovanie pomocou zoznamov:
  - kľúčové slová
  - vstavané triedy
  - globálne objekty
  - pseudopremenné

---

## </> Generovanie XML

- Implementované pomocou knižnice [`xml.etree.ElementTree`](https://docs.python.org/3/library/xml.etree.elementtree.html)
- Hlavné funkcie:
  - `generate_xml` – vytvorí koreňový `<program>` element
  - `generate_class` – generuje triedy a ich obsah rekurzívne
- XML výstup je generovaný **zhora nadol**

### Formátovanie výstupu

Pred výstupom sa aplikuje:

- `format_xml` – zabezpečuje odsadenie, kódovanie a hlavičku XML dokumentu

---

## 💡 Spustenie

```bash
python3 parse.py < vstup.sol > vystup.xml
