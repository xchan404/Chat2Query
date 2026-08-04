import json

spec = json.load(open('openapi.json'))

for sname in ['ChatRequest', 'ChatResponse', 'SQLResultOut', 'CitationOut', 'ConversationOut', 'ConversationDetailOut', 'MessageOut']:
    if sname in spec['components']['schemas']:
        print(f"=== {sname} ===")
        print(json.dumps(spec['components']['schemas'][sname], indent=2))
        print()
