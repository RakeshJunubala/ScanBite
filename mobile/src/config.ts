// Set these in mobile/.env (see .env.example). Expo inlines EXPO_PUBLIC_* at build time.

export const APP_NAME = process.env.EXPO_PUBLIC_APP_NAME || 'LabelBol';

/** Base URL of the backend, e.g. http://192.168.1.20:8000 when testing on your phone. */
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || '').replace(/\/$/, '');

/** Demo mode serves the 8 bundled sample products and needs no backend. */
export const DEMO_MODE = process.env.EXPO_PUBLIC_DEMO_MODE === 'true' || API_URL === '';

/** Where "Report a mistake" emails go. Leave empty to hide the button. */
export const SUPPORT_EMAIL = process.env.EXPO_PUBLIC_SUPPORT_EMAIL || '';

export const DEMO_BARCODE = '2000000000015'; // fictional "Multigrain Digestive Biscuits"
