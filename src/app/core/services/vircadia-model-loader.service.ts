/**
 * Vircadia 模型加载器服务
 *
 * 负责从 KiCad 模型库加载电子元件 3D 模型到 Vircadia 场景
 * 支持 LOD 切换、材质管理、实例化渲染等功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';

import { GameObject } from '../../models/vircadia.models';

import { VircadiaSdkService } from './vircadia-sdk.service';

/**
 * 电子元件模型信息
 */
export interface ComponentModelInfo {
  /** 元件 ID */
  componentId: string;
  /** 元件名称 */
  componentName: string;
  /** 类别 */
  category: string;
  /** 封装类型 */
  packageType: string;
  /** LOD 级别 */
  lodLevel: 'high' | 'medium' | 'low';
  /** 模型 URL */
  modelUrl: string;
  /** 文件大小 (MB) */
  fileSizeMB: number;
  /** 三角形数量 */
  triangleCount: number;
}

/**
 * 模型库分类
 */
export interface ComponentLibrary {
  [category: string]: ComponentModelInfo[];
}

/**
 * LOD 配置
 */
export interface LODConfig {
  /** 近距离阈值 (米) */
  nearThreshold: number;
  /** 远距离阈值 (米) */
  farThreshold: number;
  /** 当前 LOD 级别 */
  currentLevel: 'high' | 'medium' | 'low';
}

@Injectable({
  providedIn: 'root',
})
export class VircadiaModelLoaderService {
  private gltfLoader: GLTFLoader;
  private loadedModels: Map<string, THREE.Group> = new Map();
  private modelCache: Map<string, THREE.Group> = new Map();

  // LOD 配置
  private defaultLODConfig: LODConfig = {
    nearThreshold: 5.0, // < 5m 使用高模
    farThreshold: 15.0, // > 15m 使用低模
    currentLevel: 'medium', // 默认使用中模
  };

  // 模型库索引
  private libraryIndex: ComponentLibrary | null = null;

  constructor(private vircadiaSdk: VircadiaSdkService) {
    this.gltfLoader = new GLTFLoader();
    this.loadLibraryIndex();
  }

  /**
   * 加载模型库索引
   */
  private async loadLibraryIndex(): Promise<void> {
    try {
      const response = await fetch('assets/models/kicad_model_index.json');
      const data = await response.json();

      this.libraryIndex = this.buildLibraryIndex(data.models);
      console.log(
        '[ModelLoader] 模型库索引加载成功:',
        Object.keys(this.libraryIndex).length,
        '个类别'
      );
    } catch (error) {}
  }

  /**
   * 构建模型库索引
   */
  private buildLibraryIndex(models: any[]): ComponentLibrary {
    const library: ComponentLibrary = {};

    for (const model of models) {
      const category = model.category;

      if (!library[category]) {
        library[category] = [];
      }

      library[category].push({
        componentId: model.id,
        componentName: model.component_name,
        category,
        packageType: model.package_type,
        lodLevel: 'medium',
        modelUrl: model.source_url.replace('.step', '.glb'),
        fileSizeMB: model.file_size_bytes / (1024 * 1024),
        triangleCount: 0, // TODO: 从元数据中读取
      });
    }

    return library;
  }

  /**
   * 加载元件模型
   *
   * @param componentId 元件 ID
   * @param lodLevel LOD 级别 (可选)
   * @returns 加载的 GameObject
   */
  async loadComponentModel(
    componentId: string,
    lodLevel: 'high' | 'medium' | 'low' = 'medium'
  ): Promise<GameObject | null> {
    try {
      // 查找模型信息
      const modelInfo = this.findModelInfo(componentId);
      if (!modelInfo) {
        return null;
      }

      // 检查缓存
      const cacheKey = `${componentId}_${lodLevel}`;
      const cachedModel = this.modelCache.get(cacheKey);

      let modelGroup: THREE.Group;

      if (cachedModel) {
        modelGroup = cachedModel.clone();
      } else {
        // 加载新模型
        modelGroup = await this.loadGLBModel(modelInfo.modelUrl);

        if (!modelGroup) {
          throw new Error('模型加载失败');
        }

        // 添加到缓存
        this.modelCache.set(cacheKey, modelGroup);
      }

      // 创建 Vircadia Entity
      const entity = await this.createVircadiaEntity(modelGroup, modelInfo);

      // 存储引用
      this.loadedModels.set(entity.id, modelGroup);

      return entity;
    } catch (error) {
      return null;
    }
  }

