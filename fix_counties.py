"""
Fix county names in parks.json using postcodes.io batch lookup.
For parks without postcodes, maps towns to known UK counties.
"""
import json
import re
import time
import requests

# Comprehensive town/village to county mapping for common mismatches
TOWN_TO_COUNTY = {
    # Greater London
    'london': 'Greater London', 'rainham': 'Greater London',
    'crumpsall': 'Greater Manchester', 'urmston': 'Greater Manchester',
    'eccles': 'Greater Manchester', 'romiley': 'Greater Manchester',
    'shaw': 'Greater Manchester', 'middleton': 'Greater Manchester',
    'leigh': 'Greater Manchester', 'astley': 'Greater Manchester',
    # Lancashire
    'burscough': 'Lancashire', 'scarisbrick': 'Lancashire', 'hoscar': 'Lancashire',
    'midge hall': 'Lancashire', 'new longton': 'Lancashire', 'longton': 'Lancashire',
    'walton-le-dale': 'Lancashire', 'goosnargh': 'Lancashire', 'greenhalgh': 'Lancashire',
    'forton': 'Lancashire', 'singleton': 'Lancashire', 'mawdesley': 'Lancashire',
    'hesketh bank': 'Lancashire', 'kelbrook': 'Lancashire', 'lytham st annes': 'Lancashire',
    'tarbock green': 'Merseyside', 'rainhill': 'Merseyside', 'birkenhead': 'Merseyside',
    'thurstaston': 'Merseyside', 'formby': 'Merseyside',
    # Yorkshire
    'burley in wharfedale': 'West Yorkshire', 'menston': 'West Yorkshire',
    'calverley': 'West Yorkshire', 'horsforth': 'West Yorkshire',
    'gildersome': 'West Yorkshire', 'birkenshaw': 'West Yorkshire',
    'pudsey': 'West Yorkshire', 'northowram': 'West Yorkshire',
    'southowram': 'West Yorkshire', 'farnley': 'West Yorkshire',
    'yeadon': 'West Yorkshire', 'oakworth': 'West Yorkshire',
    'east morton': 'West Yorkshire', 'cowling': 'West Yorkshire',
    'silkstone common': 'South Yorkshire', 'worsbrough': 'South Yorkshire',
    'conisbrough': 'South Yorkshire', 'todwick': 'South Yorkshire',
    'ecclesfield': 'South Yorkshire', 'penistone': 'South Yorkshire',
    'boroughbridge': 'North Yorkshire', 'minskip': 'North Yorkshire',
    'kirklington': 'North Yorkshire', 'knapton': 'North Yorkshire',
    'east cowton': 'North Yorkshire', 'south kilvington': 'North Yorkshire',
    'ingleton': 'North Yorkshire', 'thornton': 'North Yorkshire',
    # Worcestershire
    'claines': 'Worcestershire', 'hallow': 'Worcestershire', 'bushley': 'Worcestershire',
    'hartlebury': 'Worcestershire', 'blakedown': 'Worcestershire',
    'hunnington': 'Worcestershire', 'iverley': 'Worcestershire',
    'stourport-on-severn': 'Worcestershire', 'great wyrley': 'Staffordshire',
    'muckley corner': 'Staffordshire', 'dunston heath': 'Staffordshire',
    'cocknage': 'Staffordshire', 'halmerend': 'Staffordshire',
    'coven': 'Staffordshire', 'kinver': 'Staffordshire',
    # Cheshire
    'cuddington': 'Cheshire', 'lower whitley': 'Cheshire', 'gawsworth': 'Cheshire',
    'hale barns': 'Cheshire', 'mottram in longdendale': 'Cheshire',
    # Warwickshire
    'berkswell': 'Warwickshire', 'hampton in arden': 'Warwickshire',
    'meriden': 'Warwickshire', 'clifford chambers': 'Warwickshire',
    'harbury': 'Warwickshire', 'barford': 'Warwickshire',
    'radway': 'Warwickshire', 'shotteswell': 'Warwickshire',
    'danzey green': 'Warwickshire',
    # Northamptonshire
    'mears ashby': 'Northamptonshire', 'kislingbury': 'Northamptonshire',
    'creaton': 'Northamptonshire', 'weedon': 'Northamptonshire',
    'sywell': 'Northamptonshire', 'moulton': 'Northamptonshire',
    # Suffolk
    'bury st edmunds': 'Suffolk', 'grundisburgh': 'Suffolk', 'haughley': 'Suffolk',
    'fressingfield': 'Suffolk', 'brockford green': 'Suffolk', 'wetherden': 'Suffolk',
    'great cornard': 'Suffolk', 'aldeby': 'Norfolk', 'felthorpe': 'Norfolk',
    'salhouse': 'Norfolk', 'foxley': 'Norfolk', 'tuttington': 'Norfolk',
    'winterton-on-sea': 'Norfolk',
    # Essex
    'writtle': 'Essex', 'bicknacre': 'Essex', 'rettendon common': 'Essex',
    'danbury': 'Essex', 'birchanger': 'Essex', 'rayne': 'Essex',
    'ford end': 'Essex', 'coxtie green rd': 'Essex',
    # Hertfordshire
    'barkway': 'Hertfordshire', 'lilley': 'Hertfordshire', 'st ippolyts': 'Hertfordshire',
    # Cambridgeshire
    'haslingfield': 'Cambridgeshire', 'fenstanton': 'Cambridgeshire',
    'grantchester': 'Cambridgeshire', 'little downham': 'Cambridgeshire',
    'somersham': 'Cambridgeshire',
    # Lincolnshire
    'alkborough': 'Lincolnshire', 'billinghay': 'Lincolnshire',
    'nocton': 'Lincolnshire', 'scampton': 'Lincolnshire', 'huttoft': 'Lincolnshire',
    'bitchfield': 'Lincolnshire', 'foston': 'Lincolnshire', 'norton disney': 'Lincolnshire',
    'north muskham': 'Lincolnshire', 'west pinchbeck': 'Lincolnshire',
    'walcott': 'Lincolnshire', 'belton': 'Lincolnshire', 'bawtry': 'Nottinghamshire',
    'blidworth': 'Nottinghamshire', 'kirkby in ashfield': 'Nottinghamshire',
    'radcliffe on trent': 'Nottinghamshire', 'underwood': 'Nottinghamshire',
    'thurgarton': 'Nottinghamshire', 'old whittington': 'Derbyshire',
    'whatstandwell': 'Derbyshire', 'smalley': 'Derbyshire', 'ripley': 'Derbyshire',
    # Shropshire
    'cressage': 'Shropshire', 'shawbury': 'Shropshire', 'whixall': 'Shropshire',
    'pave lane': 'Shropshire',
    # Somerset
    'staple fitzpaine': 'Somerset', 'chipstable': 'Somerset', 'emborough': 'Somerset',
    'binegar': 'Somerset', 'tonedale': 'Somerset', 'chew magna': 'Somerset',
    'cleeve': 'Somerset', 'badgworth': 'Somerset',
    # Devon
    'bovey tracey': 'Devon', 'daccombe': 'Devon', 'dainton': 'Devon',
    'brampford speke': 'Devon', 'clyst honiton': 'Devon', 'hemyock': 'Devon',
    'bratton fleming': 'Devon', 'thorverton': 'Devon', 'kentisbeare': 'Devon',
    'mutterton': 'Devon', 'appledore': 'Devon', 'great torrington': 'Devon',
    # Cornwall
    'zelah': 'Cornwall', 'goonhavern': 'Cornwall', 'roche': 'Cornwall',
    'grampound': 'Cornwall', 'quintrell downs': 'Cornwall', 'st columb': 'Cornwall',
    'st erth': 'Cornwall',
    # Dorset
    'three legged cross': 'Dorset', 'todber': 'Dorset', 'crossways': 'Dorset',
    'west wellow': 'Hampshire', 'headbourne worthy': 'Hampshire',
    'headley': 'Hampshire', 'hordle': 'Hampshire', 'east meon': 'Hampshire',
    'upham': 'Hampshire', 'moundsmere': 'Hampshire', 'hartley wintney': 'Hampshire',
    'portchester': 'Hampshire', 'fareham': 'Hampshire',
    # Sussex
    'burwash': 'East Sussex', 'crawley down': 'West Sussex', 'lower dicker': 'East Sussex',
    'barns green': 'West Sussex', 'wisborough green': 'West Sussex',
    'wivelsfield green': 'East Sussex', 'charlwood': 'Surrey', 'dormansland': 'Surrey',
    'felbridge': 'Surrey', 'west horsley': 'Surrey', 'send': 'Surrey',
    # Kent
    'meopham': 'Kent', 'southfleet': 'Kent', 'cliffe': 'Kent',
    'staplehurst': 'Kent', 'wouldham': 'Kent',
    # Gloucestershire
    'churchdown': 'Gloucestershire', 'redmarley d\'abitot': 'Gloucestershire',
    'gorsley': 'Gloucestershire', 'quedgeley': 'Gloucestershire',
    'coalpit heath': 'Gloucestershire', 'thornbury': 'Gloucestershire',
    # Wiltshire
    'grittenham': 'Wiltshire', 'lower south wraxall': 'Wiltshire',
    'wootton rivers': 'Wiltshire', 'whitcombe': 'Dorset',
    # Oxfordshire
    'horton-cum-studley': 'Oxfordshire', 'yarnton': 'Oxfordshire',
    'bletchingdon road': 'Oxfordshire', 'postcombe': 'Oxfordshire',
    'little horwood': 'Buckinghamshire', 'gayhurst': 'Buckinghamshire',
    'stewkley': 'Buckinghamshire', 'wendover': 'Buckinghamshire',
    'bourne end': 'Buckinghamshire',
    # Durham / Northumberland
    'cornforth': 'County Durham', 'coxhoe': 'County Durham',
    'hurworth-on-tees': 'County Durham', 'east grimstead': 'County Durham',
    'throckley': 'Tyne and Wear', 'longframlington': 'Northumberland',
    'ancroft': 'Northumberland', 'newbiggin': 'Northumberland',
    'hareshaw': 'Northumberland',
    # Leicestershire
    'gaddesby': 'Leicestershire', 'cropston': 'Leicestershire',
    'earl shilton': 'Leicestershire', 'long clawson': 'Leicestershire',
    'narborough': 'Leicestershire', 'thurlaston': 'Leicestershire',
    'shepshed': 'Leicestershire', 'barrow upon soar': 'Leicestershire',
    # Bedfordshire
    'ridgmont': 'Bedfordshire', 'kempston': 'Bedfordshire',
    'upper shelton': 'Bedfordshire',
    # Scotland
    'aberdour': 'Fife', 'dunshalt': 'Fife', 'markinch': 'Fife',
    'comrie': 'Tayside', 'coupar angus': 'Tayside', 'old scone': 'Tayside',
    'pencaitland': 'East Lothian', 'cousland': 'Midlothian',
    'hardengreen ln': 'Midlothian', 'winchburgh': 'West Lothian',
    'camelon': 'Falkirk', 'caldercruix': 'North Lanarkshire',
    'glenboig': 'North Lanarkshire', 'cumbernauld': 'North Lanarkshire',
    'gartcosh': 'North Lanarkshire', 'cleland': 'North Lanarkshire',
    'chryston': 'North Lanarkshire', 'balloch': 'West Dunbartonshire',
    'barrhead': 'East Renfrewshire', 'east kilbride': 'South Lanarkshire',
    'elsrickle': 'South Lanarkshire', 'law': 'South Lanarkshire',
    'forth': 'South Lanarkshire', 'carmunnock': 'Glasgow',
    'eaglesham': 'East Renfrewshire', 'burnhouse': 'North Ayrshire',
    'auchenreoch': 'Dumfries and Galloway', 'springholm': 'Dumfries and Galloway',
    'kirkgunzeon': 'Dumfries and Galloway', 'irongray rd': 'Dumfries and Galloway',
    'laigh braidley': 'Ayrshire', 'monkton': 'Ayrshire',
    'dess': 'Aberdeenshire', 'rhynie': 'Aberdeenshire', 'midmar': 'Aberdeenshire',
    'gamrie': 'Aberdeenshire', 'backhill': 'Aberdeenshire', 'kingseat': 'Aberdeenshire',
    'kingswells': 'Aberdeenshire', 'bridge of don': 'Aberdeenshire',
    'lynwilg': 'Highland', 'hardgate': 'Highland',
    # Wales
    'pontllanfraith': 'Caerphilly', 'llanbradach': 'Caerphilly',
    'rhydyfelin': 'Rhondda Cynon Taf', 'pontprennau': 'Cardiff',
    'pontardawe': 'Neath Port Talbot', 'tondu': 'Bridgend', 'pyle': 'Bridgend',
    'sketty': 'Swansea', 'gresford': 'Wrexham', 'llanrwst': 'Conwy',
    'connah\'s quay': 'Flintshire', 'sealand': 'Flintshire',
    'higher kinnerton': 'Flintshire', 'johnstown': 'Wrexham',
    'new radnor': 'Powys', 'st harmon': 'Powys', 'abermule': 'Powys',
    'whitford': 'Flintshire',
    # Northern Ireland
    'dundonald': 'County Down', 'conlig': 'County Down', 'comber': 'County Down',
    'six road ends': 'County Down', 'magheralin': 'County Down',
    'lurgan': 'County Armagh', 'castledawson': 'County Londonderry',
    'six mile water': 'County Antrim',
}

