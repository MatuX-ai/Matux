/**
 * AR/VR 课程播放器组件
 * 基于 Three.js 的 3D 交互课程播放
 * 支持 3D 模型展示、场景漫游、课程内容播放
 */
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  NgZone,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil, timeout } from 'rxjs/operators';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

import { OfflineStorageService } from '../../../core/services/offline-storage.service';
import { OfflineStorageKey } from '../../../../shared/models/offline.models';

/**
 * 【P1 修复】ARVR 课程加载统一超时兑底。避免后端代理 / CORS hang 时
 *   页面永远卡在 loading。
 */
const COURSE_LOAD_TIMEOUT_MS = 8_000;

/**
 * 【P1 终极兑底】三级定时器兑底：5s / 10s / 15s。
 *   - 5s: HTTP 应已返回或 timeout 触发（极大概率）
 *   - 10s: 中级兑底
 *   - 15s: 终极兑底，保证不再卡死
 *   三层覆盖异常: 网络 hang / change detection 异常 / NgZone 跳出等场景。
 */
const FALLBACK_LEVEL_MS = [5_000, 10_000, 15_000];

interface ARVRCourseData {
  id: number;
  title: string;
  description: string;
  model_url?: string;
  scene_config?: string;
  content_type: '3d_model' | 'ar_scene' | 'vr_scene';
  course_materials: ARVRCourseMaterial[];
}

interface ARVRCourseMaterial {
  id: number;
  title: string;
  type: string;
  content: string;
  order: number;
}

