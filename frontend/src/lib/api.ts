import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 15000,
});

// ── Types ──────────────────────────────────────────────────────────────────

export interface Brand {
  id: number;
  name: string;
  slug: string;
  country?: string;
  founded_year?: number;
  logo_url?: string;
}

export interface Collection {
  id: number;
  brand_id: number;
  name: string;
  slug: string;
  brand?: Brand;
}

export interface WatchImage {
  id: number;
  url: string;
  angle?: string;
  is_primary: boolean;
}

export interface WatchTag {
  id: number;
  tag: string;
  confidence: number;
}

export interface WatchCard {
  id: number;
  slug: string;
  name: string;
  reference_number?: string;
  brand_name?: string;
  collection_name?: string;
  primary_image_url?: string;
  thumbnail_url?: string;
  case_diameter_mm?: number;
  case_material?: string;
  dial_color?: string;
  watch_style?: string;
  era?: string;
  production_year_start?: number;
  production_year_end?: number;
  movement_type?: string;
  similarity_score?: number;
}

export interface WatchDetail extends WatchCard {
  description?: string;
  collection?: Collection;
  images: WatchImage[];
  tags: WatchTag[];
  view_count: number;
  // Case
  case_shape?: string;
  case_thickness_mm?: number;
  lug_width_mm?: number;
  water_resistance_m?: number;
  // Dial
  dial_style?: string;
  dial_indices?: string;
  dial_complications?: string[];
  // Bezel
  bezel_type?: string;
  bezel_material?: string;
  bezel_style?: string;
  bezel_insert_color?: string;
  // Hands
  hand_style?: string;
  hand_lume?: boolean;
  // Movement
  movement_caliber?: string;
  movement_jewels?: number;
  power_reserve_hours?: number;
  frequency_bph?: number;
  // Bracelet
  bracelet_type?: string;
  bracelet_material?: string;
  clasp_type?: string;
  // Meta
  gender?: string;
  is_limited_edition?: boolean;
  limited_edition_count?: number;
  production_year_end?: number;
}

export interface SimilarWatch {
  watch: WatchCard;
  score: number;
}

export interface SearchResponse {
  results: WatchCard[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ImageSearchResponse {
  best_match?: SimilarWatch;
  similar_watches: SimilarWatch[];
  query_processed: boolean;
}

export interface FilterOptions {
  brands: { id: number; name: string }[];
  watch_styles: string[];
  eras: string[];
  case_materials: string[];
  dial_colors: string[];
  bezel_types: string[];
  hand_styles: string[];
  bracelet_types: string[];
  movement_types: string[];
  genders: string[];
  diameter_range: { min: number; max: number };
  year_range: { min: number; max: number };
}

export interface AutocompleteResult {
  suggestions: {
    type: "brand" | "collection" | "watch";
    id: number;
    label: string;
    slug: string;
  }[];
}

export interface SearchParams {
  q?: string;
  brand_ids?: string;
  watch_styles?: string;
  eras?: string;
  case_materials?: string;
  dial_colors?: string;
  bezel_types?: string;
  movement_types?: string;
  diameter_min?: number;
  diameter_max?: number;
  year_start?: number;
  year_end?: number;
  page?: number;
  per_page?: number;
}

// ── API functions ──────────────────────────────────────────────────────────

export const watchesApi = {
  list: (params: SearchParams) =>
    api.get<SearchResponse>("/api/v1/watches/", { params }).then((r) => r.data),

  featured: (limit = 12) =>
    api.get<WatchCard[]>(`/api/v1/watches/featured?limit=${limit}`).then((r) => r.data),

  trending: (style?: string, era?: string, limit = 8) =>
    api
      .get<WatchCard[]>("/api/v1/watches/trending", { params: { style, era, limit } })
      .then((r) => r.data),

  get: (slug: string) =>
    api.get<WatchDetail>(`/api/v1/watches/${slug}`).then((r) => r.data),

  similar: (slug: string, limit = 12) =>
    api
      .get<SimilarWatch[]>(`/api/v1/watches/${slug}/similar?limit=${limit}`)
      .then((r) => r.data),
};

export const searchApi = {
  byImage: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<ImageSearchResponse>("/api/v1/search/image", form).then((r) => r.data);
  },

  autocomplete: (q: string, limit = 8) =>
    api
      .get<AutocompleteResult>("/api/v1/search/autocomplete", { params: { q, limit } })
      .then((r) => r.data),
};

export const brandsApi = {
  list: () => api.get<Brand[]>("/api/v1/brands/").then((r) => r.data),
  get: (slug: string) => api.get<Brand>(`/api/v1/brands/${slug}`).then((r) => r.data),
};

export const filtersApi = {
  options: () => api.get<FilterOptions>("/api/v1/filters/options").then((r) => r.data),
};
