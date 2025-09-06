# Translate Mode Feature Specification

## Overview
Add a "Translate Mode" toggle to the search interface that allows users to input words in any language, automatically detect the language, translate to German using OpenAI, and then perform a regular German word search.

## User Flow
1. User toggles "Translate Mode" ON in the search interface
2. User enters a word in any language (English, Chinese, French, etc.)
3. System automatically detects the input language using OpenAI
4. System translates the word to German using OpenAI
5. System performs regular German word search on the translated word
6. Results display both original word and German translation with full word details

## Technical Requirements

### Backend Changes

#### 1. API Endpoint Modification (`app/api/words.py`)
- Add new endpoint: `POST /api/words/translate-search`
- Input: `{"text": "hello", "translate_mode": true}`
- Process:
  1. Detect language using OpenAI
  2. Translate to German using OpenAI  
  3. Search German word in vocabulary database
- Output: Include original text, detected language, German translation, and search results

#### 2. Schema Updates (`app/schemas/word.py`)
```python
class TranslateSearchRequest(BaseModel):
    text: str
    translate_mode: bool = True

class TranslateSearchResponse(BaseModel):
    original_text: str
    detected_language: str
    german_translations: List[TranslationOption]  # Multiple options when ambiguous
    search_results: Optional[WordSearchResponse]  # None if user needs to select translation

class TranslationOption(BaseModel):
    german_word: str
    context: str  # e.g., "financial institution", "river bank"
```

#### 3. OpenAI Service Integration (`app/services/openai_service.py`)
- Enhance `detect_language(text)` function with ambiguity detection
- Add `translate_to_german(text, source_language)` function
- Use existing OpenAI client and models
- AI determines when word is ambiguous and suggests alternative language

### Frontend Changes

#### 1. Search Interface (`frontend/src/views/Home.vue`)
- Add translate mode toggle switch/button
- Modify search form to handle translate mode
- Update search results display to show:
  - Original word
  - Detected language
  - German translation
  - Regular word search results

#### 2. State Management (`frontend/src/stores/search.ts`)
- Add `translateMode: boolean` state
- Add `toggleTranslateMode()` action
- Modify search function to use translate endpoint when enabled

## Implementation Details

### Enhanced Language Detection Strategy
- Use OpenAI to identify source language with ambiguity detection
- When word might be German, check for alternative language possibilities
- Handle common languages: English, Chinese, French, Spanish, Italian, etc.
- AI determines when word is ambiguous enough to show user choice
- Fallback to "unknown" if detection fails

#### Ambiguous Word Handling
For words that could be multiple languages (e.g., "hell" = German "bright" OR English "underworld"):
1. **AI detects potential ambiguity** - when confidence suggests word could be German AND another language
2. **Present user choice**:
   ```
   This word could be:
   [ ] German word "hell" (bright, light) → search German database
   [ ] English word "hell" → translate to German first
   ```
3. **User selects approach** - direct German search OR translation workflow
4. **Reduces server load** - only shown when AI determines uncertainty exists

### Translation Strategy  
- Only translate single words (not phrases/sentences)
- Use OpenAI for accurate word-level translation
- Request multiple translation options when word has multiple meanings
- Present selection UI when multiple German translations exist

### Search Integration
- After translation, use existing German word search logic
- Search for exact translated German word
- Return full word details (definitions, examples, grammar, etc.)

### Error Handling

#### 1. Language Detection Results
- **Cannot detect language**: Show error message "Unable to detect language. Please try a different word or switch to normal search mode."
- **Clearly German word**: Skip translation, go directly to German word search
- **Ambiguous word (German + other)**: Present user with choice dialog
- **Clearly non-German**: Proceed with translation workflow

#### 2. Translation Results
- **No corresponding German word**: Show message "No German translation found for this word. Please try a synonym or check spelling."
- **Multiple German translations**: Present user with selection interface (similar to relevant words module):
  ```
  Multiple translations found for "bank":
  [ ] Bank (financial institution)
  [ ] Ufer (river bank) 
  [ ] Sandbank (sandbank)
  ```
- User clicks desired option to proceed with German word search

#### 3. Other Failures
- Translation API failures
- No German word found in vocabulary database
- API rate limits

### UI/UX Design
- Clear toggle for translate mode ON/OFF
- Visual indication when translate mode is active
- Display translation process (original → German → results)
- Maintain existing search functionality when translate mode OFF

## Example User Interactions

### Simple Case (Clearly Non-German)
```
User Input: "hello" (with translate mode ON)
System Detects: English (high confidence)
System Translates: "hallo"  
System Searches: German word "hallo"
Results Display:
  Original: hello (English)
  German: hallo
  [Full German word details for "hallo"]
```

### Ambiguous Case (Could be German or Other Language)
```
User Input: "hell" (with translate mode ON)
System Detects: Ambiguous (could be German or English)
System Shows Choice:
  [ ] Search German word "hell" (bright, light)
  [ ] Translate English "hell" to German (Hölle)
User Selects: German option
Results Display:
  [German word details for "hell" meaning "bright"]
```

## Files to Modify
1. `app/api/words.py` - New translate-search endpoint
2. `app/schemas/word.py` - New request/response schemas  
3. `app/services/openai_service.py` - Language detection & translation functions
4. `frontend/src/views/Home.vue` - UI toggle and search modifications
5. `frontend/src/stores/search.ts` - State management for translate mode

## Success Criteria
- [ ] Toggle works correctly (ON/OFF states)
- [ ] Language detection works for major languages
- [ ] Translation to German is accurate for single words
- [ ] German word search functions normally after translation
- [ ] UI clearly shows original word, translation, and results
- [ ] Error handling works for edge cases
- [ ] Performance is acceptable (< 2 seconds for full flow)

## Future Enhancements (Not in Scope)
- Translate full sentences/phrases
- Multiple translation options
- Translation history
- Support for more languages
- Offline translation capabilities