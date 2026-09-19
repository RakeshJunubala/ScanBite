import { API_URL, DEMO_MODE } from '../config';
import { demoAlternatives, demoProduct, demoSearch } from '../demo/demo';
import type { ProductResult } from './types';

export class NotFoundError extends Error {}
export class OfflineError extends Error {}

const TIMEOUT_MS = 8000;

async function getJson<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
  } catch (err) {
    throw new OfflineError(err instanceof Error ? err.message : String(err));
  } finally {
    clearTimeout(timer);
  }
  if (response.status === 404) throw new NotFoundError(path);
  if (!response.ok) throw new OfflineError(`Server error ${response.status}`);
  return (await response.json()) as T;
}

export async function getProduct(barcode: string): Promise<ProductResult> {
  if (DEMO_MODE) {
    const hit = demoProduct(barcode);
    if (hit) return hit;
    throw new NotFoundError(barcode);
  }
  try {
    return await getJson<ProductResult>(`/v1/products/${encodeURIComponent(barcode)}`);
  } catch (err) {
    // Demo barcodes still work when the API can't be reached.
    const hit = err instanceof OfflineError ? demoProduct(barcode) : undefined;
    if (hit) return hit;
    throw err;
  }
}

export async function getAlternatives(barcode: string): Promise<ProductResult[]> {
  if (DEMO_MODE) return demoAlternatives(barcode);
  try {
    return await getJson<ProductResult[]>(`/v1/products/${encodeURIComponent(barcode)}/alternatives`);
  } catch {
    return demoAlternatives(barcode);
  }
}

export async function search(query: string): Promise<ProductResult[]> {
  if (DEMO_MODE) return demoSearch(query);
  return getJson<ProductResult[]>(`/v1/search?q=${encodeURIComponent(query)}`);
}
