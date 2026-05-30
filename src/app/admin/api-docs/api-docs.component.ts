import { Component } from '@angular/core';

@Component({
  selector: 'app-api-docs',
  template: `
    <div class="api-docs-container">
      <iframe src="http://localhost:8000/docs" frameborder="0" width="100%" height="100%"> </iframe>
    </div>
  `,
  styles: [
    `
      .api-docs-container {
        width: 100%;
        height: calc(100vh - 120px);
        position: relative;
      }

      iframe {
        width: 100%;
        height: 100%;
        border: none;
      }
    `,
  ],
})
export class ApiDocsComponent {}
