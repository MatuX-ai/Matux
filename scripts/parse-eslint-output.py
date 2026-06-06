import re

with open(r'C:\Users\Administrator\.lingma\cache\projects\iMato-1de25ebc\agent-tools\e1c1a22c\65af5f6f.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Parse the output
lines = content.split('\n')
current_file = None
file_errors = {}
file_warnings = {}
error_types = {}

for line in lines:
    # Detect file path
    file_match = re.match(r'^([A-Z]:\\.+?)\.ts(?:\s*|$)', line)
    if file_match:
        current_file = file_match.group(1) + '.ts'
        current_file = current_file.replace(
            '\\', '/').split('src/')[-1] if 'src/' in current_file else current_file
        continue

    # Detect error/warning with line number
    msg_match = re.match(
        r'\s+(\d+):(\d+)\s+(error|warning)\s+(.+?)\s{2,}(.+?)$', line)
    if msg_match and current_file:
        severity = msg_match.group(3)
        rule = msg_match.group(5).strip()
        if severity == 'error':
            file_errors[current_file] = file_errors.get(current_file, 0) + 1
            error_types[rule] = error_types.get(rule, 0) + 1
        elif severity == 'warning':
            file_warnings[current_file] = file_warnings.get(
                current_file, 0) + 1

print("=== Errors per file ===")
sorted_files = sorted(file_errors.items(), key=lambda x: -x[1])
for fp, count in sorted_files:
    w = file_warnings.get(fp, 0)
    print(f'{count:3d} errors, {w:3d} warnings: {fp}')

print(f'\nTotal files with errors: {len(sorted_files)}')
print(f'Total errors: {sum(file_errors.values())}')

print('\n=== Error types breakdown ===')
sorted_types = sorted(error_types.items(), key=lambda x: -x[1])
for rule, count in sorted_types:
    print(f'{count:3d}: {rule}')
