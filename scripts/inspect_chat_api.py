import json

spec = json.load(open('openapi.json'))

paths_to_check = [
    '/api/chat/stream',
    '/api/chat',
    '/api/conversations',
    '/api/conversations/{id}',
    '/api/messages/{id}/citations',
    '/api/messages/{id}/sql'
]

for p in paths_to_check:
    if p in spec['paths']:
        print(f"=== {p} ===")
        print(json.dumps(spec['paths'][p], indent=2)[:1000])
        print()

for name, schema in spec['components']['schemas'].items():
    if any(k in name.lower() for k in ['chat', 'message', 'conversation', 'citation', 'sql', 'stream']):
        print(f"=== SCHEMA: {name} ===")
        print(json.dumps(schema, indent=2)[:600])
        print()
