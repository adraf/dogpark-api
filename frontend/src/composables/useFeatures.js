export const FEATURE_ICON_FILES = {
  parking:                'parking',
  water:                  'blur',
  agility_equipment:      'dumbbell',
  lighting:               'idea',
  shelter:                'home',
  toilet_facilities:      'toilet-paper',
  paddling_pool:          'wave-lines',
  astroturf:              'sabzeh',
  separate_small_dog_area:'dog',
  stream:                 'wave-lines',
  woodland:               'oak-tree',
  rubber_surface:         'expand',
  indoor_area:            'front-door',
  cafe:                   'cafe',
  wildflower_meadow:      'flower-doodle',
}

export const FEATURE_LABELS = {
  parking:                'Parking',
  water:                  'Fresh water',
  agility_equipment:      'Agility equipment',
  lighting:               'Lighting',
  shelter:                'Shelter',
  toilet_facilities:      'Toilets',
  paddling_pool:          'Paddling pool',
  astroturf:              'Astroturf',
  separate_small_dog_area:'Small dog area',
  stream:                 'Stream',
  woodland:               'Woodland',
  rubber_surface:         'All-weather surface',
  indoor_area:            'Indoor area',
  cafe:                   'Cafe',
  wildflower_meadow:      'Wildflower meadow',
}

export function useFeatures() {
  function iconFile(key) {
    return FEATURE_ICON_FILES[key] || null
  }
  function label(key) {
    return FEATURE_LABELS[key] || key
  }
  return { iconFile, label, FEATURE_LABELS }
}
