export type VariantOption = {
  value: string;
  available: boolean;
  price: number | null;
};

export type ProductVariant = {
  title: string;
  options: VariantOption[];
};

export type Product = {
  filename: string;
  name: string;
  brand: string;
  category: string;
  price: string;
  currency: string;
  compare_at_price?: string;
  description: string;
  key_features: string;
  image_urls: string;
  colors: string;
  video_url: string;
  variants?: string;
};
