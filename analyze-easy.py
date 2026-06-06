import json
r = json.load(open('eslint-report.json', 'r', encoding='utf-8'))

# Easy errors
for rule_id in ['await-thenable', 'no-unsafe-enum-comparison', 'simple-import-sort/imports', 'prettier/prettier']:
    full_rule = f'@typescript-eslint/{rule_id}' if not rule_id.startswith(
        'simple') and not rule_id.startswith('prettier') else rule_id
    for f in r:
        for m in f['messages']:
            if m.get('ruleId') == full_rule and m.get('severity') == 2:
                print(
                    f"{m['ruleId']} | {f['filePath']}:{m['line']} | {m['message']}")

print()
print("=== UNBOUND METHOD ===")
for f in r:
    for m in f['messages']:
        if m.get('ruleId') == '@typescript-eslint/unbound-method' and m.get('severity') == 2:
            print(f"{f['filePath']}:{m['line']} | {m['message'][:120]}")
