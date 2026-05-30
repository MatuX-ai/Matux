/**
 * 学员编辑对话框组件
 */

import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';

import { StudentProfile } from '../../../models/student.models';
import { StudentService } from '../../../services/student.service';

export interface StudentEditDialogData {
  student: StudentProfile;
}

@Component({
  selector: 'app-student-edit-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule,
    MatIconModule,
  ],
  template: `
    <div class="dialog-container">
      <h2 mat-dialog-title>编辑学员信息</h2>

      <form [formGroup]="studentForm" (ngSubmit)="onSubmit()">
        <mat-dialog-content>
          <!-- 基本信息 -->
          <h3 class="section-title">基本信息</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>姓名</mat-label>
              <input matInput formControlName="name" placeholder="输入学员姓名" required />
              <mat-error *ngIf="studentForm.get('name')?.hasError('required')">
                姓名必填
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>性别</mat-label>
              <mat-select formControlName="gender" required>
                <mat-option value="male">男</mat-option>
                <mat-option value="female">女</mat-option>
                <mat-option value="other">其他</mat-option>
              </mat-select>
              <mat-error *ngIf="studentForm.get('gender')?.hasError('required')">
                性别必填
              </mat-error>
            </mat-form-field>
          </div>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>出生日期</mat-label>
              <input matInput formControlName="birthDate" type="date" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>年级</mat-label>
              <input matInput formControlName="grade" placeholder="例如：初三" />
            </mat-form-field>
          </div>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>学校</mat-label>
            <input matInput formControlName="school" placeholder="输入就读学校" />
          </mat-form-field>

          <!-- 联系方式 -->
          <h3 class="section-title">联系方式</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>手机号</mat-label>
              <input matInput formControlName="phone" placeholder="输入手机号" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>邮箱</mat-label>
              <input matInput formControlName="email" type="email" placeholder="输入邮箱" />
              <mat-error *ngIf="studentForm.get('email')?.hasError('email')">
                邮箱格式不正确
              </mat-error>
            </mat-form-field>
          </div>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>地址</mat-label>
            <input matInput formControlName="address" placeholder="输入地址" />
          </mat-form-field>

          <!-- 身份证信息 -->
          <h3 class="section-title">身份证信息</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>身份证号</mat-label>
              <input matInput formControlName="idCardNumber" placeholder="输入身份证号" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>户籍地址</mat-label>
              <input matInput formControlName="idCardAddress" placeholder="输入户籍地址" />
            </mat-form-field>
          </div>

          <!-- 学籍状态 -->
          <h3 class="section-title">学籍状态</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>状态</mat-label>
              <mat-select formControlName="status" required>
                <mat-option value="在读">在读</mat-option>
                <mat-option value="休学">休学</mat-option>
                <mat-option value="毕业">毕业</mat-option>
                <mat-option value="退学">退学</mat-option>
                <mat-option value="转校">转校</mat-option>
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>入学日期</mat-label>
              <input matInput formControlName="enrollmentDate" type="date" required />
              <mat-error *ngIf="studentForm.get('enrollmentDate')?.hasError('required')">
                入学日期必填
              </mat-error>
            </mat-form-field>
          </div>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>预计毕业日期</mat-label>
              <input matInput formControlName="graduationDate" type="date" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>实际毕业日期</mat-label>
              <input matInput formControlName="actualGraduationDate" type="date" />
            </mat-form-field>
          </div>

          <!-- 课时信息 -->
          <h3 class="section-title">课时信息</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>总购买课时</mat-label>
              <input matInput formControlName="totalPurchasedHours" type="number" min="0" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>总消耗课时</mat-label>
              <input matInput formControlName="totalConsumedHours" type="number" min="0" />
            </mat-form-field>
          </div>

          <mat-form-field appearance="outline" class="half-width">
            <mat-label>剩余课时</mat-label>
            <input matInput formControlName="remainingHours" type="number" min="0" />
          </mat-form-field>

          <!-- 紧急联系人 -->
          <h3 class="section-title">紧急联系人</h3>

          <div class="row">
            <mat-form-field appearance="outline" class="half-width">
              <mat-label>紧急联系人姓名</mat-label>
              <input matInput formControlName="emergencyContact" placeholder="输入紧急联系人姓名" />
            </mat-form-field>

            <mat-form-field appearance="outline" class="half-width">
              <mat-label>紧急联系电话</mat-label>
              <input matInput formControlName="emergencyPhone" placeholder="输入紧急联系电话" />
            </mat-form-field>
          </div>

          <!-- 备注 -->
          <h3 class="section-title">备注</h3>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>备注说明</mat-label>
            <textarea
              matInput
              formControlName="notes"
              rows="3"
              placeholder="输入备注信息"
            ></textarea>
          </mat-form-field>
        </mat-dialog-content>

        <mat-dialog-actions align="end">
          <button mat-button type="button" (click)="onCancel()">取消</button>
          <button
            mat-raised-button
            color="primary"
            type="submit"
            [disabled]="!studentForm.valid || isLoading"
          >
            {{ isLoading ? '保存中...' : '保存更改' }}
          </button>
        </mat-dialog-actions>
      </form>
    </div>
  `,
  styles: [
    `
      .dialog-container {
        min-width: 600px;
        max-width: 800px;
      }

      .section-title {
        font-size: 16px;
        font-weight: 500;
        margin: 24px 0 16px;
        color: rgba(0, 0, 0, 0.87);
      }

      .full-width {
        width: 100%;
        margin-bottom: 16px;
      }

      .half-width {
        width: 48%;
        margin-right: 4%;

        &:last-child {
          margin-right: 0;
        }
      }

      .row {
        display: flex;
        margin-bottom: 16px;
      }

      mat-dialog-content {
        max-height: 70vh;
        overflow-y: auto;
      }
    `,
  ],
})
export class StudentEditDialogComponent {
  studentForm: FormGroup;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<StudentEditDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: StudentEditDialogData,
    private studentService: StudentService,
    private snackBar: MatSnackBar
  ) {
    /* eslint-disable @typescript-eslint/unbound-method */
    this.studentForm = this.initForm();
    /* eslint-enable @typescript-eslint/unbound-method */
  }

  /**
   * 初始化表单
   */
  /* eslint-disable @typescript-eslint/unbound-method, complexity */
  private initForm(): FormGroup {
    return this.fb.group({
      name: [this.data.student.name, [Validators.required]],
      gender: [this.data.student.gender, [Validators.required]],
      birthDate: [this.data.student.birthDate ?? ''],
      grade: [this.data.student.grade ?? ''],
      school: [this.data.student.school ?? ''],
      phone: [this.data.student.phone ?? ''],
      email: [this.data.student.email ?? ''],
      address: [this.data.student.address ?? ''],
      idCardNumber: [this.data.student.idCardNumber ?? ''],
      idCardAddress: [this.data.student.idCardAddress ?? ''],
      status: [this.data.student.status, [Validators.required]],
      enrollmentDate: [this.data.student.enrollmentDate, [Validators.required]],
      graduationDate: [this.data.student.graduationDate ?? ''],
      actualGraduationDate: [this.data.student.actualGraduationDate ?? ''],
      totalPurchasedHours: [this.data.student.totalPurchasedHours ?? 0],
      totalConsumedHours: [this.data.student.totalConsumedHours ?? 0],
      remainingHours: [this.data.student.remainingHours ?? 0],
      emergencyContact: [this.data.student.emergencyContact ?? ''],
      emergencyPhone: [this.data.student.emergencyPhone ?? ''],
      notes: [this.data.student.notes ?? ''],
    });
  }

  onSubmit(): void {
    if (this.studentForm.invalid || this.isLoading) return;

    this.isLoading = true;
    const formValue = this.studentForm.value as Partial<StudentProfile>;

    this.studentService.updateStudent(this.data.student.id, formValue).subscribe({
      next: (updatedStudent) => {
        this.isLoading = false;
        this.snackBar.open('学员信息更新成功!', '关闭', { duration: 3000 });
        this.dialogRef.close(updatedStudent);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('更新学员信息失败:', error);
        this.snackBar.open('更新学员信息失败，请重试', '关闭', { duration: 3000 });
      },
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
