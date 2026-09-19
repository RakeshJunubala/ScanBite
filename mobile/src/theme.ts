// Colours and spacing from the design canvas ("LabelLens — MVP Screens").
import type { Verdict } from './api/types';

export const colors = {
  ground: '#F7F4EC',
  surface: '#FFFFFF',
  ink: '#16201A',
  ink2: '#3E4944',
  ink3: '#4A5550',
  caption: '#5E6862',
  line: '#ECE6D9',
  lineSoft: '#F0EBE0',
  field: '#E0DACB',
  brand: '#1D5C43',
  brandDark: '#123D2C',
  brandSoft: '#E3EFE7',
  brandMid: '#2C7556',
  brandOnDark: '#D3E6DB',
  placeholder: '#EFE6D2',
  placeholderText: '#6B5C40',
  amberBg: '#FBF0D2',
  amberText: '#7A5000',
  orange: '#B4460C',
  orangeText: '#9A3A0A',
  orangeBg: '#FBE7D6',
  orangeBar: '#D0661F',
  red: '#A11A2F',
  redText: '#8E1628',
  redBg: '#F8DDE1',
  greenText: '#1D5C43',
  greenBg: '#DCEFE3',
  great: '#1D6B45',
  limeText: '#3F6A0A',
  limeBg: '#EEF5DC',
  limeBar: '#7FA532',
  dark: '#0E1411',
  dark2: '#1C2520',
  darkText: '#E9EFEA',
  darkMuted: '#A9B5AE',
  scanAccent: '#7FD1A6',
};

export const radius = { sm: 8, md: 14, lg: 20, xl: 24, pill: 999 };

export const verdictStyle: Record<Verdict, { label: string; text: string; bg: string; ring: string }> = {
  great: { label: 'Great', text: colors.greenText, bg: colors.greenBg, ring: colors.great },
  good: { label: 'Good', text: colors.limeText, bg: colors.limeBg, ring: colors.limeBar },
  limit: { label: 'Limit', text: colors.orangeText, bg: colors.orangeBg, ring: colors.orange },
  avoid: { label: 'Avoid', text: colors.redText, bg: colors.redBg, ring: colors.red },
  unknown: { label: 'Not scored', text: colors.ink3, bg: colors.lineSoft, ring: colors.caption },
};

// System fonts for now; swap in the canvas fonts (Bricolage Grotesque,
// Instrument Sans) with expo-font once the first build works on your phone.
export const fonts = {
  display: undefined as string | undefined,
  body: undefined as string | undefined,
};
