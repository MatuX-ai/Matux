import { CommonModule } from '@angular/common';
import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { interval, Observable, Subject } from 'rxjs';
import { switchMap, takeUntil } from 'rxjs/operators';

import { CollaborationClient, TextOperation } from './ot-algorithm';

interface DocumentInfo {
  id: number;
  document_name: string;
  content: string;
  version_number: number;
  allow_comments: boolean;
  allow_suggestions: boolean;
}

interface DocumentOperation {
  id: number;
  operation_type: string;
  position: number;
  content: string;
  client_id: string;
  user_id: number;
  timestamp: string;
}

interface DocumentComment {
  id: number;
  start_position: number;
  end_position: number;
  content: string;
  comment_type: string;
  user_name: string;
  is_resolved: boolean;
  created_at: string;
}

interface DocumentSuggestion {
  id: number;
  start_position: number;
  end_position: number;
  original_content: string;
  suggested_content: string;
  user_name: string;
  status: string;
  created_at: string;
  suggestion_reason?: string;
}

@Component({
  selector: 'app-collaborative-editor',
  templateUrl: './collaborative-editor.component.html',
  styleUrls: ['./collaborative-editor.component.scss'],
  imports: [
    CommonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
    FormsModule,
    ReactiveFormsModule,
    DatePipe,
  ],
})
export class CollaborativeEditorComponent implements OnInit, OnDestroy {
  @Input() courseId!: number;
  @Input() orgId!: number;
  @Input() documentId!: number;
  @Input() userId!: number;
  @Input() userName!: string;

  @Output() contentChange = new EventEmitter<string>();
  @Output() documentLoaded = new EventEmitter<DocumentInfo>();

  @ViewChild('editorContainer') editorContainer!: ElementRef;

  // 编辑器状态
  documentInfo: DocumentInfo | null = null;
  editorContent: string = '';
  isLoading = false;
  isSaving = false;
  isConnected = false;

  // 协作功能
  clientId: string = this.generateClientId();
  sessionId: string = '';
  collaborationClient!: CollaborationClient;
  activeUsers: Array<{ userId: number; userName: string; cursorPosition: number }> = [];
  currentCursorPosition: number = 0;

  // 评论和建议
  showCommentsPanel = false;
  showSuggestionsPanel = false;
  comments: DocumentComment[] = [];
  suggestions: DocumentSuggestion[] = [];

  // 工具栏相关
  showSelectionToolbar = false;
  selectionToolbarPosition = { x: 0, y: 0 };
  selectedTextRange: { start: number; end: number } | null = null;

  // WebSocket连接
  private ws: WebSocket | null = null;
  private destroy$ = new Subject<void>();

  // 操作队列
  private pendingOperations: any[] = [];
  private lastSyncTime = Date.now();
  private syncInterval = 1000; // 1秒同步间隔

  constructor(
    private http: HttpClient,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadDocument();
    this.setupAutoSync();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.disconnectWebSocket();
  }

  private generateClientId(): string {
    return (
      Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    );
  }

  loadDocument(): void {
    if (!this.documentId || !this.orgId || !this.courseId) {
      return;
    }

    this.isLoading = true;

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}`;

    this.http.get<DocumentInfo>(url).subscribe({
      next: (data) => {
        this.documentInfo = data;
        this.editorContent = data.content;
        this.contentChange.emit(this.editorContent);
        this.documentLoaded.emit(data);
        this.joinSession();
        this.loadComments();
        this.loadSuggestions();
        this.isLoading = false;
      },
      error: (error) => {
        this.snackBar.open('加载文档失败', '关闭', { duration: 3000 });
        this.isLoading = false;
      },
    });
  }

  joinSession(): void {
    if (!this.documentInfo) return;

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/sessions`;

