// Three.js 扩展类型声明
// 用于解决 meshoptimizer/decoder 和 three/webgpu 模块找不到类型定义的问题

// 修复 @types/three 引用的 meshoptimizer/decoder 模块路径问题
declare module 'meshoptimizer/decoder' {
  export * from 'meshoptimizer';
}

declare module 'meshoptimizer/meshopt_decoder.module.js' {
  export class MeshoptDecoder {
    ready: Promise<void>;
    decodeVertexBuffer(
      target: Uint8Array,
      count: number,
      size: number,
      source: Uint8Array,
      filter?: string | null
    ): void;
    decodeIndexBuffer(target: Uint8Array, count: number, size: number, source: Uint8Array): void;
    decodeIndexSequence(target: Uint8Array, count: number, size: number, source: Uint8Array): void;
    setWasmUrl(url: string): void;
  }
}

declare module 'three/webgpu' {
  import { WebGLRenderer } from 'three';
  export * from 'three';

  // WebGPU Renderer 类型定义
  export interface WebGPURenderer extends WebGLRenderer {
    // WebGPU 渲染器特定属性和方法
  }

  // Renderer 类型 - 支持 WebGL 和 WebGPU
  export type Renderer = WebGLRenderer | WebGPURenderer;

  export const WebGPURenderer: new () => WebGPURenderer;
  export const WebGPUBackend: unknown;
  export const WebGPUUtils: unknown;
  export const WGSLNodeBuilder: unknown;
  export const WebGPUNodeMaterial: unknown;
  export const WebGPUNodeGeometry: unknown;
  export const WebGPUNodeObject: unknown;
  export const NodeUtils: unknown;
}

declare module 'three/addons/misc/Timer.js' {
  import { Object3D } from 'three';
  export class Timer extends Object3D {
    delta: number;
    elapsed: number;
    frameCount: number;
    reset(): void;
    update(): void;
  }
}
