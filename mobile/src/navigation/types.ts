import type { NativeStackScreenProps } from '@react-navigation/native-stack';

export type RootStackParamList = {
  Onboarding: { editing?: boolean } | undefined;
  Home: undefined;
  Scanner: undefined;
  Result: { barcode: string };
  Search: { query: string };
};

export type ScreenProps<T extends keyof RootStackParamList> = NativeStackScreenProps<RootStackParamList, T>;
