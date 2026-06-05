import { Component } from '@angular/core';
import { routeTransition } from './animations/route.animations';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  animations: [routeTransition],
})
export class AppComponent {
  title = 'imatuproject';
}
