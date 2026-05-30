/**
 * 统一课件素材数据模型
 */

export type MaterialType = 'document' | 'video' | 'image' | 'interactive' | 'ar_model' | 'vr_experience' | 'arvr_scene';

export interface UnifiedMaterial {
  id: number;
  course_id: number;
  title: string;
  material_type: MaterialType;
  url: string;
  description: string | null;
  order_index: number;
  created_at: string;
}