# Known UK counties (lowercase for matching)
KNOWN_COUNTIES = {
    'bedfordshire', 'berkshire', 'bristol', 'buckinghamshire', 'cambridgeshire',
    'cheshire', 'cornwall', 'cumbria', 'derbyshire', 'devon', 'dorset',
    'county durham', 'durham', 'east riding of yorkshire', 'east sussex', 'essex',
    'gloucestershire', 'greater london', 'greater manchester', 'hampshire',
    'herefordshire', 'hertfordshire', 'isle of wight', 'kent', 'lancashire',
    'leicestershire', 'lincolnshire', 'london', 'merseyside', 'norfolk',
    'north yorkshire', 'northamptonshire', 'northumberland', 'nottinghamshire',
    'oxfordshire', 'shropshire', 'somerset', 'south yorkshire', 'staffordshire',
    'suffolk', 'surrey', 'tyne and wear', 'warwickshire', 'west midlands',
    'west sussex', 'west yorkshire', 'wiltshire', 'worcestershire',
    'wales', 'scotland', 'northern ireland',
    'aberdeenshire', 'angus', 'argyll and bute', 'dumfries and galloway',
    'east ayrshire', 'east dunbartonshire', 'east lothian', 'east renfrewshire',
    'edinburgh', 'falkirk', 'fife', 'glasgow', 'highland', 'inverclyde',
    'midlothian', 'moray', 'north ayrshire', 'north lanarkshire', 'perth and kinross',
    'renfrewshire', 'scottish borders', 'south ayrshire', 'south lanarkshire',
    'stirling', 'west dunbartonshire', 'west lothian', 'ayrshire', 'tayside',
    'blaenau gwent', 'bridgend', 'caerphilly', 'cardiff', 'carmarthenshire',
    'ceredigion', 'conwy', 'denbighshire', 'flintshire', 'gwynedd',
    'isle of anglesey', 'merthyr tydfil', 'monmouthshire', 'neath port talbot',
    'newport', 'pembrokeshire', 'powys', 'rhondda cynon taf', 'swansea',
    'torfaen', 'vale of glamorgan', 'wrexham',
    'belfast', 'county antrim', 'county down', 'county armagh',
    'county londonderry', 'county tyrone', 'county fermanagh',
    'perthshire',
}

