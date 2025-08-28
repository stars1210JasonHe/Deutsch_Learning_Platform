/**
 * Composable for Part of Speech display utilities
 * Used across components to provide consistent verb type displays
 */

export const usePartOfSpeech = () => {
  const getPosDisplay = (pos: string, verbProps?: any): string => {
    if (!pos) return 'unknown'
    
    // Enhanced verb display using database properties
    if (pos.toLowerCase() === 'verb' && verbProps) {
      const parts = ['Verb']
      
      // Add reflexive
      if (verbProps.reflexive) {
        parts.push('(reflexive)')
      }
      
      // Add separable
      if (verbProps.separable) {
        parts.push('(separable)')
      }
      
      // Add transitivity info from valency
      if (verbProps.cases && verbProps.cases.length > 0) {
        if (verbProps.cases.includes('accusative')) {
          parts.push('(transitive)')
        } else if (verbProps.cases.includes('dative')) {
          parts.push('(intransitive + dat)')
        }
      }
      
      // If we have enhanced info, return it
      if (parts.length > 1) {
        return parts.join(' ')
      }
    }
    
    const posDisplays: { [key: string]: string } = {
      // Basic verb types (fallback for cases without verb_props)
      'verb': 'Verb',
      'vt': 'Verb (transitive)',
      'vi': 'Verb (intransitive)', 
      'vr': 'Verb (reflexive)',
      'aux': 'Auxiliary verb',
      'modal': 'Modal verb',
      'vi_impers': 'Verb (impersonal)',
      'vt_impers': 'Verb (impersonal transitive)',
      'vi_prep_obj': 'Verb (intransitive + prep)',
      'vt_prep_obj': 'Verb (transitive + prep)',
      
      // Other POS types
      'noun': 'Noun',
      'adj': 'Adjective',
      'adv': 'Adverb',
      'prep': 'Preposition',
      'conj': 'Conjunction',
      'pron': 'Pronoun',
      'det': 'Determiner',
      'art': 'Article',
      'num': 'Number',
      'particle': 'Particle',
      'interj': 'Interjection'
    }
    
    return posDisplays[pos.toLowerCase()] || pos.charAt(0).toUpperCase() + pos.slice(1)
  }

  const getPosClass = (pos: string): string => {
    if (!pos) return 'bg-gray-100 text-gray-800'
    
    const posClasses: { [key: string]: string } = {
      // All POS types use green color scheme for consistency
      'verb': 'bg-green-100 text-green-800',
      'vt': 'bg-green-100 text-green-800',
      'vi': 'bg-green-100 text-green-800',
      'vr': 'bg-green-100 text-green-800',
      'aux': 'bg-green-100 text-green-800',
      'modal': 'bg-green-100 text-green-800',
      'vi_impers': 'bg-green-100 text-green-800',
      'vt_impers': 'bg-green-100 text-green-800',
      'vi_prep_obj': 'bg-green-100 text-green-800',
      'vt_prep_obj': 'bg-green-100 text-green-800',
      
      // Other POS types also use green
      'noun': 'bg-green-100 text-green-800',
      'adj': 'bg-green-100 text-green-800',
      'adv': 'bg-green-100 text-green-800',
      'prep': 'bg-green-100 text-green-800',
      'conj': 'bg-green-100 text-green-800',
      'pron': 'bg-green-100 text-green-800',
      'det': 'bg-green-100 text-green-800',
      'art': 'bg-green-100 text-green-800',
      'num': 'bg-green-100 text-green-800',
      'particle': 'bg-green-100 text-green-800',
      'interj': 'bg-green-100 text-green-800'
    }
    
    return posClasses[pos.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  const getPosAbbreviation = (pos: string): string => {
    if (!pos) return '?'
    
    const abbreviations: { [key: string]: string } = {
      'verb': 'V',
      'vt': 'VT',
      'vi': 'VI',
      'vr': 'VR', 
      'aux': 'AUX',
      'modal': 'MOD',
      'vi_impers': 'VI-imp',
      'vt_impers': 'VT-imp',
      'vi_prep_obj': 'VI+prep',
      'vt_prep_obj': 'VT+prep',
      'noun': 'N',
      'adj': 'ADJ',
      'adv': 'ADV',
      'prep': 'PREP',
      'conj': 'CONJ',
      'pron': 'PRON',
      'det': 'DET',
      'art': 'ART',
      'num': 'NUM',
      'particle': 'PART',
      'interj': 'INTERJ'
    }
    
    return abbreviations[pos.toLowerCase()] || pos.toUpperCase()
  }

  const isVerbType = (pos: string): boolean => {
    if (!pos) return false
    const verbTypes = ['verb', 'vt', 'vi', 'vr', 'aux', 'modal', 'vi_impers', 'vt_impers', 'vi_prep_obj', 'vt_prep_obj']
    return verbTypes.includes(pos.toLowerCase())
  }

  return {
    getPosDisplay,
    getPosClass,
    getPosAbbreviation,
    isVerbType
  }
}