import json
r = json.load(open('eslint-report.json', 'r', encoding='utf-8'))
err_by_file = {}
for f in r:
    cnt = sum(1 for m in f['messages'] if m.get('severity') == 2)
    if cnt > 0:
        short = f['filePath'].split('src\\')[-1]
        err_by_file[short] = cnt
for k, v in sorted(err_by_file.items(), key=lambda x: -x[1])[:25]:
    print(f"{v:4d} | {k}")