  /**
   * 加载 GLB 模型
   */
  private async loadGLBModel(url: string): Promise<THREE.Group> {
    return new Promise((resolve, reject) => {
      this.gltfLoader.load(
        url,
        (gltf) => {
          const group = new THREE.Group();

          // 添加所有网格
          gltf.scene.children.forEach((child) => {
            if (child instanceof THREE.Mesh) {
              group.add(child.clone());
            }
          });

          // 优化：合并几何体以减少绘制调用
          this.mergeGeometries(group);

          resolve(group);
        },
        (progress) => {
          if (progress.total > 0) {
            const percent = (progress.loaded / progress.total) * 100;
            console.log(`[ModelLoader] 加载进度：${percent.toFixed(1)}%`);
          }
        },
        (error) => {
          reject(error);
        }
      );
    });
  }

  /**
   * 合并几何体优化渲染
   */
  private mergeGeometries(group: THREE.Group): void {
    // TODO: 实现几何体合并逻辑
    // 这可以减少 draw calls，提高渲染性能
  }

  /**
   * 创建 Vircadia 实体
   */
  private async createVircadiaEntity(
    modelGroup: THREE.Group,
    modelInfo: ComponentModelInfo
  ): Promise<GameObject> {
    // 使用 Three.js 创建实体的占位符
    // 实际应该调用 Vircadia SDK 的 createEntity 方法

    const entity: GameObject = {
      id: `entity_${modelInfo.componentId}_${Date.now()}`,
      name: modelInfo.componentName,
      type: 'mesh',
      position: { x: 0, y: 0, z: 0 },
      rotation: { x: 0, y: 0, z: 0, w: 1 },
      scale: { x: 1, y: 1, z: 1 },
      visible: true,
      interactable: true,
      metadata: {
        componentId: modelInfo.componentId,
        category: modelInfo.category,
        packageType: modelInfo.packageType,
        lodLevel: modelInfo.lodLevel,
        modelUrl: modelInfo.modelUrl,
        triangleCount: modelInfo.triangleCount,
      },
    };

    return entity;
  }

  /**
   * 查找模型信息
   */
  private findModelInfo(componentId: string): ComponentModelInfo | null {
    if (!this.libraryIndex) {
      return null;
    }

    for (const category of Object.keys(this.libraryIndex)) {
      const models = this.libraryIndex[category];
      const model = models.find((m) => m.componentId === componentId);

      if (model) {
        return model;
      }
    }

    return null;
  }

  /**
   * 获取某类别的所有模型
   */
  getModelsByCategory(category: string): ComponentModelInfo[] {
    if (!this.libraryIndex) {
      return [];
    }

    return this.libraryIndex[category] || [];
  }

  /**
   * 获取所有类别
   */
  getAllCategories(): string[] {
    if (!this.libraryIndex) {
      return [];
    }

    return Object.keys(this.libraryIndex);
  }

  /**
   * 动态 LOD 切换
   *
   * @param entityId 实体 ID
   * @param cameraDistance 相机距离
   */
  updateLOD(entityId: string, cameraDistance: number): void {
    const model = this.loadedModels.get(entityId);
    if (!model) {
      return;
    }

    const config = this.defaultLODConfig;
    let targetLOD: 'high' | 'medium' | 'low';

    if (cameraDistance < config.nearThreshold) {
      targetLOD = 'high';
    } else if (cameraDistance > config.farThreshold) {
      targetLOD = 'low';
    } else {
      targetLOD = 'medium';
    }

    // 如果 LOD 需要切换
    if (config.currentLevel !== targetLOD) {
      console.log(
        `[ModelLoader] LOD 切换：${config.currentLevel} -> ${targetLOD} (距离:${cameraDistance.toFixed(1)}m)`
      );
      config.currentLevel = targetLOD;

      // TODO: 实现 LOD 切换逻辑
      // 这需要重新加载对应 LOD 级别的模型
    }
  }

  /**
   * 批量加载元件库
   */
  async loadComponentLibrary(): Promise<ComponentLibrary> {
    if (!this.libraryIndex) {
      throw new Error('模型库索引未加载');
    }

    // 预加载常用模型
    const commonCategories = ['resistor', 'capacitor', 'led'];

    for (const category of commonCategories) {
      const models = this.getModelsByCategory(category);

      // 每类只预加载前 5 个常用模型
      for (let i = 0; i < Math.min(models.length, 5); i++) {
        try {
          await this.loadComponentModel(models[i].componentId, 'medium');
        } catch (error) {}
      }
    }

    return this.libraryIndex;
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.modelCache.clear();
  }

  /**
   * 移除已加载的模型
   */
  removeModel(entityId: string): void {
    const model = this.loadedModels.get(entityId);

    if (model) {
      // 清理 Three.js 资源
      model.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach((m) => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });

      this.loadedModels.delete(entityId);
    }
  }
}
