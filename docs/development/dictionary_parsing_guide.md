# Collins Concise German Dictionary Parsing Guide

This document provides structured rules to help a program parse and understand entries from the **Collins Concise German Dictionary (German → English)**.

---

## 1. Entry Boundaries & Headword Line
- **Alphabetical order**: Headwords are ordered alphabetically. Bracketed letters are included in ordering.
- **Homographs**: Superscript numbers (¹, ², ³) distinguish headwords with identical spelling.
- **Part of Speech (POS) separation**: Black square (`■`) separates POS blocks or verb subcategories.
- **Sense Letters**: Lowercase letters (`a, b, c…`) denote fundamentally different meanings.
- **Plural-only nouns**: Some nouns are listed only in plural form. Mark as `pl-only`.
- **Compounds**: Listed alphabetically; may include element glosses.
- **Phrasal Verbs**: Indicated by `▶`, stored after the main entry.
- **Idioms & Set Phrases**: Usually listed under the first meaningful element.

---

## 2. Annotations & Signposts
- **Italics**: Explanations, clarifications, subjects/objects, or partial definitions.
- **Unbracketed collocators**: Typical complements.
- **Field labels**: (Anat), (Phys), (Tech), (Chess), etc.
- **Style labels**: (inf), (sl), (vulg), (geh), (form), (spec), (dated), (old), (obs), (liter).
- **also/auch**: Indicates additional (not alternative) translations.

---

## 3. Grammar Extraction
- **Gender**: Always indicated (m, f, nt).
- **Animate nouns/adjective-like nouns**:
  - `Angestellte(r)` → adjective-declension noun.
  - `Beamte(r)` → follows adjective endings.
  - `letzte(r,s)` → attributive only.
- **Feminine forms**: Brackets with `-in`, e.g. `Mörder(in)`.
- **Countability**: `no pl`, `no art` affect article/numeral usage.
- **Morphology hints**: Headwords list genitive & plural endings.
- **Prepositions**: Given with case and English mapping.

---

## 4. Phrasal Verbs
- Categories:
  - I: `vi` (intransitive)
  - II: `vi + prep obj`
  - III: `vt` (transitive)
  - IV: `vt + prep obj`
- **Separability flags**: `sep`, `always separate`, `insep`.

---

## 5. Punctuation & Symbols
- **`,`**: interchangeable synonyms (same sense).
- **`;`**: different meanings → new subsense.
- **`/`**: parallel structures/variants.
- **`—`**: separates speakers in dialogue.
- **`≈`**: approximate/cultural equivalent.
- **`od/or`**: interchangeable segment in phrase.
- **`CAPITALS`**: stress marking.

---

## 6. Cross References
- Used for spelling variants, idioms, categories (numerals, weekdays, etc.).

---

## 7. Recommended JSON Schema
```json
{
  "lemma": "…",
  "homograph_index": 1,
  "pos_blocks": [
    {
      "pos": "n|adj|vt|vi|vr",
      "subpos": "vt|vi impers|vt impers|vi+prep obj",
      "register": ["inf","sl","vulg","geh","form","spec","dated","old","obs","liter"],
      "domain": ["Anat","Phys","Tech","Chess"],
      "gram": {
        "gender": "m|f|nt|null",
        "number": "sg|pl|pl-only",
        "countability": "count|uncount|no-pl|no-art",
        "declension": "normal|adj-like",
        "has_feminine": true,
        "feminine_suffix": "-in",
        "de_genitive": "…",
        "de_plural": "…"
      },
      "senses": [
        {
          "sense_letter": "a",
          "gloss_en": "…",
          "translations_en": ["…","…"],
          "collocations": ["…"],
          "examples": [{"de":"…","en":"…"}],
          "prepositions": {
            "en": ["into","on"],
            "de": {"prep":"über","case":"acc"}
          }
        }
      ],
      "phrasal_verbs": [
        {"form_de":"…","pv_type":"vt","particle":"…","separability":"sep","translations_en":["…"]}
      ],
      "idioms": [
        {"de":"…","en":["…"],"xref_host":"…"}
      ],
      "compounds": [
        {"de":"…","en":["…"],"first_element_gloss":"Korallen-"}
      ]
    }
  ]
}
```

---

## 8. Parsing Heuristics
- **Split headword line**: Homographs, IPA, POS blocks separated by `■`.
- **Sense letters**: Match `^\s*[abcde]\s`.
- **Labels**: `(inf)`, `(dated)`, `(Anat)` etc.
- **Phrasal verbs**: Start with `▶`.
- **Prepositions**: `über +acc`.
- **Separability markers**: `sep|insep|always separate`.

---

## 9. Edge Cases
- Adjective-only forms.
- Adjective-declension nouns.
- `no pl`, `no art`.
- Approximate equivalents `≈`.
- Stress marking in phrases.

---

## 10. Example
```
Denkzettel m
a (inf) telling-off; (≈ Brit) ticking off

  jdm einen Denkzettel verpassen → to teach sb a lessonvery
```

Parsed JSON:
```json
{
  "lemma": "Denkzettel",
  "pos_blocks": [
    {
      "pos": "n",
      "gram": {"gender": "m"},
      "senses": [
        {
          "sense_letter": "a",
          "register": ["inf"],
          "translations_en": ["telling-off","ticking off"]
        }
      ],
      "idioms": [
        {"de":"jdm einen Denkzettel verpassen","en":["to teach sb a lesson"]}
      ]
    }
  ]
}
```

---
