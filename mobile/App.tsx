import { DefaultTheme, NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { RootNavigator } from './src/navigation/RootNavigator';
import { ProfileProvider, useProfile } from './src/profile/ProfileContext';
import { colors } from './src/theme';

const navTheme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: colors.ground, primary: colors.brand, text: colors.ink, card: colors.ground },
};

function Root() {
  const { ready, hasProfile } = useProfile();
  if (!ready) return <View style={{ flex: 1, backgroundColor: colors.ground }} />;
  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style="dark" />
      <RootNavigator initial={hasProfile ? 'Home' : 'Onboarding'} />
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ProfileProvider>
        <Root />
      </ProfileProvider>
    </SafeAreaProvider>
  );
}
