import json
r = json.load(open('eslint-report.json', 'r', encoding='utf-8'))
files = [
    'G:\\iMato\\src\\app\\components\\token-stats-chart\\token-stats-chart.component.ts',
    'G:\\iMato\\src\\app\\core\\services\\network-monitor.service.ts',
    'G:\\iMato\\src\\app\\core\\services\\performance-monitor.service.ts',
    'G:\\iMato\\src\\app\\core\\services\\pricing.service.ts',
    'G:\\iMato\\src\\app\\core\\services\\pwa.service.ts',
    'G:\\iMato\\src\\app\\shared\\components\\status-bar\\status-bar.component.ts',
    'G:\\iMato\\src\\app\\core\\services\\diagnosis.service.ts',
    'G:\\iMato\\src\\app\\core\\services\\milestone.service.ts',
]
for target in files:
    for f in r:
        if f['filePath'] == target:
            cnt = sum(1 for m in f['messages'] if m.get('severity') == 2)
            if cnt > 0:
                short = target.split('src\\')[-1]
                print(f"\n=== {short} ({cnt} errors) ===")
                for m in f['messages']:
                    if m.get('severity') == 2:
                        print(
                            f"  L{m['line']:4d} | {m.get('ruleId', 'NONE')[:40]} | {m['message'][:80]}")
