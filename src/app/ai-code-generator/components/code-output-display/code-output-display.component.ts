import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';

import { ProgrammingLanguage } from '../../../../ai-sdk/types';

@Component({
  selector: 'app-code-output-display',
  standalone: false,
  templateUrl: './code-output-display.component.html',
  styleUrls: ['./code-output-display.component.scss'],
})
export class CodeOutputDisplayComponent {
  @ViewChild('codeOutput') codeOutput!: ElementRef;

  @Input() generatedCode = '';
  @Input() isGenerating = false;
  @Input() language: ProgrammingLanguage = ProgrammingLanguage.PYTHON;

  @Output() copyCode = new EventEmitter<void>();
  @Output() downloadCode = new EventEmitter<void>();

  scrollToOutput(): void {
    setTimeout(() => {
      this.codeOutput.nativeElement.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }
}
