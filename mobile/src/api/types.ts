// Mirrors backend/app/models.py. Values are per 100 g (food) or 100 ml (drinks).

export type DataStatus = 'verified' | 'community' | 'provisional' | 'sample';
export type Verdict = 'great' | 'good' | 'limit' | 'avoid' | 'unknown';
export type Level = 'low' | 'medium' | 'high';
export type Risk = 'none' | 'low' | 'moderate' | 'high' | 'unknown';

export interface Nutriments {
  energy_kcal?: number | null;
  fat_g?: number | null;
  saturated_fat_g?: number | null;
  trans_fat_g?: number | null;
  sugars_g?: number | null;
  added_sugars_g?: number | null;
  sodium_mg?: number | null;
  fibre_g?: number | null;
  protein_g?: number | null;
  fruit_veg_nuts_pct?: number | null;
}

export interface Product {
  barcode: string;
  name: string;
  brand?: string | null;
  quantity?: string | null;
  category?: string | null;
  is_drink: boolean;
  nutriments: Nutriments;
  serving_size_g?: number | null;
  ingredients_text?: string | null;
  additives: string[];
  allergens: string[];
  traces: string[];
  labels: string[];
  image_url?: string | null;
  status: DataStatus;
}

export interface NutrientFact {
  key: string;
  label: string;
  value: number;
  unit: string;
  kind: 'negative' | 'positive' | 'neutral';
  level?: Level | null;
  percent_daily?: number | null;
  per_serving?: number | null;
}

export interface AdditiveFact {
  code: string;
  name: string;
  function: string;
  risk: Risk;
  note?: string | null;
  known: boolean;
  animal: 'yes' | 'maybe' | 'no';
}

export interface ProcessingFlag {
  key: string;
  label: string;
  penalty: number;
}

export interface ScoreResult {
  score: number | null;
  verdict: Verdict;
  reason: string;
  nutrients: NutrientFact[];
  additives: AdditiveFact[];
  processing: ProcessingFlag[];
  breakdown: {
    nutrition?: number | null;
    additive_penalty: number;
    processing_penalty: number;
    caps_applied: string[];
  };
  incomplete: boolean;
  missing: string[];
  method_version: string;
}

/**
 * Where a product sits among the others the server holds in its category.
 * Absent when the category is too small to say anything, or has no category.
 */
export interface CategoryRank {
  category: string;
  better_than_percent: number;
  total: number;
}

export interface ProductResult {
  product: Product;
  score: ScoreResult;
  rank?: CategoryRank | null;
}
