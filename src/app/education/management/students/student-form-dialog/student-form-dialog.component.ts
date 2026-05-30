/**
 * 学员表单对话框组件 - 新增/编辑学员信息
 */
/* eslint-disable @typescript-eslint/unbound-method */

import { CommonModule } from '@angular/common';
import { Component, Inject, OnInit } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatStepperModule } from '@angular/material/stepper';

import {
  Gender,
  ParentInfo,
  RelationshipType,
  StudentProfile,
  StudentStatus,
} from '../../../models/student.models';

@Component({
  selector: 'app-student-form-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule,
    MatStepperModule,
    MatProgressBarModule,
  ],
  templateUrl: './student-form-dialog.component.html',
  styleUrls: ['./student-form-dialog.component.scss'],
})
export class StudentFormDialogComponent implements OnInit {
  form!: FormGroup;
  loading = false;
  submitError: string | null = null;

  // 选项数据
  genderOptions: { value: Gender; label: string }[] = [
    { value: 'male', label: '男' },
    { value: 'female', label: '女' },
  ];

  statusOptions: { value: StudentStatus; label: string }[] = [
    { value: '在读', label: '在读' },
    { value: '休学', label: '休学' },
    { value: '毕业', label: '毕业' },
    { value: '退学', label: '退学' },
    { value: '转校', label: '转校' },
  ];

  relationshipOptions: { value: RelationshipType; label: string }[] = [
    { value: '父亲', label: '父亲' },
    { value: '母亲', label: '母亲' },
    { value: '其他监护人', label: '其他监护人' },
  ];

  constructor(
    private fb: FormBuilder,
    public dialogRef: MatDialogRef<StudentFormDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { student?: StudentProfile; mode: 'create' | 'edit' }
  ) {}

  ngOnInit(): void {
    this.initForm();

    if (this.data.mode === 'edit' && this.data.student) {
      this.patchFormData(this.data.student);
    }
  }

  /**
   * 初始化表单
   */
  initForm = (): void => {
    this.form = this.fb.group({
      // 基本信息
      name: ['', [Validators.required]],
      gender: ['male', [Validators.required]],
      birthDate: [null],
      grade: [''],
      school: [''],

      // 联系方式
      phone: ['', [Validators.pattern(/^\d{10,15}$/)]],
      email: ['', [Validators.email]],
      address: [''],

      // 身份证信息
      idCardNumber: ['', [Validators.pattern(/^\d{17}[\dXx]$/)]],
      idCardAddress: [''],

      // 学籍状态
      status: ['在读', [Validators.required]],
      enrollmentDate: [new Date(), [Validators.required]],
      graduationDate: [null],
      actualGraduationDate: [null],

      // 分班信息
      currentClassId: [''],
      currentClassName: [''],

      // 课时信息
      totalPurchasedHours: [0, [Validators.min(0)]],
      totalConsumedHours: [0, [Validators.min(0)]],
      remainingHours: [0, [Validators.min(0)]],

      // 家长信息 (至少一个)
      parents: this.fb.array([]),

      // 紧急联系人
      emergencyContact: [''],
      emergencyPhone: ['', [Validators.pattern(/^\d{10,15}$/)]],

      // 备注
      notes: [''],
    });
  };

  /**
   * 填充表单数据 (编辑模式)
   */
  patchFormData = (student: StudentProfile): void => {
    this.patchBasicInfo(student);
    this.patchContactInfo(student);
    this.patchStudentStatus(student);
    this.patchClassAndHours(student);
    this.patchOtherInfo(student);
    this.patchParentData(student.parents);
  };

  /**
   * 填充基本信息
   */
  private patchBasicInfo = (student: StudentProfile): void => {
    this.form.patchValue({
      name: student.name,
      gender: student.gender,
      birthDate: student.birthDate ?? null,
      grade: student.grade ?? '',
      school: student.school ?? '',
    });
  };

  /**
   * 填充联系方式
   */
  private patchContactInfo = (student: StudentProfile): void => {
    this.form.patchValue({
      phone: student.phone ?? '',
      email: student.email ?? '',
      address: student.address ?? '',
      idCardNumber: student.idCardNumber ?? '',
      idCardAddress: student.idCardAddress ?? '',
    });
  };

  /**
   * 填充学籍状态
   */
  private patchStudentStatus = (student: StudentProfile): void => {
    this.form.patchValue({
      status: student.status,
      enrollmentDate: student.enrollmentDate,
      graduationDate: student.graduationDate ?? null,
      actualGraduationDate: student.actualGraduationDate ?? null,
    });
  };

  /**
   * 填充分班和课时信息
   */
  private patchClassAndHours = (student: StudentProfile): void => {
    this.form.patchValue({
      currentClassId: student.currentClassId ?? '',
      currentClassName: student.currentClassName ?? '',
      totalPurchasedHours: student.totalPurchasedHours,
      totalConsumedHours: student.totalConsumedHours,
      remainingHours: student.remainingHours,
    });
  };

  /**
   * 填充其他信息
   */
  private patchOtherInfo = (student: StudentProfile): void => {
    this.form.patchValue({
      emergencyContact: student.emergencyContact ?? '',
      emergencyPhone: student.emergencyPhone ?? '',
      notes: student.notes ?? '',
    });
  };

  /**
   * 填充家长信息
   */
  private patchParentData = (parents?: ParentInfo[]): void => {
    if (parents?.length) {
      parents.forEach((parent) => this.addParent(parent));
    } else {
      this.addParent();
    }
  };

  /**
   * 获取家长表单数组
   */
  get parentsForm(): FormArray {
    return this.form.get('parents') as FormArray;
  }

  /**
   * 添加家长信息
   */
  addParent = (parent?: ParentInfo): void => {
    const parentGroup = this.fb.group({
      name: [parent?.name ?? '', [Validators.required]],
      relationshipType: [parent?.relationshipType ?? '父亲', [Validators.required]],
      phone: [parent?.phone ?? '', [Validators.required, Validators.pattern(/^\d{10,15}$/)]],
      email: [parent?.email ?? '', [Validators.email]],
      wechat: [parent?.wechat ?? ''],
      qq: [parent?.qq ?? ''],
      address: [parent?.address ?? ''],
      isPrimary: [parent?.isPrimary ?? false],
      notes: [parent?.notes ?? ''],
    });

    this.parentsForm.push(parentGroup);
  };

  /**
   * 移除家长信息
   */
  removeParent = (index: number): void => {
    if (this.parentsForm.length > 1) {
      this.parentsForm.removeAt(index);
    }
  };

  /**
   * 提交表单
   */
  onSubmit = (): void => {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading = true;
    this.submitError = null;

    const formData = this.form.value as Partial<StudentProfile>;

    // TODO: 调用 API 保存数据

    // 模拟提交
    setTimeout(() => {
      this.loading = false;
      this.dialogRef.close(formData);
    }, 500);
  };

  /**
   * 取消
   */
  onCancel = (): void => {
    this.dialogRef.close(null);
  };

  /**
   * 课时自动计算
   */
  onHoursChange = (): void => {
    const purchased = (this.form.get('totalPurchasedHours')?.value as number) || 0;
    const consumed = (this.form.get('totalConsumedHours')?.value as number) || 0;
    const remaining = purchased - consumed;
    this.form.get('remainingHours')?.setValue(remaining, { emitEvent: false });
  };
}
