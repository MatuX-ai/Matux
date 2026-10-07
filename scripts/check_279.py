# -*- coding: utf-8 -*-
import glob
chunks = glob.glob(r'I:\iMato\dist\imatuproject\279.*.js')
for c in chunks:
    with open(c, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print(f'chunk: {c} [{len(content)} bytes]')
    print(f'  cloud_off: {content.count("cloud_off")} hits')
    print(f'  fallback-banner-top: {content.count("fallback-banner-top")} hits')
    print(f'  refresh: {content.count("refresh")} hits')
    print(f'  loadModules: {content.count("loadModules")} hits')
    print(f'  applyModulesFallback: {content.count("applyModulesFallback")} hits')
    # 抽取含 cloud_off 的字符串
    idx = content.find('cloud_off')
    if idx >= 0:
        print(f'  cloud_off context: {content[max(0, idx-50):idx+100]}')
