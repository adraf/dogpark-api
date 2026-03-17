export const FEATURE_ICONS = {
  parking:                'pi-car',
  water:                  'pi-tint',
  agility_equipment:      'pi-flag',
  lighting:               'pi-sun',
  shelter:                'pi-home',
  toilet_facilities:      'pi-user',
  paddling_pool:          'pi-cloud',
  astroturf:              'pi-image',
  separate_small_dog_area:'pi-tag',
  stream:                 'pi-wave-pulse',
  woodland:               'pi-globe',
  rubber_surface:         'pi-circle-fill',
  indoor_area:            'pi-building',
  cafe:                   'pi-shopping-bag',
  wildflower_meadow:      'pi-star',
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
  function icon(key)  { return FEATURE_ICONS[key]  || 'pi-circle' }
  function label(key) { return FEATURE_LABELS[key] || key }
  return { icon, label, FEATURE_ICONS, FEATURE_LABELS }
}
