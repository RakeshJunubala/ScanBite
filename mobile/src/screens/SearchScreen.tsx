import { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { search } from '../api/client';
import type { ProductResult } from '../api/types';
import { ScorePill } from '../components/Score';
import { IconButton } from '../components/ui';
import type { ScreenProps } from '../navigation/types';
import { colors } from '../theme';

export default function SearchScreen({ navigation, route }: ScreenProps<'Search'>) {
  const { query } = route.params;
  const [results, setResults] = useState<ProductResult[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setResults(null);
    setError(false);
    search(query)
      .then((r) => !cancelled && setResults(r))
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [query]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.topBar}>
        <IconButton icon="chevronLeft" label="Back" onPress={() => navigation.goBack()} />
        <Text style={styles.title} numberOfLines={1}>
          “{query}”
        </Text>
        <View style={{ width: 44 }} />
      </View>
      {error ? (
        <Text style={styles.message}>Search needs a connection. Try again when you're online.</Text>
      ) : results === null ? (
        <ActivityIndicator style={{ marginTop: 40 }} color={colors.brand} />
      ) : results.length === 0 ? (
        <Text style={styles.message}>Nothing found yet. Try scanning the barcode instead.</Text>
      ) : (
        <FlatList
          data={results}
          keyExtractor={(r) => r.product.barcode}
          contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 24 }}
          ItemSeparatorComponent={() => <View style={styles.sep} />}
          renderItem={({ item }) => (
            <Pressable
              onPress={() => navigation.navigate('Result', { barcode: item.product.barcode })}
              accessibilityRole="button"
              style={styles.row}
            >
              <View style={styles.thumb} />
              <View style={{ flex: 1, gap: 2 }}>
                <Text style={styles.name} numberOfLines={1}>
                  {item.product.name}
                </Text>
                <Text style={styles.meta} numberOfLines={1}>
                  {[item.product.brand, item.product.quantity].filter(Boolean).join(' · ')}
                </Text>
              </View>
              <ScorePill score={item.score.score} verdict={item.score.verdict} />
            </Pressable>
          )}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ground },
  topBar: { height: 56, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { flex: 1, textAlign: 'center', fontSize: 16, fontWeight: '600', color: colors.ink },
  message: { padding: 24, fontSize: 15, lineHeight: 22, color: colors.ink3, textAlign: 'center' },
  row: { height: 68, flexDirection: 'row', alignItems: 'center', gap: 12 },
  sep: { height: 1, backgroundColor: '#E7E2D6' },
  thumb: { width: 44, height: 44, borderRadius: 10, backgroundColor: colors.placeholder },
  name: { fontSize: 15, fontWeight: '600', color: colors.ink },
  meta: { fontSize: 13, color: colors.caption },
});
