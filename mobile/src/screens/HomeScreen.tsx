import { useFocusEffect } from '@react-navigation/native';
import { useCallback, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '../components/Icon';
import { Logo } from '../components/Logo';
import { ScorePill } from '../components/Score';
import { Tag, TextButton } from '../components/ui';
import { APP_NAME, DEMO_BARCODE, DEMO_MODE } from '../config';
import { loadHistory, timeAgo, type HistoryItem } from '../history/storage';
import type { ScreenProps } from '../navigation/types';
import { useProfile } from '../profile/ProfileContext';
import { profileLabels } from '../profile/types';
import { colors, radius } from '../theme';

export default function HomeScreen({ navigation }: ScreenProps<'Home'>) {
  const { profile } = useProfile();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [query, setQuery] = useState('');
  const watching = profileLabels(profile);

  useFocusEffect(
    useCallback(() => {
      loadHistory().then(setHistory).catch(() => setHistory([]));
    }, []),
  );

  const submitSearch = () => {
    const q = query.trim();
    if (q.length >= 2) navigation.navigate('Search', { query: q });
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.brandRow}>
            <Logo />
            <Text style={styles.brand}>{APP_NAME}</Text>
          </View>
          {DEMO_MODE ? <Tag label="Demo data" color={colors.amberText} background={colors.amberBg} /> : null}
        </View>

        <View style={{ gap: 6 }}>
          <Text style={styles.hero} accessibilityRole="header">
            What's really inside?
          </Text>
          <Text style={styles.heroSub}>Scan a barcode and get a straight answer in two seconds.</Text>
        </View>

        <Pressable
          onPress={() => navigation.navigate('Scanner')}
          accessibilityRole="button"
          accessibilityLabel="Scan a product"
          style={({ pressed }) => [styles.scanCard, pressed && { backgroundColor: colors.brandDark }]}
        >
          <View style={styles.scanIcon}>
            <Icon name="scan" size={38} color="#FFFFFF" />
          </View>
          <View style={{ gap: 4 }}>
            <Text style={styles.scanTitle}>Scan a product</Text>
            <Text style={styles.scanSub}>Point your camera at the barcode</Text>
          </View>
        </Pressable>

        <View style={styles.search}>
          <Icon name="search" size={20} color={colors.caption} />
          <TextInput
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={submitSearch}
            placeholder="Search 'makhana', 'oats', a brand…"
            placeholderTextColor="#6F7872"
            returnKeyType="search"
            accessibilityLabel="Search products"
            style={styles.searchInput}
          />
        </View>

        <View style={{ gap: 4 }}>
          <View style={styles.rowBetween}>
            <Text style={styles.overline}>WATCHING FOR</Text>
            <TextButton
              label={watching.length ? 'Edit' : 'Set up'}
              onPress={() => navigation.navigate('Onboarding', { editing: true })}
            />
          </View>
          {watching.length ? (
            <View style={styles.chips}>
              {watching.map((w) => (
                <View key={w} style={styles.watchChip}>
                  <Text style={styles.watchChipText}>{w}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.muted}>No alerts yet. Add diabetes, allergies or diet so every scan checks them.</Text>
          )}
        </View>

        <View>
          <Text style={styles.sectionTitle} accessibilityRole="header">
            Recent scans
          </Text>
          {history.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.muted}>Nothing scanned yet.</Text>
              {DEMO_MODE ? (
                <TextButton
                  label="Try a demo product"
                  icon="chevronRight"
                  onPress={() => navigation.navigate('Result', { barcode: DEMO_BARCODE })}
                />
              ) : null}
            </View>
          ) : (
            history.slice(0, 8).map((item, i) => (
              <Pressable
                key={item.barcode}
                onPress={() => navigation.navigate('Result', { barcode: item.barcode })}
                accessibilityRole="button"
                style={[styles.historyRow, i < Math.min(history.length, 8) - 1 && styles.divider]}
              >
                <View style={styles.thumb} />
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={styles.historyName} numberOfLines={1}>
                    {item.name}
                  </Text>
                  <Text style={styles.historyMeta} numberOfLines={1}>
                    {[item.brand, item.quantity, timeAgo(item.scannedAt)].filter(Boolean).join(' · ')}
                  </Text>
                </View>
                <ScorePill score={item.score} verdict={item.verdict} />
              </Pressable>
            ))
          )}
        </View>

        <View style={styles.trust}>
          <Icon name="shield" size={18} color={colors.brand} />
          <Text style={styles.trustText}>No brand can pay for a better score. Ever.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ground },
  content: { padding: 20, paddingTop: 12, gap: 18 },
  header: { height: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  brand: { fontSize: 22, fontWeight: '800', color: colors.ink, letterSpacing: -0.4 },
  hero: { fontSize: 30, lineHeight: 34, fontWeight: '700', color: colors.ink, letterSpacing: -0.5 },
  heroSub: { fontSize: 15, lineHeight: 22, color: colors.ink3 },
  scanCard: {
    height: 128,
    borderRadius: radius.xl,
    backgroundColor: colors.brand,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 18,
    paddingHorizontal: 22,
  },
  scanIcon: { width: 72, height: 72, borderRadius: 20, backgroundColor: colors.brandMid, alignItems: 'center', justifyContent: 'center' },
  scanTitle: { fontSize: 24, fontWeight: '700', color: '#FFFFFF' },
  scanSub: { fontSize: 14, color: colors.brandOnDark },
  search: {
    height: 50,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.field,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
  },
  searchInput: { flex: 1, fontSize: 15, color: colors.ink, paddingVertical: 0 },
  rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  overline: { fontSize: 12, fontWeight: '700', letterSpacing: 0.7, color: colors.caption },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  watchChip: { height: 34, paddingHorizontal: 12, borderRadius: 17, backgroundColor: colors.brandSoft, justifyContent: 'center' },
  watchChipText: { fontSize: 14, fontWeight: '600', color: colors.brand },
  muted: { fontSize: 14, lineHeight: 20, color: colors.caption },
  sectionTitle: { fontSize: 19, fontWeight: '700', color: colors.ink, marginBottom: 4 },
  empty: { gap: 2, paddingVertical: 6 },
  historyRow: { height: 64, flexDirection: 'row', alignItems: 'center', gap: 12 },
  divider: { borderBottomWidth: 1, borderBottomColor: '#E7E2D6' },
  thumb: { width: 44, height: 44, borderRadius: 10, backgroundColor: colors.placeholder },
  historyName: { fontSize: 15, fontWeight: '600', color: colors.ink },
  historyMeta: { fontSize: 13, color: colors.caption },
  trust: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingBottom: 8 },
  trustText: { fontSize: 13, color: colors.ink2 },
});
