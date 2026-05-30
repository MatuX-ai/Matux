import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface EditorContext {
  language: string;
  currentLine: number;
  currentColumn: number;
  scopeLevel: string;
  syntaxContext: string;
  variables: string[];
  functions: string[];
  imports: string[];
}

@Injectable({
  providedIn: 'root',
})
export class EditorContextService {
  private contextSubject = new BehaviorSubject<EditorContext>({
    language: 'python',
    currentLine: 1,
    currentColumn: 1,
    scopeLevel: 'global',
    syntaxContext: 'general',
    variables: [],
    functions: [],
    imports: [],
  });

  context$ = this.contextSubject.asObservable();
  private context: EditorContext;

  constructor() {
    this.context = this.contextSubject.value;
  }

  initialize(language: string): void {
    this.context = {
      ...this.context,
      language,
    };
    this.contextSubject.next(this.context);
  }

  updateContext(code: string, caretPosition: number): void {
    const lines = code.substring(0, caretPosition).split('\n');
    const currentLine = lines.length;
    const currentColumn = lines[lines.length - 1].length + 1;

    const newContext: EditorContext = {
      ...this.context,
      currentLine,
      currentColumn,
      scopeLevel: this.detectScopeLevel(lines),
      syntaxContext: this.detectSyntaxContext(lines),
      variables: this.extractVariables(lines),
      functions: this.extractFunctions(lines),
      imports: this.extractImports(lines),
    };

    this.context = newContext;
    this.contextSubject.next(this.context);
  }

  getCurrentContext(): EditorContext {
    return { ...this.context };
  }

  private detectScopeLevel(lines: string[]): string {
    if (lines.length === 0) return 'global';

    const lastLine = lines[lines.length - 1].trim();

    // 检查常见的作用域关键字
    if (lastLine.match(/^(class|def|function)\s+/)) {
      return 'definition';
    } else if (lastLine.includes('{') && !lastLine.includes('}')) {
      return 'block';
    } else if (lastLine.match(/^\s*(if|for|while|try|except|with)/)) {
      return 'control_structure';
    }

    return 'global';
  }

  private detectSyntaxContext(lines: string[]): string {
    const text = lines.join(' ').toLowerCase();

    if (text.includes('import ') || text.includes('from ')) {
      return 'import';
    } else if (text.includes('class ')) {
      return 'class_definition';
    } else if (text.includes('def ') || text.includes('function ')) {
      return 'function_definition';
    } else if (text.includes('if ') || text.includes('elif ')) {
      return 'conditional';
    } else if (text.includes('for ') || text.includes('while ')) {
      return 'loop';
    }

    return 'general';
  }

  private extractVariables(lines: string[]): string[] {
    const variables: string[] = [];
    const varPattern = /(?:^|\s)([a-zA-Z_][a-zA-Z0-9_]*)\s*=/g;

    lines.forEach((line) => {
      let match;
      while ((match = varPattern.exec(line)) !== null) {
        const varName = match[1];
        if (!['if', 'for', 'while', 'def', 'class'].includes(varName)) {
          variables.push(varName);
        }
      }
    });

    return [...new Set(variables)].slice(0, 20); // 去重并限制数量
  }

  private extractFunctions(lines: string[]): string[] {
    const functions: string[] = [];
    const funcPatterns = [
      /def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g,
      /function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g,
    ];

    lines.forEach((line) => {
      funcPatterns.forEach((pattern) => {
        let match;
        while ((match = pattern.exec(line)) !== null) {
          functions.push(match[1]);
        }
      });
    });

    return [...new Set(functions)].slice(0, 10);
  }

  private extractImports(lines: string[]): string[] {
    const imports: string[] = [];

    lines.forEach((line) => {
      line = line.trim();
      if (line.startsWith('import ')) {
        const modules = line
          .substring(7)
          .split(',')
          .map((m) => m.trim());
        imports.push(...modules);
      } else if (line.startsWith('from ')) {
        const match = line.match(/from\s+(\S+)\s+import/);
        if (match) {
          imports.push(match[1]);
        }
      }
    });

    return [...new Set(imports)].slice(0, 10);
  }
}