@Component({
  selector: 'app-arvr-course-player',
  templateUrl: './arvr-course-player.component.html',
  styleUrls: ['./arvr-course-player.component.scss'],
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
})
export class ARVRCoursePlayerComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('threeContainer', { static: true }) threeContainer!: ElementRef;

  courseId: string | null = null;
  courseData: ARVRCourseData | null = null;
  isLoading = true;
  errorMessage: string | null = null;
  currentMaterialIndex = 0;

  // 【启动优化 P3】离线模式标志：true 时数据来自 IndexedDB 而非后端
  isOffline = false;

  private scene: THREE.Scene | null = null;
  private camera: THREE.PerspectiveCamera | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private controls: OrbitControls | null = null;
  private model: THREE.Group | null = null;
  private animationFrameId: number | null = null;
  private destroy$ = new Subject<void>();
  /** 【P1 终极兑底】三级 timer 句柄集合，供 ngOnDestroy 清理 */
  private fallbackTimers: ReturnType<typeof setTimeout>[] = [];

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef,
    private zone: NgZone,
    private offlineStorage: OfflineStorageService
  ) {}

  ngOnInit(): void {
    try {
      this.courseId = this.route.snapshot.paramMap.get('id');
      if (this.courseId) {
        this.loadCourseData(this.courseId);
      } else {
        this.zone.run(() => {
          this.errorMessage = '课程 ID 无效';
          this.isLoading = false;
          this.cdr.detectChanges();
        });
      }
    } catch (e) {
      // 【P1 终极兑底】ngOnInit 任何异常都不能让 spinner 卡死。
      console.error('[ARVRPlayer] ngOnInit error:', e);
      this.zone.run(() => {
        this.errorMessage = '页面初始化失败：' + (e instanceof Error ? e.message : String(e));
        this.isLoading = false;
        this.cdr.detectChanges();
      });
    }
  }

  ngAfterViewInit(): void {
    // 【P1 终极兑底】WebGL 初始化异常不能让 spinner 卡死。
    try {
      this.initThreeScene();
    } catch (e) {
      console.error('[ARVRPlayer] initThreeScene error:', e);
      // 3D 场景初始化失败不影响课程数据展示，只是不渲染 3D
    }
  }

  ngOnDestroy(): void {
    this.fallbackTimers.forEach((t) => clearTimeout(t));
    this.fallbackTimers = [];
    this.destroy$.next();
    this.destroy$.complete();
    this.cleanupThreeScene();
  }

  private loadCourseData(id: string): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.isOffline = false;

    // 【P1 终极兑底】清理上一轮 timer，注册三级新 timer。
    this.fallbackTimers.forEach((t) => clearTimeout(t));
    this.fallbackTimers = [];
    FALLBACK_LEVEL_MS.forEach((ms, idx) => {
      const timer = setTimeout(() => {
        if (this.isLoading) {
          console.warn(
            `[ARVRPlayer] Fallback timer #${idx + 1} fired at ${ms}ms, forcing UI reset`
          );
          this.zone.run(() => {
            this.isLoading = false;
            if (!this.courseData) {
              this.errorMessage =
                idx === FALLBACK_LEVEL_MS.length - 1
                  ? '加载课程超时(15s)，可能是后端服务不可达'
                  : `加载较慢(${idx * 5 + 5}s)，后端可能不稳定`;
            }
            this.cdr.detectChanges();
          });
        }
      }, ms);
      this.fallbackTimers.push(timer);
    });

    // 【启动优化 P3】先查本地 IndexedDB 缓存：fast mode / 后端未就绪时立即可用
    this.tryLoadFromOfflineCache(id)
      .then((cached) => {
        if (cached) {
          // 命中本地缓存 → 直接渲染，不发 HTTP 请求
          this.fallbackTimers.forEach((t) => clearTimeout(t));
          this.fallbackTimers = [];
          this.zone.run(() => {
            this.courseData = cached;
            this.isLoading = false;
            this.isOffline = true;
            this.cdr.detectChanges();
          });
          if (cached.model_url) {
            this.loadModel(cached.model_url);
          }
          console.log(`[ARVRPlayer] 从离线缓存加载课程 ${id}`);
          return;
        }
        // 未命中 → 走原有 HTTP 路径
        this.fetchCourseFromApi(id);
      })
      .catch((err) => {
        console.warn('[ARVRPlayer] 离线缓存查询失败, 降级到 HTTP:', err);
        this.fetchCourseFromApi(id);
      });
  }

  /**
   * 【启动优化 P3】从 IndexedDB 'courses' store 读取课程
   * 仅查询 keyPath=id 命中即返回；未命中返回 null（不抛错，避免污染 HTTP 路径）
   */
  private async tryLoadFromOfflineCache(id: string): Promise<ARVRCourseData | null> {
    try {
      // OfflineStorageKey.COURSES = 'courses'，store 格式 { keyPath: 'id' }
      const cached = await this.offlineStorage.getData<ARVRCourseData & { id: string | number }>(
        OfflineStorageKey.COURSES,
        id
      );
      if (!cached) return null;
      // 兼容存储格式：可能字段是 id 字符串而非 number
      return {
        id: typeof cached.id === 'string' ? parseInt(cached.id, 10) : cached.id,
        title: cached.title,
        description: cached.description,
        model_url: cached.model_url,
        scene_config: cached.scene_config,
        content_type: cached.content_type,
        course_materials: cached.course_materials ?? [],
      } as ARVRCourseData;
    } catch (err) {
      console.warn('[ARVRPlayer] IndexedDB 查询失败:', err);
      return null;
    }
  }

  /**
   * 【启动优化 P3】从后端 API 加载课程（原有逻辑抽离）
   */
  private fetchCourseFromApi(id: string): void {
    this.http
      .get<ARVRCourseData>(`/api/v1/arvr-courses/${id}`)
      .pipe(
        // 【P1 修复】统一 8s 超时兑底。超时会被 catchError 接住。
        timeout(COURSE_LOAD_TIMEOUT_MS),
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (data) => {
          this.fallbackTimers.forEach((t) => clearTimeout(t));
          this.fallbackTimers = [];
          this.zone.run(() => {
            this.courseData = data;
            this.isLoading = false;
            this.cdr.detectChanges();
          });
          if (data.model_url) {
            this.loadModel(data.model_url);
          }
          // 【启动优化 P3】顺便写入本地缓存（fire-and-forget），下次 fast mode 命中
          void this.offlineStorage
            .setData(OfflineStorageKey.COURSES, { ...data, id: String(data.id) })
            .catch((err) => console.warn('[ARVRPlayer] 写离线缓存失败:', err));
        },
        error: (_error) => {
          this.fallbackTimers.forEach((t) => clearTimeout(t));
          this.fallbackTimers = [];
          this.zone.run(() => {
            this.isLoading = false;
            this.errorMessage = '加载课程失败，请稍后重试';
            this.cdr.detectChanges();
          });
          this.snackBar.open('加载课程失败', '关闭', { duration: 3000 });
        },
      });
  }

  private initThreeScene(): void {
    const container = this.threeContainer.nativeElement as HTMLElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a2e);

    this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    this.camera.position.set(5, 5, 5);
    this.camera.lookAt(0, 0, 0);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 1.0;

    this.addLighting();
    this.addGridHelper();
    this.startAnimationLoop();

    window.addEventListener('resize', this.onResize);
  }

  private addLighting(): void {
    if (!this.scene) return;

    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    this.scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(10, 10, 10);
    directionalLight.castShadow = true;
    this.scene.add(directionalLight);

    const backLight = new THREE.DirectionalLight(0x8888ff, 0.3);
    backLight.position.set(-5, 0, -5);
    this.scene.add(backLight);
  }

  private addGridHelper(): void {
    if (!this.scene) return;
    const gridHelper = new THREE.GridHelper(10, 10, 0x444466, 0x444466);
    this.scene.add(gridHelper);
  }

  private loadModel(url: string): void {
    // 使用 Three.js GLTFLoader 加载 3D 模型
    void import('three/examples/jsm/loaders/GLTFLoader.js').then(({ GLTFLoader }) => {
      const loader = new GLTFLoader();
      loader.load(
        url,
        (gltf) => {
          this.model = gltf.scene;
          if (this.scene && this.model) {
            this.model.scale.set(1, 1, 1);
            this.model.position.set(0, 0, 0);
            this.scene.add(this.model);
          }
        },
        undefined,
        (_error) => {
          // 模型加载失败时使用默认几何体
          this.addDefaultModel();
        }
      );
    });
  }

  private addDefaultModel(): void {
    if (!this.scene) return;

    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshStandardMaterial({
      color: 0x3d5a80,
      metalness: 0.3,
      roughness: 0.4,
    });
    const cube = new THREE.Mesh(geometry, material);
    cube.castShadow = true;
    this.scene.add(cube);

    const torusGeometry = new THREE.TorusKnotGeometry(0.8, 0.3, 64, 8);
    const torusMaterial = new THREE.MeshStandardMaterial({
      color: 0xee6c4d,
      metalness: 0.6,
      roughness: 0.2,
    });
    const torus = new THREE.Mesh(torusGeometry, torusMaterial);
    torus.position.set(2, 1, 0);
    torus.castShadow = true;
    this.scene.add(torus);
  }

  private startAnimationLoop(): void {
    const animate = (): void => {
      this.animationFrameId = requestAnimationFrame(animate);
      if (this.controls) {
        this.controls.update();
      }
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
    };
    animate();
  }

  private cleanupThreeScene(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.controls?.dispose();
    this.renderer?.dispose();
    if (this.renderer?.domElement?.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
    this.model = null;
    this.controls = null;
    this.renderer = null;
    this.camera = null;
    this.scene = null;
    window.removeEventListener('resize', this.onResize);
  }

  private readonly onResize = (): void => {
    const container = this.threeContainer?.nativeElement as HTMLElement | undefined;
    if (!container || !this.camera || !this.renderer) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };

  getCurrentMaterial(): ARVRCourseMaterial | null {
    if (!this.courseData?.course_materials) return null;
    return this.courseData.course_materials[this.currentMaterialIndex] ?? null;
  }

  prevMaterial(): void {
    if (this.currentMaterialIndex > 0) {
      this.currentMaterialIndex--;
    }
  }

  nextMaterial(): void {
    if (
      this.courseData?.course_materials &&
      this.currentMaterialIndex < this.courseData.course_materials.length - 1
    ) {
      this.currentMaterialIndex++;
    }
  }

  toggleAutoRotate(): void {
    if (this.controls) {
      this.controls.autoRotate = !this.controls.autoRotate;
    }
  }

  resetView(): void {
    this.controls?.reset();
  }

  isLastMaterial(): boolean {
    return (
      !this.courseData?.course_materials?.length ||
      this.currentMaterialIndex >= this.courseData.course_materials.length - 1
    );
  }

  retryLoad(): void {
    if (this.courseId) {
      this.loadCourseData(this.courseId);
    }
  }
}
