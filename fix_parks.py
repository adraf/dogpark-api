"""
Post-processing script for parks.json:
1. Filter out non-dog-park results
2. Fix county names (clean up coordinates, sort alphabetically)
3. Better feature inference from descriptions and names
"""
import json
import re

UK_COUNTIES = {
    # England
    'bedfordshire', 'berkshire', 'bristol', 'buckinghamshire', 'cambridgeshire',
    'cheshire', 'cornwall', 'cumbria', 'derbyshire', 'devon', 'dorset', 'durham',
    'east riding of yorkshire', 'east sussex', 'essex', 'gloucestershire',
    'greater london', 'greater manchester', 'hampshire', 'herefordshire',
    'hertfordshire', 'isle of wight', 'kent', 'lancashire', 'leicestershire',
    'lincolnshire', 'london', 'merseyside', 'norfolk', 'north yorkshire',
    'northamptonshire', 'northumberland', 'nottinghamshire', 'oxfordshire',
    'rutland', 'shropshire', 'somerset', 'south yorkshire', 'staffordshire',
    'suffolk', 'surrey', 'tyne and wear', 'warwickshire', 'west midlands',
    'west sussex', 'west yorkshire', 'wiltshire', 'worcestershire',
    # Devolved
    'wales', 'scotland', 'northern ireland',
    # Scottish regions
    'aberdeenshire', 'angus', 'argyll and bute', 'clackmannanshire',
    'dumfries and galloway', 'dundee', 'east ayrshire', 'east dunbartonshire',
    'east lothian', 'east renfrewshire', 'edinburgh', 'falkirk', 'fife',
    'glasgow', 'highland', 'inverclyde', 'midlothian', 'moray',
    'north ayrshire', 'north lanarkshire', 'orkney', 'perth and kinross',
    'renfrewshire', 'scottish borders', 'shetland', 'south ayrshire',
    'south lanarkshire', 'stirling', 'west dunbartonshire', 'west lothian',
    # Welsh
    'blaenau gwent', 'bridgend', 'caerphilly', 'cardiff', 'carmarthenshire',
    'ceredigion', 'conwy', 'denbighshire', 'flintshire', 'gwynedd',
    'isle of anglesey', 'merthyr tydfil', 'monmouthshire', 'neath port talbot',
    'newport', 'pembrokeshire', 'powys', 'rhondda cynon taf', 'swansea',
    'torfaen', 'vale of glamorgan', 'wrexham',
}

# Keywords that suggest it's NOT a secure dog park
EXCLUDE_KEYWORDS = [
    'cricket', 'football', 'stadium', 'golf course', 'tennis',
    'bowling', 'rugby', 'athletics', 'leisure centre', 'swimming',
    'hospital', 'school', 'college', 'university', 'church', 'cathedral',
    'museum', 'gallery', 'shopping', 'supermarket', 'hotel', 'restaurant',
    'pub', 'bar', 'cafe only', 'car park only', 'cemetery', 'graveyard',
]

# Keywords that confirm it IS a dog park
INCLUDE_KEYWORDS = [
    'dog', 'canine', 'hound', 'puppy', 'pup', 'pooch', 'secure', 'enclosed',
    'fenced', 'paddock', 'field', 'park', 'walking', 'exercise', 'off lead',
    'off-lead', 'agility',
]

def is_valid_park(park):
    text = ' '.join([
        park.get('name', ''),
        park.get('description', ''),
        park.get('address', ''),
    ]).lower()
    
    # Exclude if clearly not a dog park
    for kw in EXCLUDE_KEYWORDS:
        if kw in text and not any(dk in text for dk in ['dog', 'canine', 'hound']):
            return False
    
    # Must have at least one dog-related keyword
    return any(kw in text for kw in INCLUDE_KEYWORDS)

