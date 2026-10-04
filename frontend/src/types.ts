export type ScanConfig = {
  folder_path: string;
  overall_similarity: number;
  face_similarity: number;
  strict_mode: boolean;
};

export type ImageResult = {
  id: number;
  file_path: string;
  recommended_delete: boolean;
  user_marked_delete: boolean;
  width: number;
  height: number;
  sharpness: number;
  exposure: number;
  face_count: number;
  expression_score: number;
};

export type SimilarityGroupResult = {
  group_id: number;
  keep_image_id: number | null;
  images: ImageResult[];
};

export type SessionSummary = {
  id: number;
  folder_path: string;
  created_at: string;
  total_images: number;
  group_count: number;
};

export type SessionDetail = {
  id: number;
  folder_path: string;
  created_at: string;
  total_images: number;
  config: Record<string, unknown>;
  groups: SimilarityGroupResult[];
};

export type DeleteMarkedResponse = {
  moved: string[];
  trash_folder: string;
};
