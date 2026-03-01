export interface UserProfile {
  gender: 'male' | 'female';
  age: number;
  height: number;
  weight: number;
  goal: '减脂' | '增肌' | '维持';
  diet_prefs: string[];
  activity_level: '低' | '中' | '高';
  allergies: string[];
}

export interface ProfileResponse {
  user_id: string;
  tdee: number;
  message: string;
}

export interface DishRecommendation {
  name: string;
  reason: string;
  category: string;
}

export interface AnalyzeResult {
  dishes: string[];
  recommendations: DishRecommendation[];
  order_notes: string[];
  alternatives: string[];
  mood: string;
  goal: string;
  disclaimer: string;
  ocr_source: string;
}

export interface HistoryRecord extends AnalyzeResult {
  id: string;
  user_id: string;
  timestamp: string;
  dishes_count: number;
}

export type MoodOption = '均衡' | '更饱' | '更便宜' | '更清淡' | '更好吃';
