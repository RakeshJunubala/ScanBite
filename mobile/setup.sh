#!/usr/bin/env bash
# One-time install. `npx expo install` picks the versions that match the
# Expo SDK, so nothing here is pinned by hand.
set -euo pipefail
cd "$(dirname "$0")"

npm install expo@latest
npx expo install react react-native expo-status-bar expo-camera expo-secure-store \
  @react-native-async-storage/async-storage react-native-svg \
  @react-navigation/native @react-navigation/native-stack \
  react-native-screens react-native-safe-area-context
npm install --save-dev typescript @types/react tsx

npx expo install --check || true
echo
echo "Done. Next: cp .env.example .env, then npm start and scan the QR code with Expo Go."
