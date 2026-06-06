import json
with open('eslint-report.json', 'r', encoding='utf-8-sig') as f:
    report = json.load(f)
file_errors = {}
file_warnings = {}
error_types = {}
for entry in report:
    file_path = entry['filePath']
    short_path = file_path.replace(
        '\\', '/').split('src/')[-1] if 'src/' in file_path else file_path
    errors = [m for m in entry['messages'] if m['severity'] == 2]
    warnings = [m for m in entry['messages'] if m['severity'] == 1]
    if errors:
        file_errors[short_path] = len(errors)
    if warnings:
        file_warnings[short_path] = len(warnings)
    for m in entry['messages']:
        if m['severity'] == 2:
            rule = m['ruleId'] or 'parsing-error'
            error_types[rule] = error_types.get(rule, 0) + 1

print("=== Errors per file (sorted) ===")
sorted_files = sorted(file_errors.items(), key=lambda x: -x[1])
for fp, count in sorted_files:
    w = file_warnings.get(fp, 0)
    print(f'{count:3d} errors, {w:3d} warnings: {fp}')

print(f'\n=== Total files with errors: {len(sorted_files)} ===')
print(f'Total errors: {sum(file_errors.values())}')
print(f'Total warnings: {sum(file_warnings.values())}')

print('\n=== Error types breakdown ===')
sorted_types = sorted(error_types.items(), key=lambda x: -x[1])
for rule, count in sorted_types:
    print(f'{count:3d}: {rule}')
