/**
 * Markdown 编辑器组件
 * 
 * 功能:
 * 1. 分屏编辑（左侧编辑 + 右侧预览）
 * 2. 实时预览
 * 3. 工具栏（格式化、插入、导出）
 * 4. 自动保存
 * 5. 文档管理
 * 6. 主题切换
 */

import { Component, OnInit, OnDestroy, ViewChild, ElementRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { HttpClient } from '@angular/common/http';
import { Subject, interval, Subscription } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-markdown-editor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatToolbarModule,
    MatMenuModule,
    MatTooltipModule,
    MatSnackBarModule,
    MatSelectModule,
    MatFormFieldModule,
    MatDialogModule
  ],
  templateUrl: './markdown-editor.component.html',
  styleUrls: ['./markdown-editor.component.scss']
})
export class MarkdownEditorComponent implements OnInit, OnDestroy {
  @ViewChild('editorTextarea') editorTextarea?: ElementRef<HTMLTextAreaElement>;
  
  // 编辑器状态
  markdownContent: string = '';
  htmlPreview: string = '';
  documentTitle: string = '未命名文档';
  documentId: string | null = null;
  isDirty: boolean = false;
  isSaving: boolean = false;
  isLoading: boolean = false;
  
  // 配置
  theme: string = 'light';
  previewTheme: string = 'default';
  fontSize: number = 14;
  showPreview: boolean = true;
  syncScroll: boolean = true;
  
  // 自动保存
  autoSaveEnabled: boolean = true;
  autoSaveInterval: number = 30000; // 30 秒
  private autoSaveSubscription?: Subscription;
  private contentChangeSubject = new Subject<string>();
  
  // 文档列表
  documents: any[] = [];
  
  // 工具栏
  templates: any[] = [];
  
  private destroy$ = new Subject<void>();
  
  constructor(
    private http: HttpClient,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private ngZone: NgZone
  ) {}
  
  ngOnInit(): void {
    this.loadConfig();
    this.setupAutoSave();
    this.loadTemplates();
    this.loadDocuments();
    
    // 加载欢迎文档
    this.loadWelcomeDocument();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.autoSaveSubscription) {
      this.autoSaveSubscription.unsubscribe();
    }
    
