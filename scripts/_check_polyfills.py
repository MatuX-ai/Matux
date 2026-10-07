import re

with open('dist/imatuproject/polyfills.1c932e0a26b11d53.js', 'r', encoding='utf-8') as f:
    content = f.read()

matches = list(re.finditer(r'__load_patch\("(\w+)"', content))
print(f'Patches ({len(matches)}):')
for m in matches:
    print(f'  {m.group(1)}')

print()
print(f'me\( count: {content.count("me(")}')
print(f'"Timeout" count: {content.count(chr(34) + "Timeout" + chr(34))}')

# Find timers patch
timers_idx = content.find('"timers"')
if timers_idx > 0:
    print(f'\ntimers code: {content[timers_idx-50:timers_idx+500]}')