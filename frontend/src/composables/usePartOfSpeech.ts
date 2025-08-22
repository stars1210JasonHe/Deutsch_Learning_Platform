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
      // Verb types - different shades to distinguish subtypes
      'verb': 'bg-green-100 text-green-800',
      'vt': 'bg-green-100 text-green-800',          // Transitive - green
      'vi': 'bg-blue-100 text-blue-800',           // Intransitive - blue
      'vr': 'bg-teal-100 text-teal-800',           // Reflexive - teal
      'aux': 'bg-indigo-100 text-indigo-800',      // Auxiliary - indigo
      'modal': 'bg-purple-100 text-purple-800',    // Modal - purple
      'vi_impers': 'bg-blue-50 text-blue-700',     // Impersonal intransitive - light blue
      'vt_impers': 'bg-green-50 text-green-700',   // Impersonal transitive - light green
      'vi_prep_obj': 'bg-cyan-100 text-cyan-800',  // Intransitive + prep - cyan
      'vt_prep_obj': 'bg-emerald-100 text-emerald-800', // Transitive + prep - emerald
      
      // Other POS types - distinct colors
      'noun': 'bg-red-100 text-red-800',
      'adj': 'bg-yellow-100 text-yellow-800',
      'adv': 'bg-orange-100 text-orange-800',
      'prep': 'bg-pink-100 text-pink-800',
      'conj': 'bg-amber-100 text-amber-800',
      'pron': 'bg-lime-100 text-lime-800',
      'det': 'bg-violet-100 text-violet-800',
      'art': 'bg-rose-100 text-rose-800',
      'num': 'bg-slate-100 text-slate-800',
      'particle': 'bg-stone-100 text-stone-800',
      'interj': 'bg-zinc-100 text-zinc-800'
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