import os

files = [(f, os.path.getmtime(os.path.join('dist/imatuproject', f))) for f in os.listdir('dist/imatuproject') if 'digital' in f.lower() or 'twin' in f.lower()]
files.sort(key=lambda x: x[1], reverse=True)
print('Latest digital-twin files:')
for f in files[:5]:
    print(' ', f)