    // 最后保存
    if (this.isDirty && this.autoSaveEnabled) {
      this.saveDocument();
    }
  }
  
  // ==================== 编辑器操作 ====================
  
  onContentChange(): void {
    this.isDirty = true;
    this.contentChangeSubject.next(this.markdownContent);
    this.updatePreview();
  }
  
  async updatePreview(): Promise<void> {
    if (!this.markdownContent.trim()) {
      this.htmlPreview = '<p class="placeholder">开始编写 Markdown...</p>';
      return;
    }
    
    try {
      const response: any = await this.http.post('/api/v1/markdown/parse', {
        content: this.markdownContent,
        extensions: ['extra', 'codehilite', 'toc']
      }).toPromise();
      
      if (response.success !== false) {
        this.htmlPreview = response.html || '';
      }
    } catch (error) {
      console.error('预览更新失败:', error);
    }
  }
  
  // ==================== 文档管理 ====================
  
  async loadDocuments(): Promise<void> {
    try {
      this.documents = await this.http.get<any[]>('/api/v1/markdown/documents?limit=50').toPromise() || [];
    } catch (error) {
      console.error('加载文档列表失败:', error);
    }
  }
  
  async loadDocument(docId: string): Promise<void> {
    this.isLoading = true;
    
    try {
      const doc: any = await this.http.get(`/api/v1/markdown/documents/${docId}`).toPromise();
      
      this.documentId = doc.id;
      this.documentTitle = doc.title;
      this.markdownContent = doc.content;
      this.isDirty = false;
      
      this.updatePreview();
      
      this.snackBar.open(`已加载: ${doc.title}`, '关闭', { duration: 2000 });
    } catch (error) {
      this.snackBar.open('加载文档失败', '关闭', { duration: 3000 });
    } finally {
      this.isLoading = false;
    }
  }
  
  async saveDocument(): Promise<void> {
    if (!this.isDirty && this.documentId) return;
    
    this.isSaving = true;
    
    try {
      const response: any = await this.http.post('/api/v1/markdown/save', {
        id: this.documentId,
        title: this.documentTitle,
        content: this.markdownContent,
        tags: []
      }).toPromise();
      
      if (response.id) {
        this.documentId = response.id;
        this.isDirty = false;
        
        this.snackBar.open('文档已保存', '关闭', { duration: 2000 });
        
        // 刷新文档列表
        this.loadDocuments();
      }
    } catch (error) {
      this.snackBar.open('保存失败', '关闭', { duration: 3000 });
    } finally {
      this.isSaving = false;
    }
  }
  
  async newDocument(): Promise<void> {
    // 如果当前文档有未保存的更改，提示保存
    if (this.isDirty) {
      const confirm = window.confirm('当前文档有未保存的更改，是否保存？');
      if (confirm) {
        await this.saveDocument();
      }
    }
    
    this.documentId = null;
    this.documentTitle = '未命名文档';
    this.markdownContent = '';
    this.isDirty = false;
    
    this.updatePreview();
  }
  
  async deleteDocument(docId: string): Promise<void> {
    const confirm = window.confirm('确定要删除此文档吗？');
    if (!confirm) return;
    
    try {
      await this.http.delete(`/api/v1/markdown/documents/${docId}`).toPromise();
      
      this.snackBar.open('文档已删除', '关闭', { duration: 2000 });
      
      // 如果删除的是当前文档，新建空白文档
      if (this.documentId === docId) {
        this.newDocument();
      }
      
      this.loadDocuments();
    } catch (error) {
      this.snackBar.open('删除失败', '关闭', { duration: 3000 });
    }
  }
  
  // ==================== 导出 ====================
  
  async exportHTML(): Promise<void> {
    try {
      const response: any = await this.http.post('/api/v1/markdown/export/html', {
        content: this.markdownContent,
        title: this.documentTitle,
        theme: this.previewTheme,
        include_toc: true
      }).toPromise();
      
      if (response.success) {
        // 下载文件
        window.open(response.downloadUrl, '_blank');
        this.snackBar.open('HTML 导出成功', '关闭', { duration: 2000 });
      }
    } catch (error) {
      this.snackBar.open('导出失败', '关闭', { duration: 3000 });
    }
  }
  
  async exportPDF(): Promise<void> {
    try {
      const response: any = await this.http.post('/api/v1/markdown/export/pdf', {
        content: this.markdownContent,
        title: this.documentTitle,
        theme: this.previewTheme,
        include_toc: true
      }).toPromise();
      
      if (response.success) {
        window.open(response.downloadUrl, '_blank');
        this.snackBar.open('PDF 导出成功', '关闭', { duration: 2000 });
      }
    } catch (error) {
      this.snackBar.open('PDF 导出失败（可能需要安装额外工具）', '关闭', { duration: 3000 });
    }
  }
  
  // ==================== 工具栏操作 ====================
  
  insertText(before: string, after: string = '', placeholder: string = ''): void {
    const textarea = this.editorTextarea?.nativeElement;
    if (!textarea) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = this.markdownContent.substring(start, end);
    
    const newText = this.markdownContent.substring(0, start) +
      before + (selectedText || placeholder) + after +
      this.markdownContent.substring(end);
    
    this.markdownContent = newText;
    this.onContentChange();
    
    // 恢复光标位置
    setTimeout(() => {
      textarea.focus();
      const cursorPos = start + before.length + (selectedText || placeholder).length;
      textarea.setSelectionRange(cursorPos, cursorPos);
    }, 0);
  }
  
  insertHeading(level: number): void {
    const prefix = '#'.repeat(level) + ' ';
    this.insertText(prefix, '', '标题');
  }
  
  insertBold(): void {
    this.insertText('**', '**', '粗体文本');
  }
  
  insertItalic(): void {
    this.insertText('*', '*', '斜体文本');
  }
  
  insertStrikethrough(): void {
    this.insertText('~~', '~~', '删除线文本');
  }
  
  insertCode(): void {
    this.insertText('`', '`', '代码');
  }
  
  insertCodeBlock(): void {
    this.insertText('```\n', '\n```', '代码');
  }
  
  insertLink(): void {
    this.insertText('[', '](https://)', '链接文本');
  }
  
  insertImage(): void {
    this.insertText('![', '](https://)', '图片描述');
  }
  
  insertList(ordered: boolean = false): void {
    if (ordered) {
      this.insertText('1. ', '', '列表项');
    } else {
      this.insertText('- ', '', '列表项');
    }
  }
  
  insertQuote(): void {
    this.insertText('> ', '', '引用文本');
  }
  
  insertTable(): void {
    const table = `| 列 1 | 列 2 | 列 3 |
|------|------|------|
| 数据 | 数据 | 数据 |
`;
    this.insertText(table);
  }
  
  insertHorizontalRule(): void {
    this.insertText('\n---\n');
  }
  
  insertCheckbox(): void {
    this.insertText('- [ ] ', '', '待办事项');
  }
  
  // ==================== 模板 ====================
  
  async loadTemplates(): Promise<void> {
    try {
      const response: any = await this.http.get('/api/v1/markdown/templates').toPromise();
      this.templates = response.templates || [];
    } catch (error) {
      console.error('加载模板失败:', error);
    }
  }
  
  applyTemplate(template: any): void {
    if (this.isDirty) {
      const confirm = window.confirm('应用模板将替换当前内容，是否继续？');
      if (!confirm) return;
    }
    
    this.markdownContent = template.content;
    this.documentTitle = template.name;
    this.isDirty = true;
    
    this.updatePreview();
    this.snackBar.open(`已应用模板: ${template.name}`, '关闭', { duration: 2000 });
  }
  
  // ==================== 自动保存 ====================
  
  setupAutoSave(): void {
    // 防抖保存（用户停止输入 2 秒后）
    this.contentChangeSubject.pipe(
      debounceTime(2000),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      if (this.autoSaveEnabled && this.isDirty) {
        this.saveDocument();
      }
    });
    
    // 定时保存
    this.autoSaveSubscription = interval(this.autoSaveInterval).pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      if (this.autoSaveEnabled && this.isDirty) {
        this.saveDocument();
      }
    });
  }
  
  // ==================== 配置 ====================
  
  loadConfig(): void {
    // 从 localStorage 加载配置
    const config = localStorage.getItem('markdown-editor-config');
    if (config) {
      try {
        const parsed = JSON.parse(config);
        this.theme = parsed.theme || 'light';
        this.previewTheme = parsed.previewTheme || 'default';
        this.fontSize = parsed.fontSize || 14;
        this.showPreview = parsed.showPreview !== false;
        this.autoSaveEnabled = parsed.autoSaveEnabled !== false;
      } catch (e) {
        console.error('加载配置失败:', e);
      }
    }
  }
  
  saveConfig(): void {
    const config = {
      theme: this.theme,
      previewTheme: this.previewTheme,
      fontSize: this.fontSize,
      showPreview: this.showPreview,
      autoSaveEnabled: this.autoSaveEnabled
    };
    
    localStorage.setItem('markdown-editor-config', JSON.stringify(config));
  }
  
  togglePreview(): void {
    this.showPreview = !this.showPreview;
    this.saveConfig();
  }
  
  changeTheme(theme: string): void {
    this.theme = theme;
    this.saveConfig();
  }
  
  changePreviewTheme(theme: string): void {
    this.previewTheme = theme;
    this.saveConfig();
    this.updatePreview();
  }
  
  // ==================== 辅助方法 ====================
  
  loadWelcomeDocument(): void {
    // 尝试加载欢迎文档
    this.http.get('/api/v1/markdown/documents/welcome').subscribe({
      next: (doc: any) => {
        if (doc && doc.content) {
          this.documentId = doc.id;
          this.documentTitle = doc.title;
          this.markdownContent = doc.content;
          this.updatePreview();
        }
      },
      error: () => {
        // 如果欢迎文档不存在，显示空白
        this.markdownContent = '# 开始编写\n\n欢迎使用 Markdown 编辑器！';
        this.updatePreview();
      }
    });
  }
  
  getWordCount(): number {
    return this.markdownContent.trim().split(/\s+/).filter(w => w.length > 0).length;
  }
  
  getCharCount(): number {
    return this.markdownContent.length;
  }
  
  getLineCount(): number {
    return this.markdownContent.split('\n').length;
  }
  
  // 滚动同步
  onEditorScroll(event: Event): void {
    if (!this.syncScroll) return;
    
    const textarea = event.target as HTMLTextAreaElement;
    const preview = document.querySelector('.preview-content');
    
    if (preview) {
      const percentage = textarea.scrollTop / (textarea.scrollHeight - textarea.clientHeight);
      preview.scrollTop = percentage * (preview.scrollHeight - preview.clientHeight);
    }
  }
}