def geocode_batch(postcodes):
    """Use postcodes.io to get county from postcode."""
    if not postcodes:
        return {}
    try:
        resp = requests.post(
            'https://api.postcodes.io/postcodes',
            json={'postcodes': postcodes},
            timeout=20
        )
        results = resp.json().get('result', [])
        mapping = {}
        for r in results:
            if r and r.get('result'):
                pc = r['query'].upper().replace(' ', '')
                result = r['result']
                county = (
                    result.get('admin_county') or
                    result.get('admin_district') or
                    result.get('region') or ''
                )
                if county:
                    mapping[pc] = county
        return mapping
    except Exception as e:
        print(f'Geocode error: {e}')
        return {}

def fix_county(park, postcode_map):
    """Determine the correct county for a park."""
    # Try postcode lookup first (most reliable)
    postcode = (park.get('postcode') or '').upper().replace(' ', '')
    if postcode and postcode in postcode_map:
        return postcode_map[postcode]

    # Check if current county is already a known county
    current = (park.get('county') or '').strip().lower()
    if current in KNOWN_COUNTIES:
        return park['county'].strip().title()

    # Try town name lookup
    town = (park.get('town') or '').strip().lower()
    if town in TOWN_TO_COUNTY:
        return TOWN_TO_COUNTY[town]

    # Try current county value as a town lookup
    if current in TOWN_TO_COUNTY:
        return TOWN_TO_COUNTY[current]

    # Try to extract county from address
    address = (park.get('address') or '').lower()
    for county in KNOWN_COUNTIES:
        if county in address:
            return county.title()

    # Last resort — use address parts
    parts = [p.strip() for p in (park.get('address') or '').split(',')]
    for part in reversed(parts):
        part_l = part.strip().lower()
        if re.match(r'^[a-z]{1,2}\d', part_l): continue  # postcode
        if part_l in ['uk', 'united kingdom', 'england', 'gb', 'great britain']: continue
        if len(part_l) < 3: continue
        if re.match(r'^[\d\s.\-,]+$', part_l): continue  # coordinates
        if part_l in KNOWN_COUNTIES:
            return part.strip().title()

    return None  # will be removed

