import pptx

prs = pptx.Presentation('g:/iMato/scripts/MatuX_创业大赛商业计划书_完整版.pptx')

print(f"总共 {len(prs.slide_layouts)} 种布局可用：")
for i, layout in enumerate(prs.slide_layouts):
    print(f"布局 {i}: {layout.name}")

print(f"\n当前PPT共有 {len(prs.slides)} 页")