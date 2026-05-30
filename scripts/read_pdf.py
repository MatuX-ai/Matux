from pypdf import PdfReader

# 读取PDF文件
reader = PdfReader(r'G:/码图+AI.pdf')

# 提取所有文本
text = ''
for page in reader.pages:
    text += page.extract_text() + '\n\n'

# 保存到文本文件
with open('G:/码图+AI_content.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"PDF共{len(reader.pages)}页")
print(f"文本已保存到: G:/码图+AI_content.txt")
