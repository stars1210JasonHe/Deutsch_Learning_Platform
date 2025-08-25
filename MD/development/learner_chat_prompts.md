# Quick Chat Tips Implementation for Word Search Feature

Implementation plan for adding quick chat tips to the ChatModal when users open chat about a searched German word.

## UI Integration Plan

**Location**: Welcome message area in ChatModal.vue (lines 38-45)
**Trigger**: When user opens chat modal for a word
**Display**: Quick tip buttons below the welcome text "Ask me anything about [word]!"

## Core Quick Tips to Implement

### Priority Tips (5 buttons):
1. **📖 Simple Explanation**: "Explain [word] in simple terms"
2. **📝 3 Examples**: "Give 3 example sentences for [word]"
3. **🔄 Conjugations**: "Show conjugations for [word]" (verbs only)
4. **📐 Grammar Cases**: "What case does [word] take?" (verbs/prepositions)
5. **🔍 Synonyms & Antonyms**: "Show synonyms and antonyms of [word]"

### Implementation Details:

**Backend Integration**: 
- Uses updated chat.py with structured JSON responses
- Returns: `{answer, examples, mini_practice, tips}`
- Pre-written prompts sent as chat messages

**Frontend Changes**:
- Add tip buttons in ChatModal.vue welcome area
- Display structured responses nicely if available
- Fallback to regular chat display

**Button Behavior**:
- Click sends pre-written message to chat
- Shows in chat history like regular user message
- Gets AI response with structured data if possible

---

## Original Documentation (for reference)

## 1) Core Quick Prompts (use daily)

### Word Help
- **Explain `<word>` in simple A2 words.**
- **Give 3 example sentences for `<word>`** *(1 casual, 1 neutral, 1 formal).*  
- **Common phrases/collocations with `<word>`.**
- **Synonyms & antonyms of `<word>` (with nuance).**

### Compare & Contrast
- **What’s the difference between `X` and `Y`?**  
  *Return a mini table: meaning • register • grammar • example.*

### Grammar On Demand
- **Conjugate `<verb>`** *(Präsens/Präteritum/Perfekt, Partizip, trennbar?)*
- **What case does `<verb/preposition>` take?** *+ 3 examples.*
- **Gender & plural of `<noun>`** *(note irregulars/exceptions).*

### Usage & Register
- **When do I use `<word/expression>`?** *Formal, informal, regional? pitfalls?*

### Memory & Practice
- **Make a 5‑item quiz for `<word/topic>`** *(cloze; solutions at the end).*
- **Create a mnemonic for `<word>`.**
- **Similar‑looking/sounding words to avoid mixing up with `<word>`.**

---

## 2) High‑Impact Extras (recommended)

### Pronunciation Coach
- **Show IPA, main stress, and a slow→natural tip for `<word>`.**
- **Give 1 quick minimal‑pair or tongue‑twister with the target sound.**

### Error Fix‑it
- **Correct my sentence:** `_your sentence_`.  
  *Explain the rule in one line, then give 2 alternatives (casual & formal).*

### Micro‑Dialogues (context is king)
- **Write a 4‑line dialogue using `<word>` in a real situation** *(e.g., at the bakery). Bold the target word.*

### Review & Goals
- **Quiz me on my last 10 saved words** *(≈70% known, 30% stretch).*  
- **Make a 7‑day micro‑plan for `<topic>`** *(5‑minute tasks/day).*

### Culture & Etymology (lightweight)
- **Any cultural notes or regional differences for `<word>`?**  
- **Short origin/word family for `<word>`** *(keep it fun, 2 lines).*

---

## 3) Slash Shortcuts (optional UX sugar)

```
/ex <word>          # simple explanation
/ex3 <word>         # 3 examples (casual/neutral/formal)
/cmp X | Y          # compare X vs Y (mini table)
/conj <verb>        # full conjugations
/case <verb/prep>   # case & 3 examples
/quiz <topic>       # 5-item cloze quiz
/mnemo <word>       # mnemonic
/pron <word>        # IPA + stress + tip
/fix <sentence>     # correct & explain
/dialog <word> @scenario   # 4-line dialogue
/review             # spaced review of last saved items
```

---

## 4) Bot Response Style (how to answer)

- **TL;DR first line:** one‑sentence plain answer.
- **Examples:** 2–3 short, level‑appropriate sentences.
- **Mini‑practice:** 1 cloze or tiny task.
- **Keep it graded:** default to A2–B1 wording unless asked otherwise.
- **Toggle depth:** offer “Need more? Say *deep dive*.”
- **Localization:** explanations in English → switchable to Chinese on request.

> **Template:**  
> **Answer:** _short, simple._  
> **Examples:** `• …` `• …` `• …`  
> **Mini‑practice:** _Fill the blank: …_ *(Answer: …)*

---

## 5) Configuration Knobs (for your app)

- **Learner level:** A1 / A2 / B1 / B2 (controls vocab and sentence length)
- **Explanation language:** English / Chinese
- **Quiz size:** 3–10
- **Register focus:** neutral by default; allow “casual” and “formal” toggles
- **Review source:** last N saved words or current session words

---

### Example Prompt Bundle (ready to paste)

**User:** `/cmp wegen | weil`  
**Bot:**  
**TL;DR:** *„wegen“ = preposition (usually Genitiv), „weil“ = subordinating conjunction.*  
**Mini table:**  
- **Meaning:** cause vs. because  
- **Grammar:** `wegen` + Genitiv; `weil` sends verb to the end  
- **Register:** neutral; both common  
- **Examples:**  
  - **wegen:** *Wegen des Regens* bleiben wir zu Hause.  
  - **weil:** Wir bleiben zu Hause, **weil** es regnet.

---

*Tip: Start with the Core set; add “Pronunciation Coach” and “Error Fix‑it” once users settle in.*