def fix_county(park):
    address = park.get('address', '')
    current = park.get('county', '').strip().lower()
    
    # If it looks like coordinates or is empty/weird, extract from address
    if re.match(r'^[\d\s\.\-,]+$', current) or not current or len(current) < 3:
        # Try to extract county from address parts
        parts = [p.strip() for p in address.split(',')]
        # UK addresses: last part is country, second to last often postcode or county
        for part in reversed(parts):
            part_clean = part.strip().lower()
            # Skip postcode, country names, empty
            if re.search(r'[A-Z]{1,2}\d', part, re.I): continue
            if part_clean in ['uk', 'united kingdom', 'england', 'gb', 'great britain']: continue
            if len(part_clean) < 3: continue
            # Check if it matches a known county
            for county in UK_COUNTIES:
                if county in part_clean or part_clean in county:
                    return county.title()
            # Use it anyway if it looks reasonable
            if len(part_clean) > 3 and not re.match(r'^[\d\s\.\-,]+$', part_clean):
                return part.strip().title()
    
    # Clean up existing county
    for county in UK_COUNTIES:
        if county in current:
            return county.title()
    
    return park.get('county', '').strip().title() or 'Unknown'

def infer_features(park):
    existing = park.get('features') or []
    text = ' '.join([
        park.get('name', ''),
        park.get('description', ''),
        park.get('address', ''),
        park.get('opening_hours', '') or '',
    ]).lower()

    feature_map = {
        'parking':                 ['parking', 'car park', 'free parking'],
        'water':                   ['water', 'fresh water', 'tap water', 'water bowl', 'hydrant', 'water point'],
        'agility_equipment':       ['agility', 'obstacle', 'jumps', 'tunnel', 'equipment'],
        'lighting':                ['lighting', 'flood lit', 'floodlit', 'lit up', 'evening sessions', 'night'],
        'toilet_facilities':       ['toilet', 'wc', 'restroom', 'facilities', 'bathroom'],
        'shelter':                 ['shelter', 'covered', 'barn', 'shed', 'undercover'],
        'cafe':                    ['cafe', 'coffee', 'refreshments', 'snacks', 'tea', 'drinks', 'food', 'lake house cafe'],
        'paddling_pool':           ['paddling pool', 'splash', 'pool', 'dip'],
        'woodland':                ['woodland', 'woods', 'forest', 'trees', 'wooded'],
        'astroturf':               ['astroturf', 'artificial grass', 'all weather', 'all-weather', 'rubber crumb'],
        'separate_small_dog_area': ['small dog', 'small dogs', 'separate area', 'puppy area', 'little dogs'],
        'stream':                  ['stream', 'river', 'brook', 'beck', 'burn', 'water feature', 'lake', 'pond'],
        'indoor_area':             ['indoor', 'inside', 'undercover', 'covered area', 'barn'],
        'wildflower_meadow':       ['wildflower', 'meadow', 'wild flowers', 'nature'],
    }

    features = list(existing)
    for feature, keywords in feature_map.items():
        if feature not in features:
            if any(kw in text for kw in keywords):
                features.append(feature)

    return list(dict.fromkeys(features))

# Load
with open('data/parks.json') as f:
    parks = json.load(f)

print(f'Starting with {len(parks)} parks')

# Filter
parks = [p for p in parks if is_valid_park(p)]
print(f'After filtering: {len(parks)} parks')

# Fix counties and features
for p in parks:
    p['county'] = fix_county(p)
    p['features'] = infer_features(p)
    p['is_fully_enclosed'] = True
    p['is_secure'] = True

# Remove Unknown county parks
parks = [p for p in parks if p['county'] != 'Unknown']
print(f'After county fix: {len(parks)} parks')

# Sort by county for cleanliness
parks.sort(key=lambda p: (p.get('county', ''), p.get('name', '')))

# Save
with open('data/parks.json', 'w') as f:
    json.dump(parks, f, indent=2)

# Stats
counties = sorted(set(p['county'] for p in parks))
with_features = sum(1 for p in parks if p.get('features'))
with_images = sum(1 for p in parks if p.get('images'))
print(f'Counties ({len(counties)}): {", ".join(counties[:10])}...')
print(f'Parks with features: {with_features}')
print(f'Parks with images: {with_images}')
print('Done!')