# Load
with open('data/parks.json') as f:
    parks = json.load(f)

print(f'Starting: {len(parks)} parks')

# Batch geocode all postcodes
postcodes = list(set(
    p.get('postcode', '').upper().replace(' ', '')
    for p in parks if p.get('postcode')
))
print(f'Geocoding {len(postcodes)} postcodes...')
postcode_map = {}
for i in range(0, len(postcodes), 100):
    batch = postcodes[i:i+100]
    result = geocode_batch(batch)
    postcode_map.update(result)
    time.sleep(0.3)
print(f'Got county data for {len(postcode_map)} postcodes')

# Fix all counties
fixed = 0
unresolved = []
for p in parks:
    new_county = fix_county(p, postcode_map)
    if new_county:
        if new_county != p.get('county'):
            fixed += 1
        p['county'] = new_county
    else:
        unresolved.append({'name': p['name'], 'current_county': p.get('county'), 'address': p.get('address'), 'town': p.get('town')})

print(f'Fixed {fixed} counties')
print(f'\nUnresolved ({len(unresolved)}) — need manual mapping:')
for u in unresolved:
    print(f"  {u['name']} | county: {u['current_county']} | town: {u['town']} | address: {u['address']}")

# Save all parks including unresolved
with open('data/parks.json', 'w') as f:
    json.dump(parks, f, indent=2)

# Show county distribution
from collections import Counter
counties = Counter(p['county'] for p in parks)
print(f'\nFinal: {len(parks)} parks across {len(counties)} counties')
print('\nTop counties:')
for county, count in sorted(counties.items(), key=lambda x: -x[1])[:20]:
    print(f'  {county}: {count}')
