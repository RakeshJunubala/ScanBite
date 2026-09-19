import AsyncStorage from '@react-native-async-storage/async-storage';

import type { ProductResult, Verdict } from '../api/types';

export interface HistoryItem {
  barcode: string;
  name: string;
  brand?: string | null;
  quantity?: string | null;
  score: number | null;
  verdict: Verdict;
  scannedAt: number;
}

const KEY = 'scan_history_v1';
const MAX_ITEMS = 30;

export async function loadHistory(): Promise<HistoryItem[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as HistoryItem[];
  } catch {
    return [];
  }
}

export async function addToHistory(result: ProductResult): Promise<void> {
  const items = await loadHistory();
  const item: HistoryItem = {
    barcode: result.product.barcode,
    name: result.product.name,
    brand: result.product.brand,
    quantity: result.product.quantity,
    score: result.score.score,
    verdict: result.score.verdict,
    scannedAt: Date.now(),
  };
  const next = [item, ...items.filter((i) => i.barcode !== item.barcode)].slice(0, MAX_ITEMS);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
}

export async function clearHistory(): Promise<void> {
  await AsyncStorage.removeItem(KEY);
}

export function timeAgo(ms: number, now = Date.now()): string {
  const minutes = Math.round((now - ms) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? 'yesterday' : `${days} days ago`;
}
