import sys, json
sys.stdout.reconfigure(encoding='utf-8')
data = open(r'C:\Users\alaaa\.gemini\antigravity\brain\1abcf5ff-4819-4c58-8fae-6cff813547a0\.system_generated\steps\1921\content.md', encoding='utf-8').read()
start = data.find('{')
obj = json.loads(data[start:])

# Check schemas for all defs
defs = obj.get('components', {}).get('schemas', {})

targets = ['/discover_hybrid', '/discover_protocol', '/discover_protocol_v1', '/partial-reprogramming', '/chat_proxy']
for path in targets:
    info = obj['paths'].get(path, {})
    for method, details in info.items():
        body = details.get('requestBody', {})
        summary = details.get('summary', 'no summary')
        print(f'=== {method.upper()} {path} === {summary}')
        schema_ref = body.get('content', {}).get('application/json', {}).get('schema', {})
        ref = schema_ref.get('$ref', '')
        if ref:
            model_name = ref.split('/')[-1]
            model = defs.get(model_name, {})
            props = model.get('properties', {})
            req = model.get('required', [])
            for k, v in props.items():
                r = '(required)' if k in req else '(optional)'
                t = v.get('type', v.get('$ref','?'))
                d = v.get('default', '')
                print(f'  {k}: {t} {r} default={d}')
        print()
