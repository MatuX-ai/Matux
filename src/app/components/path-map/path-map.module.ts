import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { PathMapComponent } from './path-map.component';

@NgModule({
  declarations: [PathMapComponent],
  imports: [CommonModule, FormsModule],
  exports: [PathMapComponent],
})
export class PathMapModule {}
