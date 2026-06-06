import json
r = json.load(open('eslint-report.json', 'r', encoding='utf-8'))

# Error count by rule
err_by_rule = {}
# Error count by file
err_by_file = {}
# Error count by rule AND file
err_by_rule_file = {}

for f in r:
    for m in f['messages']:
        if m.get('severity') == 2:
            rid = m['ruleId']
            fp = f['filePath']
            err_by_rule[rid] = err_by_rule.get(rid, 0) + 1
            err_by_file[fp] = err_by_file.get(fp, 0) + 1
            key = (rid, fp)
            err_by_rule_file[key] = err_by_rule_file.get(key, 0) + 1

print("=== BY RULE ===")
for k, v in sorted(err_by_rule.items(), key=lambda x: -x[1]):
    print(f"{k}: {v}")

print("\n=== TOP 20 FILES ===")
for f, cnt in sorted(err_by_file.items(), key=lambda x: -x[1])[:20]:
    short = f.replace('G:\\iMato\\src\\', '')
    print(f"{cnt:4d} | {short}")

print("\n=== FILES WITH MOST no-unsafe-assignment ===")
rule = '@typescript-eslint/no-unsafe-assignment'
for (rid, fp), cnt in sorted(err_by_rule_file.items(), key=lambda x: -x[1]):
    if rid == rule:
        short = fp.replace('G:\\iMato\\src\\', '')
        print(f"{cnt:4d} | {short}")

print("\n=== FILES WITH MOST no-unsafe-member-access ===")
rule = '@typescript-eslint/no-unsafe-member-access'
for (rid, fp), cnt in sorted(err_by_rule_file.items(), key=lambda x: -x[1]):
    if rid == rule:
        short = fp.replace('G:\\iMato\\src\\', '')
        print(f"{cnt:4d} | {short}")
