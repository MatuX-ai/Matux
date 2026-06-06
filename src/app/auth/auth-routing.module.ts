import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { LoginComponent } from './login/login.component';
import { OAuthCallbackComponent } from './oauth-callback/oauth-callback.component';
import { RegisterComponent } from './register/register.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
  {
    path: 'login',
    component: LoginComponent,
    data: {
      title: '登录',
    },
  },
  {
    path: 'register',
    component: RegisterComponent,
    data: {
      title: '注册',
    },
  },
  {
    path: 'callback',
    component: OAuthCallbackComponent,
    data: {
      title: 'OAuth 回调处理',
    },
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AuthRoutingModule {}