    this.http.post<any>(url, { client_id: this.clientId }).subscribe({
      next: (response) => {
        this.sessionId = response.session_id;
        this.connectWebSocket();
        this.snackBar.open('已加入协作会话', '', { duration: 2000 });
      },
      error: (error) => {},
    });
  }

  connectWebSocket(): void {
    if (!this.documentId || !this.sessionId) return;

    const wsUrl = `ws://localhost:8000/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/ws?session_id=${this.sessionId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.snackBar.open('实时连接已建立', '', { duration: 2000 });
      };

      this.ws.onmessage = (event) => {
        this.handleWebSocketMessage(event.data);
      };

      this.ws.onclose = () => {
        this.isConnected = false;
      };

      this.ws.onerror = (error) => {
        this.isConnected = false;
      };
    } catch (error) {
      this.isConnected = false;
    }
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  private handleWebSocketMessage(data: string): void {
    try {
      const message = JSON.parse(data);

      switch (message.type) {
        case 'operations_applied':
          this.applyRemoteOperations(message.operations);
          break;
        case 'comment_added':
          this.addRemoteComment(message.comment);
          break;
        case 'suggestion_added':
          this.addRemoteSuggestion(message.suggestion);
          break;
        case 'cursor_update':
          this.updateRemoteCursor(message);
          break;
        case 'user_left':
          this.removeUser(message.session_id);
          break;
      }
    } catch (error) {}
  }

  onContentChange(newContent: string): void {
    const oldContent = this.editorContent;
    this.editorContent = newContent;

    // 计算操作差异
    const operations = this.calculateOperations(oldContent, newContent);

    if (operations.length > 0) {
      this.pendingOperations.push(...operations);
      this.contentChange.emit(newContent);
    }
  }

  private calculateOperations(oldContent: string, newContent: string): TextOperation[] {
    const operations: TextOperation[] = [];

    // 使用协作客户端处理本地编辑
    if (!this.collaborationClient) {
      this.collaborationClient = new CollaborationClient(this.clientId, oldContent);
    }

    // 简单的差异检测算法
    let i = 0;
    let j = 0;

    while (i < oldContent.length && j < newContent.length) {
      if (oldContent[i] === newContent[j]) {
        i++;
        j++;
      } else {
        // 发现差异点
        const startPos = j;

        // 查找插入的内容
        while (
          j < newContent.length &&
          (i >= oldContent.length || oldContent[i] !== newContent[j])
        ) {
          j++;
        }

        const insertedText = newContent.substring(startPos, j);
        if (insertedText) {
          const op = this.collaborationClient.localEdit('insert', startPos, insertedText);
          operations.push({
            type: 'insert',
            position: op.position,
            content: op.content,
            clientId: op.clientId,
            timestamp: op.timestamp,
          });
        }

        // 查找删除的内容
        const deleteStart = i;
        while (
          i < oldContent.length &&
          (j >= newContent.length || oldContent[i] !== newContent[j])
        ) {
          i++;
        }

        if (i > deleteStart) {
          const deleteContent = oldContent.substring(deleteStart, i);
          const op = this.collaborationClient.localEdit('delete', deleteStart, deleteContent);
          operations.push({
            type: 'delete',
            position: op.position,
            content: op.content,
            clientId: op.clientId,
            timestamp: op.timestamp,
          });
        }
      }
    }

    // 处理尾部内容
    if (j < newContent.length) {
      const op = this.collaborationClient.localEdit('insert', j, newContent.substring(j));
      operations.push({
        type: 'insert',
        position: op.position,
        content: op.content,
        clientId: op.clientId,
        timestamp: op.timestamp,
      });
    }

    if (i < oldContent.length) {
      const op = this.collaborationClient.localEdit('delete', i, oldContent.substring(i));
      operations.push({
        type: 'delete',
        position: op.position,
        content: op.content,
        clientId: op.clientId,
        timestamp: op.timestamp,
      });
    }

    return operations;
  }

  private setupAutoSync(): void {
    interval(this.syncInterval)
      .pipe(
        takeUntil(this.destroy$),
        switchMap(() => {
          if (this.pendingOperations.length > 0) {
            return this.syncOperations();
          }
          return new Observable((observer) => observer.complete());
        })
      )
      .subscribe();
  }

  private syncOperations(): Observable<any> {
    if (this.pendingOperations.length === 0) {
      return new Observable((observer) => observer.complete());
    }

    const operationsToSend = [...this.pendingOperations];
    this.pendingOperations = [];

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/operations/batch`;

    return this.http.post(url, operationsToSend);
  }

  private applyRemoteOperations(operations: DocumentOperation[]): void {
    if (!this.collaborationClient) {
      this.collaborationClient = new CollaborationClient(this.clientId, this.editorContent);
    }

    // 转换远程操作为本地格式
    const textOps: TextOperation[] = operations
      .filter((op) => op.client_id !== this.clientId) // 忽略自己的操作
      .map((op) => ({
        type: op.operation_type as 'insert' | 'delete',
        position: op.position,
        content: op.content || '',
        clientId: op.client_id,
        timestamp: new Date(op.timestamp).getTime(),
      }));

    // 使用OT算法处理远程操作
    const transformedOps = this.collaborationClient.handleRemoteOperations(textOps);

    // 更新编辑器内容
    const newContent = this.collaborationClient.getCurrentContent();
    this.editorContent = newContent;
    this.contentChange.emit(newContent);
  }

  private applyOperation(content: string, operation: DocumentOperation): string {
    const pos = operation.position;

    if (operation.operation_type === 'insert') {
      if (pos >= content.length) {
        return content + (operation.content || '');
      } else {
        return content.slice(0, pos) + (operation.content || '') + content.slice(pos);
      }
    } else if (operation.operation_type === 'delete') {
      const deleteLen = operation.content ? operation.content.length : 1;
      if (pos >= content.length) {
        return content;
      } else if (pos + deleteLen >= content.length) {
        return content.slice(0, pos);
      } else {
        return content.slice(0, pos) + content.slice(pos + deleteLen);
      }
    }

    return content;
  }

  onCursorPositionChange(position: number): void {
    this.currentCursorPosition = position;
    this.updateRemoteCursorPosition();
  }

  private updateRemoteCursorPosition(): void {
    if (!this.sessionId) return;

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/sessions/${this.sessionId}/cursor`;

    this.http
      .put(url, {
        cursor_position: this.currentCursorPosition,
      })
      .subscribe({
        error: (error) => {},
      });
  }

  // 评论功能
  addComment(startPos: number, endPos: number, content: string): void {
    if (!this.documentInfo?.allow_comments) {
      this.snackBar.open('此文档不允许添加评论', '关闭', { duration: 3000 });
      return;
    }

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/comments`;

    this.http
      .post<DocumentComment>(url, {
        start_position: startPos,
        end_position: endPos,
        content,
        comment_type: 'comment',
      })
      .subscribe({
        next: (comment) => {
          this.comments.push({
            ...comment,
            user_name: this.userName,
          });
          this.snackBar.open('评论已添加', '', { duration: 2000 });
        },
        error: (error) => {
          this.snackBar.open('添加评论失败', '关闭', { duration: 3000 });
        },
      });
  }

  loadComments(): void {
    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/comments`;

    this.http.get<DocumentComment[]>(url).subscribe({
      next: (comments) => {
        this.comments = comments;
      },
      error: (error) => {},
    });
  }

  private addRemoteComment(comment: any): void {
    this.comments.push(comment);
  }

  resolveComment(commentId: number): void {
    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/comments/${commentId}/resolve`;

    this.http.put(url, {}).subscribe({
      next: () => {
        const comment = this.comments.find((c) => c.id === commentId);
        if (comment) {
          comment.is_resolved = true;
        }
        this.snackBar.open('评论已标记为已解决', '', { duration: 2000 });
      },
      error: (error) => {
        this.snackBar.open('解决评论失败', '关闭', { duration: 3000 });
      },
    });
  }

  // 建议功能
  addSuggestion(startPos: number, endPos: number, suggestedContent: string, reason?: string): void {
    if (!this.documentInfo?.allow_suggestions) {
      this.snackBar.open('此文档不允许添加建议', '关闭', { duration: 3000 });
      return;
    }

    const originalContent = this.editorContent.substring(startPos, endPos);

    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/suggestions`;

    this.http
      .post<DocumentSuggestion>(url, {
        start_position: startPos,
        end_position: endPos,
        original_content: originalContent,
        suggested_content: suggestedContent,
        suggestion_reason: reason,
      })
      .subscribe({
        next: (suggestion) => {
          this.suggestions.push({
            ...suggestion,
            user_name: this.userName,
          });
          this.snackBar.open('建议已添加', '', { duration: 2000 });
        },
        error: (error) => {
          this.snackBar.open('添加建议失败', '关闭', { duration: 3000 });
        },
      });
  }

  loadSuggestions(): void {
    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/suggestions`;

    this.http.get<DocumentSuggestion[]>(url).subscribe({
      next: (suggestions) => {
        this.suggestions = suggestions;
      },
      error: (error) => {},
    });
  }

  private addRemoteSuggestion(suggestion: any): void {
    this.suggestions.push(suggestion);
  }

  reviewSuggestion(suggestionId: number, status: 'accepted' | 'rejected'): void {
    const url = `/api/v1/org/${this.orgId}/courses/${this.courseId}/collaborative-documents/${this.documentId}/suggestions/${suggestionId}/review`;

    this.http.put(url, { status }).subscribe({
      next: (response: any) => {
        const suggestion = this.suggestions.find((s) => s.id === suggestionId);
        if (suggestion) {
          suggestion.status = status;
        }

        if (status === 'accepted') {
          // 应用建议到文档内容
          this.applySuggestion(response.suggestion);
        }

        this.snackBar.open(`建议已${status === 'accepted' ? '接受' : '拒绝'}`, '', {
          duration: 2000,
        });
      },
      error: (error) => {
        this.snackBar.open('审核建议失败', '关闭', { duration: 3000 });
      },
    });
  }

  private applySuggestion(suggestion: any): void {
    const before = this.editorContent.substring(0, suggestion.start_position);
    const after = this.editorContent.substring(suggestion.end_position);
    this.editorContent = before + suggestion.suggested_content + after;
    this.contentChange.emit(this.editorContent);
  }

  // 用户管理
  private updateRemoteCursor(message: any): void {
    const existingUser = this.activeUsers.find((u) => u.userId === message.user_id);
    if (existingUser) {
      existingUser.cursorPosition = message.cursor_position;
    } else {
      this.activeUsers.push({
        userId: message.user_id,
        userName: message.user_name,
        cursorPosition: message.cursor_position,
      });
    }
  }

  private removeUser(sessionId: string): void {
    // 这里可以根据sessionId移除用户
    // 需要在服务端维护session到user的映射
  }

  // 工具方法
  toggleCommentsPanel(): void {
    this.showCommentsPanel = !this.showCommentsPanel;
  }

  toggleSuggestionsPanel(): void {
    this.showSuggestionsPanel = !this.showSuggestionsPanel;
  }

  getConnectedUsersCount(): number {
    return this.activeUsers.length + 1; // +1 表示自己
  }

  // 工具方法 - 计算光标位置
  calculateCursorPosition(position: number): number {
    // 根据文本内容计算光标的像素位置
    // 这里需要根据实际编辑器实现来计算
    const charWidth = 8; // 假设每个字符宽度为 8px
    const lineHeight = 20; // 假设每行高度为 20px

    const lines = this.editorContent.substring(0, position).split('\n');
    const lineNumber = lines.length - 1;
    const columnNumber = lines[lines.length - 1].length;

    return columnNumber * charWidth;
  }

  // 获取评论类型标签
  getCommentTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      comment: '评论',
      question: '问题',
      suggestion: '建议',
      note: '备注',
    };
    return labels[type] || type;
  }

  // 获取建议状态标签
  getSuggestionStatusLabel(status: string): string {
    const labels: { [key: string]: string } = {
      pending: '待审核',
      accepted: '已接受',
      rejected: '已拒绝',
    };
    return labels[status] || status;
  }

  // 打开评论对话框
  openCommentDialog(): void {
    if (!this.selectedTextRange) {
      this.snackBar.open('请先选择要评论的文本', '', { duration: 2000 });
      return;
    }

    const commentText = prompt('请输入评论内容:');
    if (commentText) {
      this.addComment(this.selectedTextRange.start, this.selectedTextRange.end, commentText);
    }
    this.hideSelectionToolbar();
  }

  // 打开建议对话框
  openSuggestionDialog(): void {
    if (!this.selectedTextRange) {
      this.snackBar.open('请先选择要建议的文本', '', { duration: 2000 });
      return;
    }

    const suggestedText = prompt('请输入建议内容:');
    const reason = prompt('请输入建议理由（可选）:') || undefined;

    if (suggestedText) {
      this.addSuggestion(
        this.selectedTextRange.start,
        this.selectedTextRange.end,
        suggestedText,
        reason
      );
    }
    this.hideSelectionToolbar();
  }

  // 显示/隐藏工具栏
  showToolbarAtPosition(range: { start: number; end: number }): void {
    this.selectedTextRange = range;
    this.showSelectionToolbar = true;

    // 计算工具栏位置（简化版本）
    const pos = this.calculateCursorPosition(range.start);
    this.selectionToolbarPosition = {
      x: pos,
      y: 100, // 固定位置，实际应该根据滚动位置计算
    };
  }

  hideSelectionToolbar(): void {
    this.showSelectionToolbar = false;
    this.selectedTextRange = null;
  }
}
