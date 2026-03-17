// Map feature keys to their icons8 PNG filename (without the icons8- prefix and -50.png suffix)
// e.g. water -> icons8-blur-50.png, so the value is 'blur'
// Fill in the correct name for any you have - missing ones fall back to a pi icon

export const FEATURE_ICON_FILES = {
  parking:                'parking',        // icons8-parking-50.png
  water:                  'blur',           // icons8-blur-50.png  ← confirmed
  agility_equipment:      'agility',        // icons8-agility-50.png  ← update if different
  lighting:               'lighting',       // icons8-lighting-50.png ← update if different
  shelter:                'shelter',        // icons8-shelter-50.png  ← update if different
  toilet_facilities:      'toilet',         // icons8-toilet-50.png   ← update if different
  paddling_pool:          'paddling-pool',  // icons8-paddling-pool-50.png ← update if different
  astroturf:              'grass',          // icons8-grass-50.png    ← update if different
  separate_small_dog_area:'dog',            // icons8-dog-50.png      ← update if different
  stream:                 'stream',         // icons8-stream-50.png   ← update if different
  woodland:               'woodland',       // icons8-woodland-50.png ← update if different
  rubber_surface:         'rubber',         // icons8-rubber-50.png   ← update if different
  indoor_area:            'indoor',         // icons8-indoor-50.png   ← update if different
  cafe:                   'cafe',           // icons8-cafe-50.png     ← update if different
  wildflower_meadow:      'flowers',        // icons8-flowers-50.png  ← update if different
}

// Fallback pi icon for anything without a file
export const FEATURE_PI_FALLBACK = {
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
  function iconFile(key) {
    const name = FEATURE_ICON_FILES[key]
    return name ? `/icons8/icons8-${name}-50.png` : null
  }

  function iconFallback(key) {
    return FEATURE_PI_FALLBACK[key] || 'pi-circle'
  }

  function label(key) {
    return FEATURE_LABELS[key] || key
  }

  return { iconFile, iconFallback, label, FEATURE_LABELS }
}
