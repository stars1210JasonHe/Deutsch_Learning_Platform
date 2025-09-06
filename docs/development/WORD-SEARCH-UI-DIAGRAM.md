# Word Search Results Screen - ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🔍 German Word Search Results                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                            📝 Word Result Card                              │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Header Section ──────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   🗣️ der BAUM         🔊 📖 ⭐ 📚                                          │  │
│  │   ├─ Article (blue)   │  │  │  └─ Add to SRS Button                      │  │
│  │   ├─ Word (bold)      │  │  └─ Favorite Button                           │  │
│  │   │                   │  └─ Speech Button                                 │  │
│  │   └─ Plural: Bäume    └─ Speech Button (word)                            │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Word Properties ─────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   🏷️ NOUN     🔵 der     🟢 separable     🟡 haben                       │  │
│  │      └─POS       └─Article  └─Verb prop    └─Auxiliary                    │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Noun Properties (Purple Background) ────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   📋 Noun Properties                                                      │  │
│  │   ┌─────────────┬─────────────┬─────────────┐                           │  │
│  │   │ Plural:     │ Genitive:   │ Declension: │                           │  │
│  │   │ Bäume       │ des Baums   │ Strong      │                           │  │
│  │   └─────────────┴─────────────┴─────────────┘                           │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Meanings (Gray Background) ──────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   💬 Meaning                                                              │  │
│  │   EN: tree, trunk                                                        │  │
│  │   中文: 树，树干                                                             │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Verb Conjugation Tables (Dynamic Grid) ─────────────────────────────────┐  │
│  │                                                                           │  │
│  │   🔄 Conjugation                                                          │  │
│  │                                                                           │  │
│  │   ┌─ Präsens (Blue) ──┐ ┌─ Präteritum (Green) ┐ ┌─ Perfekt (Purple) ──┐ │  │
│  │   │                  │ │                      │ │                      │ │  │
│  │   │ ich     bringe   │ │ ich      brachte     │ │ ich    habe gebracht │ │  │
│  │   │ du      bringst  │ │ du       brachtest   │ │ du     hast gebracht │ │  │
│  │   │ er/sie  bringt   │ │ er/sie   brachte     │ │ er/sie hat gebracht  │ │  │
│  │   │ wir     bringen  │ │ wir      brachten    │ │ wir    haben gebracht│ │  │
│  │   │ ihr     bringt   │ │ ihr      brachtet    │ │ ihr    habt gebracht │ │  │
│  │   │ sie/Sie bringen  │ │ sie/Sie  brachten    │ │ sie/Sie haben gebracht│ │ │
│  │   │                  │ │                      │ │                      │ │  │
│  │   └──────────────────┘ └──────────────────────┘ └──────────────────────┘ │  │
│  │                                                                           │  │
│  │   ┌─ Imperativ (Red) ─────────────────────────────────────────────────┐   │  │
│  │   │                                                                   │   │  │
│  │   │ du        bring!                                                  │   │  │
│  │   │ ihr       bringt!                                                 │   │  │
│  │   │ Sie       bringen Sie!                                            │   │  │
│  │   │                                                                   │   │  │
│  │   └───────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Example Sentence (Gray Background) ──────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   📝 Example                                                              │  │
│  │   DE: Ich bringe dir das Buch. 🔊                                        │  │
│  │   EN: I bring you the book. 🔊                                           │  │
│  │   中文: 我给你带书。🔊                                                        │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                       🤔 Word Not Found - Suggestions Screen                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                         🤔 Word Suggestions Card                            │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ Not Found Header ────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │                              🤔                                           │  │
│  │                           BRINGN                                          │  │
│  │                      Word not found                                       │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌─ Suggestions List ────────────────────────────────────────────────────────┐  │
│  │                                                                           │  │
│  │   🔍 Did you mean one of these?                                           │  │
│  │                                                                           │  │
│  │   ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │   │ bringen    🏷️ VERB                         to bring, to take │ │   │  │
│  │   └───────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                           │  │
│  │   ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │   │ Bringe     🏷️ NOUN                            a river name   │ │   │  │
│  │   └───────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                           │  │
│  │   ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │   │ Ring       🏷️ NOUN                              ring, circle │ │   │  │
│  │   └───────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

## Screen Components Explanation:

### 1. Word Found Screen:
- **Header**: Word with article (color-coded: der=blue, die=pink, das=gray) + action buttons
- **Properties**: POS tags, verb properties (separable, auxiliary) as colored badges
- **Noun/Verb Specific**: Dynamic property boxes with relevant grammatical information
- **Meanings**: Multi-language translations (EN/中文) in gray background
- **Conjugation Tables**: 
  - Dynamic grid (2-3 columns based on available tenses)
  - Color-coded tenses (Präsens=blue, Präteritum=green, Perfekt=purple)
  - Imperativ shown separately in red styling
- **Examples**: Sample sentences with speech buttons for each language

### 2. Word Not Found Screen:
- **Not Found Header**: 🤔 emoji with searched word and "Word not found" message
- **Suggestions List**: Clickable suggestions with word + POS tag + brief meaning
- **Hover Effects**: Suggestions highlight on hover with blue border

### 3. Color Coding System:
- **Articles**: der (blue), die (pink), das (gray)
- **Tenses**: Präsens (blue), Präteritum (green), Perfekt (purple), Imperativ (red)
- **Properties**: Various background colors for different grammatical features
- **Badges**: Rounded badges with contrasting text colors

### 4. Interactive Elements:
- **🔊 Speech Buttons**: Text-to-speech for German, English, Chinese
- **⭐ Favorite Button**: Toggle word in favorites
- **📚 SRS Button**: Add word to spaced repetition system
- **Clickable Suggestions**: Direct search for suggested words
```