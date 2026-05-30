/**
 * Operational Transformation 算法实现
 * 用于处理实时协同编辑中的并发操作
 */

export interface TextOperation {
  type: 'insert' | 'delete';
  position: number;
  content: string;
  clientId: string;
  timestamp: number;
  operationId?: string;
}

export interface TransformedOperation extends TextOperation {
  originalPosition: number;
}

export class OperationalTransformation {
  /**
   * 转换单个操作使其能与其他操作并发执行
   * @param op1 需要转换的操作
   * @param op2 已经应用的操作
   * @returns 转换后的操作
   */
  static transform(op1: TextOperation, op2: TextOperation): TransformedOperation {
    if (op1.type === 'insert' && op2.type === 'insert') {
      return this.transformInsertInsert(op1, op2);
    } else if (op1.type === 'insert' && op2.type === 'delete') {
      return this.transformInsertDelete(op1, op2);
    } else if (op1.type === 'delete' && op2.type === 'insert') {
      return this.transformDeleteInsert(op1, op2);
    } else if (op1.type === 'delete' && op2.type === 'delete') {
      return this.transformDeleteDelete(op1, op2);
    }

    return {
      ...op1,
      originalPosition: op1.position,
    };
  }

  /**
   * 转换两个插入操作
   */
  private static transformInsertInsert(
    op1: TextOperation,
    op2: TextOperation
  ): TransformedOperation {
    const pos1 = op1.position;
    const pos2 = op2.position;
    const content2Length = op2.content.length;

    if (pos1 < pos2) {
      // op1在op2之前插入，位置不变
      return {
        ...op1,
        originalPosition: pos1,
      };
    } else if (pos1 > pos2) {
      // op1在op2之后插入，需要调整位置
      return {
        ...op1,
        position: pos1 + content2Length,
        originalPosition: pos1,
      };
    } else {
      // 同一位置插入，根据clientId排序决定先后
      if (op1.clientId < op2.clientId) {
        return {
          ...op1,
          originalPosition: pos1,
        };
      } else {
        return {
          ...op1,
          position: pos1 + content2Length,
          originalPosition: pos1,
        };
      }
    }
  }

  /**
   * 转换插入和删除操作
   */
  private static transformInsertDelete(
    op1: TextOperation,
    op2: TextOperation
  ): TransformedOperation {
    const insertPos = op1.position;
    const deletePos = op2.position;
    const deleteLength = op2.content.length;

    if (insertPos <= deletePos) {
      // 插入位置在删除之前，不受影响
      return {
        ...op1,
        originalPosition: insertPos,
      };
    } else if (insertPos > deletePos + deleteLength) {
      // 插入位置在删除范围之后，需要向前移动
      return {
        ...op1,
        position: insertPos - deleteLength,
        originalPosition: insertPos,
      };
    } else {
      // 插入位置在删除范围内，这种情况理论上不应该发生
      // 因为删除操作应该先于插入操作处理
      return {
        ...op1,
        position: deletePos,
        originalPosition: insertPos,
      };
    }
  }

  /**
   * 转换删除和插入操作
   */
  private static transformDeleteInsert(
    op1: TextOperation,
    op2: TextOperation
  ): TransformedOperation {
    const deletePos = op1.position;
    const deleteLength = op1.content.length;
    const insertPos = op2.position;

    if (insertPos <= deletePos) {
      // 插入在删除之前，删除操作位置需要向后移动
      return {
        ...op1,
        position: deletePos + op2.content.length,
        originalPosition: deletePos,
      };
    } else if (insertPos >= deletePos + deleteLength) {
      // 插入在删除范围之后，删除操作不受影响
      return {
        ...op1,
        originalPosition: deletePos,
      };
    } else {
      // 插入在删除范围内，需要分割删除操作
      const beforeLength = insertPos - deletePos;
      const afterLength = deleteLength - beforeLength - op2.content.length;

      return {
        ...op1,
        position: deletePos,
        content:
          op1.content.substring(0, beforeLength) +
          op1.content.substring(beforeLength + op2.content.length),
        originalPosition: deletePos,
      };
    }
  }

  /**
   * 转换两个删除操作
   */
  private static transformDeleteDelete(
    op1: TextOperation,
    op2: TextOperation
  ): TransformedOperation {
    const pos1 = op1.position;
    const len1 = op1.content.length;
    const pos2 = op2.position;
    const len2 = op2.content.length;

    if (pos1 + len1 <= pos2) {
      // op1完全在op2之前
      return {
        ...op1,
        originalPosition: pos1,
      };
    } else if (pos2 + len2 <= pos1) {
      // op2完全在op1之前
      return {
        ...op1,
        position: pos1 - len2,
        originalPosition: pos1,
      };
    } else {
      // 操作重叠，合并删除范围
      const start = Math.min(pos1, pos2);
      const end = Math.max(pos1 + len1, pos2 + len2);

      return {
        ...op1,
        position: start,
        content: ' '.repeat(end - start), // 用空格填充重叠部分
        originalPosition: pos1,
      };
    }
  }

  /**
   * 将操作应用到文本内容
   * @param content 原始文本内容
   * @param operation 操作对象
   * @returns 应用操作后的新内容
   */
  static applyOperation(content: string, operation: TextOperation): string {
    if (operation.type === 'insert') {
      if (operation.position >= content.length) {
        return content + operation.content;
      } else {
        return (
          content.slice(0, operation.position) +
          operation.content +
          content.slice(operation.position)
        );
      }
    } else if (operation.type === 'delete') {
      if (operation.position >= content.length) {
        return content;
      } else if (operation.position + operation.content.length >= content.length) {
        return content.slice(0, operation.position);
      } else {
        return (
          content.slice(0, operation.position) +
          content.slice(operation.position + operation.content.length)
        );
      }
    }

    return content;
  }

