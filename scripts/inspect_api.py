import json

spec = json.load(open('openapi.json'))

# Dump all components schemas related to connections
for name, schema in spec['components']['schemas'].items():
    if any(k in name.lower() for k in ['connection', 'schema', 'table', 'column']):
        print(f'=== {name} ===')
        print(json.dumps(schema, indent=2)[:800])
        print()
