import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';

import { SharedModule } from '../shared/shared.module';

import { OfflineModeRoutingModule } from './offline-mode-routing.module';

@NgModule({
  declarations: [],
  imports: [CommonModule, OfflineModeRoutingModule, SharedModule],
})
export class OfflineModeModule {}
