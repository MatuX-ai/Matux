import os
import json

files = [(f, os.path.getmtime(os.path.join('dist/imatuproject', f))) for f in os.listdir('dist/imatuproject') if f.endswith('.js')]
files.sort(key=lambda x: x[1], reverse=True)
print('Latest 20 .js bundles:')
for f in files[:20]:
    print(' ', f)

ngsw = json.load(open('dist/imatuproject/ngsw.json'))
print('\nnSWS references for digital-twin:')
for ag in ngsw.get('assetGroups', []):
    for url in ag.get('urls', []):
        if 'digital-twin' in url or 'twin' in url:
            print(f' {url}')