  /**
   * 批量转换操作序列
   * @param operations 需要转换的操作列表
   * @param appliedOps 已经应用的操作列表
   * @returns 转换后的操作列表
   */
  static transformBatch(
    operations: TextOperation[],
    appliedOps: TextOperation[]
  ): TransformedOperation[] {
    let transformedOps: TransformedOperation[] = operations.map((op) => ({
      ...op,
      originalPosition: op.position,
    }));

    // 对每个已应用的操作进行转换
    for (const appliedOp of appliedOps) {
      transformedOps = transformedOps.map((op) => this.transform(op, appliedOp));
    }

    return transformedOps;
  }

  /**
   * 生成操作唯一标识
   * @param operation 操作对象
   * @returns 唯一标识字符串
   */
  static generateOperationId(operation: TextOperation): string {
    const data = `${operation.clientId}-${operation.type}-${operation.position}-${operation.content}-${operation.timestamp}`;
    return btoa(data).replace(/[^a-zA-Z0-9]/g, '');
  }

  /**
   * 验证操作的有效性
   * @param operation 操作对象
   * @param content 当前文本内容
   * @returns 是否有效
   */
  static validateOperation(operation: TextOperation, content: string): boolean {
    if (operation.position < 0) return false;

    if (operation.type === 'insert') {
      return operation.content !== undefined && operation.content !== null;
    } else if (operation.type === 'delete') {
      if (operation.position >= content.length) return false;
      if (operation.position + operation.content.length > content.length) return false;
      // 验证删除的内容是否匹配
      const actualContent = content.substring(
        operation.position,
        operation.position + operation.content.length
      );
      return actualContent === operation.content;
    }

    return false;
  }
}

/**
 * 文档状态管理器
 * 负责维护文档的当前状态和操作历史
 */
export class DocumentStateManager {
  private content: string = '';
  private operations: TextOperation[] = [];
  private revision: number = 0;

  constructor(initialContent: string = '') {
    this.content = initialContent;
  }

  /**
   * 应用操作到文档
   * @param operation 操作对象
   * @returns 是否应用成功
   */
  applyOperation(operation: TextOperation): boolean {
    if (!OperationalTransformation.validateOperation(operation, this.content)) {
      return false;
    }

    try {
      this.content = OperationalTransformation.applyOperation(this.content, operation);
      this.operations.push({
        ...operation,
        operationId: OperationalTransformation.generateOperationId(operation),
      });
      this.revision++;
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 批量应用操作
   * @param operations 操作列表
   * @returns 成功应用的操作数量
   */
  applyOperations(operations: TextOperation[]): number {
    let successCount = 0;

    for (const op of operations) {
      if (this.applyOperation(op)) {
        successCount++;
      }
    }

    return successCount;
  }

  /**
   * 获取当前文档内容
   */
  getContent(): string {
    return this.content;
  }

  /**
   * 获取当前修订版本号
   */
  getRevision(): number {
    return this.revision;
  }

  /**
   * 获取操作历史
   */
  getOperations(): TextOperation[] {
    return [...this.operations];
  }

  /**
   * 重置文档状态
   */
  reset(content: string = ''): void {
    this.content = content;
    this.operations = [];
    this.revision = 0;
  }
}

/**
 * 协同编辑客户端
 * 处理本地操作和远程操作的协调
 */
export class CollaborationClient {
  private localOperations: TextOperation[] = [];
  private remoteOperations: TextOperation[] = [];
  private stateManager: DocumentStateManager;
  private clientId: string;

  constructor(clientId: string, initialContent: string = '') {
    this.clientId = clientId;
    this.stateManager = new DocumentStateManager(initialContent);
  }

  /**
   * 本地编辑操作
   * @param type 操作类型
   * @param position 操作位置
   * @param content 操作内容
   * @returns 生成的操作对象
   */
  localEdit(type: 'insert' | 'delete', position: number, content: string): TextOperation {
    const operation: TextOperation = {
      type,
      position,
      content,
      clientId: this.clientId,
      timestamp: Date.now(),
    };

    // 立即应用到本地状态
    this.stateManager.applyOperation(operation);
    this.localOperations.push(operation);

    return operation;
  }

  /**
   * 处理远程操作
   * @param operations 远程操作列表
   * @returns 转换后的操作列表
   */
  handleRemoteOperations(operations: TextOperation[]): TransformedOperation[] {
    // 先转换远程操作以适应本地未发送的操作
    const transformedOps = OperationalTransformation.transformBatch(
      operations,
      this.localOperations
    );

    // 应用转换后的操作
    for (const op of transformedOps) {
      this.stateManager.applyOperation(op);
    }

    this.remoteOperations.push(...operations);
    return transformedOps;
  }

  /**
   * 获取待发送的本地操作
   */
  getPendingLocalOperations(): TextOperation[] {
    const ops = [...this.localOperations];
    this.localOperations = [];
    return ops;
  }

  /**
   * 获取当前文档内容
   */
  getCurrentContent(): string {
    return this.stateManager.getContent();
  }

  /**
   * 获取当前修订版本
   */
  getCurrentRevision(): number {
    return this.stateManager.getRevision();
  }
}
