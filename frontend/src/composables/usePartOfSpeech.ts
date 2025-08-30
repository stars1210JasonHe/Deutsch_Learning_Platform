/**
 * Composable for Part of Speech display utilities
 * Used across components to provide consistent verb type displays
 */

export const usePartOfSpeech = () => {
  const getPosDisplay = (pos: string, verbProps?: any): string => {
    if (!pos) return 'unknown'
    
    // Handle complex POS combinations (pipe-separated)
    if (pos.includes('|')) {
      const posTypes = pos.split('|').map(p => p.trim().toLowerCase())
      
      // Enhanced verb display using database properties for verb combinations
      if (posTypes.includes('verb') && verbProps) {
        const parts = ['Verb']
        
        // Add other POS types
        const otherPoses = posTypes.filter(p => p !== 'verb')
        if (otherPoses.length > 0) {
          const otherDisplays = otherPoses.map(p => getSinglePosDisplay(p)).filter(Boolean)
          if (otherDisplays.length > 0) {
            parts.push(`/ ${otherDisplays.join(' / ')}`)
          }
        }
        
        // Add verb properties
        if (verbProps.reflexive) {
          parts.push('(reflexive)')
        }
        
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
        
        return parts.join(' ')
      }
      
      // Regular complex POS display (no verb props)
      const displays = posTypes.map(p => getSinglePosDisplay(p)).filter(Boolean)
      return displays.join(' / ')
    }
    
    // Enhanced single verb display using database properties
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
    
    // Single POS display
    return getSinglePosDisplay(pos)
  }

  const getSinglePosDisplay = (pos: string): string => {
    if (!pos) return 'unknown'
    
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
      'partizip': 'Participle',
      'phrase': 'Phrase',
      'abbreviation': 'Abbreviation',
      'interj': 'Interjection'
    }
    
    return posDisplays[pos.toLowerCase()] || pos.charAt(0).toUpperCase() + pos.slice(1)
  }

  const getPosClass = (pos: string): string => {
    if (!pos) return 'bg-gray-100 text-gray-800'
    
    // All POS types should use green as requested by user
    return 'bg-green-100 text-green-800'
  }

  const getPosAbbreviation = (pos: string): string => {
    if (!pos) return '?'
    
    // Handle complex POS combinations
    if (pos.includes('|')) {
      const posTypes = pos.split('|').map(p => p.trim().toLowerCase())
      const abbreviations = posTypes.map(p => getSinglePosAbbreviation(p)).filter(Boolean)
      return abbreviations.join('/')
    }
    
    return getSinglePosAbbreviation(pos)
  }

  const getSinglePosAbbreviation = (pos: string): string => {
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
      'partizip': 'PART',
      'phrase': 'PHR',
      'abbreviation': 'ABBR',
      'interj': 'INTERJ'
    }
    
    return abbreviations[pos.toLowerCase()] || pos.toUpperCase()
  }

  const isVerbType = (pos: string): boolean => {
    if (!pos) return false
    
    // Handle complex POS combinations
    if (pos.includes('|')) {
      const posTypes = pos.split('|').map(p => p.trim().toLowerCase())
      return posTypes.some(p => isVerbType(p))
    }
    
    const verbTypes = ['verb', 'vt', 'vi', 'vr', 'aux', 'modal', 'vi_impers', 'vt_impers', 'vi_prep_obj', 'vt_prep_obj']
    return verbTypes.includes(pos.toLowerCase())
  }

  return {
    getPosDisplay,
    getPosClass,
    getPosAbbreviation,
    isVerbType,
    getSinglePosDisplay,
    getSinglePosAbbreviation
  }
}