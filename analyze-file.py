import json
r = json.load(open('eslint-report.json', 'r', encoding='utf-8'))
target = 'G:\\iMato\\src\\app\\core\\services\\pricing.service.ts'
for f in r:
    if f['filePath'] == target:
        for m in f['messages']:
            if m.get('severity') == 2:
                print(f"L{m['line']:4d} | {m['message'][:100]}")
