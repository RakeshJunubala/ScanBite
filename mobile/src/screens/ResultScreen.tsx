import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { getAlternatives, getProduct, InvalidBarcodeError, NotFoundError, SourceUnavailableError } from '../api/client';
import type { AdditiveFact, NutrientFact, Product, ProductResult, Risk } from '../api/types';
import { Icon, type IconName } from '../components/Icon';
import { PackImage } from '../components/PackImage';
import { ScorePill, ScoreRing, VerdictScale } from '../components/Score';
import { Card, IconButton, PrimaryButton, SecondaryButton, SectionTitle, Tag, TextButton } from '../components/ui';
import { API_URL, SUPPORT_EMAIL } from '../config';
import { addToHistory } from '../history/storage';
import type { ScreenProps } from '../navigation/types';
import { profileAlerts, type Alert, type AlertStatus } from '../profile/alerts';
import { useProfile } from '../profile/ProfileContext';
import { colors, radius, verdictStyle } from '../theme';

type LoadState =
  | { kind: 'loading' }
  | { kind: 'ready'; result: ProductResult }
  | { kind: 'not_found' }
  | { kind: 'source_down' }
  | { kind: 'bad_barcode' }
  | { kind: 'error'; message: string };

export default function ResultScreen({ navigation, route }: ScreenProps<'Result'>) {
  const { barcode } = route.params;
  const { profile } = useProfile();
  const [state, setState] = useState<LoadState>({ kind: 'loading' });
  const [alternatives, setAlternatives] = useState<ProductResult[]>([]);

  const load = useCallback(async () => {
    setState({ kind: 'loading' });
    try {
      const result = await getProduct(barcode);
      setState({ kind: 'ready', result });
      addToHistory(result).catch(() => undefined);
      getAlternatives(barcode).then(setAlternatives).catch(() => setAlternatives([]));
    } catch (err) {
      if (err instanceof NotFoundError) setState({ kind: 'not_found' });
      else if (err instanceof SourceUnavailableError) setState({ kind: 'source_down' });
      else if (err instanceof InvalidBarcodeError) setState({ kind: 'bad_barcode' });
      else setState({ kind: 'error', message: err instanceof Error ? err.message : String(err) });
    }
  }, [barcode]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.topBar}>
        <IconButton icon="chevronLeft" label="Back" onPress={() => navigation.goBack()} />
        <Text style={styles.topTitle}>Scan result</Text>
        <IconButton icon="scan" label="Scan another product" onPress={() => navigation.navigate('Scanner')} />
      </View>
      {state.kind === 'loading' && (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.brand} />
          <Text style={styles.muted}>Reading the label…</Text>
        </View>
      )}
      {state.kind === 'not_found' && (
        <Message
          icon="question"
          title="Not in our database yet"
          body={`We don't have barcode ${barcode} yet. Adding a product from label photos comes in the next update.`}
          primary={{ label: 'Scan another', onPress: () => navigation.replace('Scanner') }}
          secondary={{ label: 'Home', onPress: () => navigation.popToTop() }}
        />
      )}
      {state.kind === 'source_down' && (
        <Message
          icon="alert"
          title="Couldn't check Open Food Facts"
          body={`We don't have barcode ${barcode} ourselves, and the product database we check didn't answer just now. This doesn't mean the product is missing — try again in a moment.`}
          primary={{ label: 'Try again', onPress: load }}
          secondary={{ label: 'Home', onPress: () => navigation.popToTop() }}
        />
      )}
      {state.kind === 'bad_barcode' && (
        <Message
          icon="alert"
          title="That barcode doesn't look right"
          body={`${barcode} isn't a valid product barcode. If you typed it, check the digits under the barcode on the pack and try again.`}
          primary={{ label: 'Scan again', onPress: () => navigation.replace('Scanner') }}
          secondary={{ label: 'Home', onPress: () => navigation.popToTop() }}
        />
      )}
      {state.kind === 'error' && (
        <Message
          icon="alert"
          title="Can't reach the server"
          body={`Check your internet connection and try again.${__DEV__ ? `\n\nAPI: ${API_URL || '(not set)'}\n${state.message}` : ''}`}
          primary={{ label: 'Try again', onPress: load }}
          secondary={{ label: 'Home', onPress: () => navigation.popToTop() }}
        />
      )}
      {state.kind === 'ready' && (
        <Details
          result={state.result}
          alerts={profileAlerts(profile, state.result.product, state.result.score)}
          alternatives={alternatives}
          onOpen={(code) => navigation.push('Result', { barcode: code })}
          onScanNext={() => navigation.navigate('Scanner')}
          onEditAlerts={() => navigation.navigate('Onboarding', { editing: true })}
        />
      )}
    </SafeAreaView>
  );
}

// ---------------------------------------------------------------------------------

function Details({
  result,
  alerts,
  alternatives,
  onOpen,
  onScanNext,
  onEditAlerts,
}: {
  result: ProductResult;
  alerts: Alert[];
  alternatives: ProductResult[];
  onOpen: (barcode: string) => void;
  onScanNext: () => void;
  onEditAlerts: () => void;
}) {
  const { product, score } = result;
  const tint = verdictStyle[score.verdict];
  const [showMethod, setShowMethod] = useState(false);

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <ProductHeader product={product} />

      <Card style={styles.verdictCard}>
        <View style={styles.verdictRow}>
          <ScoreRing score={score.score} verdict={score.verdict} />
          <View style={{ flex: 1, gap: 6 }}>
            <Text style={[styles.verdictWord, { color: tint.ring }]}>{tint.label}</Text>
            <Text style={styles.body}>{score.reason}</Text>
          </View>
        </View>
        {score.score !== null && <VerdictScale score={score.score} verdict={score.verdict} />}
        {score.incomplete && score.score !== null ? <LowConfidence missing={score.missing} /> : null}
        <TextButton label={showMethod ? 'Hide how this is scored' : 'How is this scored?'} icon="info" onPress={() => setShowMethod(!showMethod)} />
        {showMethod ? <Method result={result} /> : null}
      </Card>

      <View>
        <SectionTitle title="For your profile" />
        {alerts.length ? (
          <Card>
            {alerts.map((a, i) => (
              <AlertRow key={a.id} alert={a} last={i === alerts.length - 1} />
            ))}
          </Card>
        ) : (
          <Card style={styles.padded}>
            <Text style={styles.body}>Add diabetes, allergies or your diet and we'll check every scan for you.</Text>
            <TextButton label="Set up alerts" icon="chevronRight" onPress={onEditAlerts} />
          </Card>
        )}
      </View>

      {alternatives.length > 0 && (
        <View>
          <SectionTitle title="Better choices" />
          <Text style={[styles.muted, { marginTop: -6, marginBottom: 10 }]}>Same category, ranked by score only. No brand pays to be here.</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 12, paddingRight: 16 }}>
            {alternatives.map((alt) => (
              <Pressable key={alt.product.barcode} onPress={() => onOpen(alt.product.barcode)} accessibilityRole="button" style={styles.altCard}>
                <PackImage uri={alt.product.image_url} style={styles.altImage} />
                <Text style={styles.altName} numberOfLines={2}>
                  {alt.product.name}
                </Text>
                <Text style={styles.small} numberOfLines={1}>
                  {[alt.product.brand, alt.product.quantity].filter(Boolean).join(' · ')}
                </Text>
                <ScorePill score={alt.score.score} verdict={alt.score.verdict} />
                {alt.score.score !== null && score.score !== null ? (
                  <Text style={styles.altDelta}>+{alt.score.score - score.score} points</Text>
                ) : null}
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}

      <Nutrition product={product} nutrients={score.nutrients} />

      {score.additives.length > 0 && <Additives additives={score.additives} />}

      {product.ingredients_text ? (
        <View>
          <SectionTitle title="Ingredients" />
          <Card style={styles.padded}>
            <Text style={styles.ingredients}>{product.ingredients_text}</Text>
            {product.allergens.length > 0 || product.traces.length > 0 ? (
              <View style={styles.allergens}>
                {product.allergens.length > 0 && (
                  <Text style={styles.small}>
                    <Text style={styles.bold}>Contains: </Text>
                    {product.allergens.join(', ')}
                  </Text>
                )}
                {product.traces.length > 0 && (
                  <Text style={styles.small}>
                    <Text style={styles.bold}>May contain: </Text>
                    {product.traces.join(', ')}
                  </Text>
                )}
              </View>
            ) : null}
          </Card>
        </View>
      ) : null}

      <View style={styles.actions}>
        <PrimaryButton label="Scan next" icon="scan" onPress={onScanNext} />
      </View>
      {SUPPORT_EMAIL ? (
        <View style={{ alignItems: 'center' }}>
          <TextButton
            label="Something wrong? Report it"
            icon="flag"
            color={colors.ink2}
            onPress={() =>
              Linking.openURL(
                `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(`Wrong data: ${product.name} (${product.barcode})`)}`,
              )
            }
          />
        </View>
      ) : null}

      <View style={styles.trust}>
        <Icon name="shield" size={20} color={colors.brand} />
        <Text style={styles.trustText}>
          <Text style={styles.bold}>Independent score.</Text> No ads, no sponsored products, no brand money. Draft method{' '}
          {score.method_version}, under dietitian review.
        </Text>
      </View>

      {product.status === 'community' ? <Attribution barcode={product.barcode} /> : null}
    </ScrollView>
  );
}

function ProductHeader({ product }: { product: Product }) {
  const status = {
    verified: { label: 'Verified data', color: colors.brand, bg: colors.brandSoft },
    community: { label: 'Community data', color: colors.amberText, bg: colors.amberBg },
    provisional: { label: 'Provisional', color: colors.amberText, bg: colors.amberBg },
    sample: { label: 'Demo product', color: colors.ink3, bg: colors.lineSoft },
  }[product.status];
  const veg = product.labels.includes('vegetarian');
  return (
    <Card style={styles.productCard}>
      <PackImage
        uri={product.image_url}
        style={styles.productImage}
        caption={`Pack\nphoto`}
        accessibilityLabel={`Pack photo of ${product.name}`}
      />
      <View style={{ flex: 1, gap: 6 }}>
        <Text style={styles.productName} accessibilityRole="header">
          {product.name}
        </Text>
        <Text style={styles.small}>{[product.brand, product.quantity].filter(Boolean).join(' · ')}</Text>
        <View style={styles.tags}>
          {veg ? (
            <View style={styles.vegRow}>
              <View style={styles.vegMark} accessibilityLabel="Vegetarian mark">
                <View style={styles.vegDot} />
              </View>
              <Text style={styles.vegText}>Veg</Text>
            </View>
          ) : null}
          <Tag label={status.label} color={status.color} background={status.bg} />
        </View>
      </View>
    </Card>
  );
}

const OFF_PRODUCT_URL = 'https://world.openfoodfacts.org/product/';
const ODBL_URL = 'https://opendatacommons.org/licenses/odbl/1-0/';

/**
 * Open Food Facts is ODbL (share-alike), which requires us to say where the
 * data came from and under what licence. Shown only for `community` records,
 * because our own verified and provisional records are not theirs.
 */
function Attribution({ barcode }: { barcode: string }) {
  return (
    <Text style={styles.attribution}>
      Product data from{' '}
      <Text style={styles.link} onPress={() => Linking.openURL(`${OFF_PRODUCT_URL}${encodeURIComponent(barcode)}`)}>
        Open Food Facts
      </Text>
      , contributed by volunteers and used under the{' '}
      <Text style={styles.link} onPress={() => Linking.openURL(ODBL_URL)}>
        Open Database Licence (ODbL)
      </Text>
      . We have not checked it against the pack ourselves.
    </Text>
  );
}

// The backend's CORE_NUTRIENTS keys, in plain words. Indian labels print salt
// rather than sodium, so that is what we call it.
const MISSING_LABEL: Record<string, string> = {
  energy_kcal: 'energy',
  sugars_g: 'sugar',
  saturated_fat_g: 'saturated fat',
  sodium_mg: 'salt',
};

/**
 * A score built on a partial nutrition table. This is deliberately loud: the
 * ring above it looks equally confident whether we had four values or one, and
 * for a health decision the person needs to know which it was.
 */
function LowConfidence({ missing }: { missing: string[] }) {
  const names = missing.map((k) => MISSING_LABEL[k] ?? k.replace(/_g$|_mg$|_kcal$/, '').replace(/_/g, ' '));
  const list =
    names.length <= 1 ? names[0] : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
  return (
    <View style={styles.lowConf} accessibilityRole="alert">
      <Icon name="alert" size={18} color={colors.amberText} />
      <Text style={styles.lowConfText}>
        <Text style={styles.bold}>Low confidence. </Text>
        This label is missing {list}, so the score is based on incomplete data and may change.
      </Text>
    </View>
  );
}

function Method({ result }: { result: ProductResult }) {
  const { breakdown, processing } = result.score;
  return (
    <View style={styles.method}>
      <Text style={styles.small}>
        We start from the nutrition table (sugar, saturated fat, salt and energy against fibre and protein), then take
        points off for additives to watch and signs of heavy processing.
      </Text>
      {breakdown.nutrition != null && (
        <Text style={styles.small}>
          Nutrition: {Math.round(breakdown.nutrition)}/100 · additives −{Math.round(breakdown.additive_penalty * 100)}% · processing −
          {Math.round(breakdown.processing_penalty * 100)}%
        </Text>
      )}
      {processing.map((p) => (
        <Text key={p.key} style={styles.small}>
          • {p.label}
        </Text>
      ))}
      {breakdown.caps_applied.includes('high_risk_additive') && <Text style={styles.small}>• Capped at 49: has a high-risk additive</Text>}
      {breakdown.caps_applied.includes('sweetened_drink') && <Text style={styles.small}>• Capped at 49: sweetened drink</Text>}
    </View>
  );
}

const ALERT_LOOK: Record<AlertStatus, { icon: IconName; color: string; bg: string }> = {
  warn: { icon: 'alert', color: colors.orangeText, bg: colors.orangeBg },
  caution: { icon: 'alert', color: colors.amberText, bg: colors.amberBg },
  ok: { icon: 'check', color: colors.great, bg: colors.greenBg },
  unknown: { icon: 'question', color: colors.ink3, bg: colors.lineSoft },
};

function AlertRow({ alert, last }: { alert: Alert; last: boolean }) {
  const look = ALERT_LOOK[alert.status];
  return (
    <View style={[styles.alertRow, !last && styles.rowDivider]}>
      <View style={[styles.alertIcon, { backgroundColor: look.bg }]}>
        <Icon name={look.icon} size={16} color={look.color} strokeWidth={2.6} />
      </View>
      <View style={{ flex: 1, gap: 3 }}>
        <Text style={styles.alertTitle}>{alert.title}</Text>
        <Text style={styles.body}>{alert.detail}</Text>
      </View>
    </View>
  );
}

const LEVEL_LOOK = {
  negative: {
    high: { label: 'High', color: colors.orangeText, bg: colors.orangeBg, bar: colors.orangeBar },
    medium: { label: 'Medium', color: colors.amberText, bg: colors.amberBg, bar: '#C98A12' },
    low: { label: 'Low', color: colors.greenText, bg: colors.greenBg, bar: colors.great },
  },
  positive: {
    high: { label: 'High', color: colors.greenText, bg: colors.greenBg, bar: colors.great },
    medium: { label: 'Good', color: colors.greenText, bg: colors.greenBg, bar: colors.great },
    low: { label: 'Low', color: colors.ink2, bg: '#F1EDE3', bar: colors.caption },
  },
} as const;

function Nutrition({ product, nutrients }: { product: Product; nutrients: NutrientFact[] }) {
  const canServe = Boolean(product.serving_size_g);
  const [perServing, setPerServing] = useState(false);
  const unit = product.is_drink ? 'ml' : 'g';
  const negatives = nutrients.filter((n) => n.kind === 'negative');
  const positives = nutrients.filter((n) => n.kind === 'positive');
  const energy = nutrients.find((n) => n.kind === 'neutral');
  const value = (n: NutrientFact) => {
    const v = perServing && n.per_serving != null ? n.per_serving : n.value;
    return `${v} ${n.unit}`;
  };
  // % of the daily limit for what's shown: per 100 g/ml, or per serving.
  const dailyShare = (n: NutrientFact): number => {
    const per100 = n.percent_daily ?? 0;
    if (!perServing || n.per_serving == null || n.value <= 0) return per100;
    return Math.round((per100 * n.per_serving) / n.value);
  };
  if (!nutrients.length) return null;

  return (
    <View>
      <View style={styles.nutritionHeader}>
        <Text style={styles.sectionTitleInline} accessibilityRole="header">
          Nutrition
        </Text>
        {canServe && (
          <View style={styles.segment}>
            {[false, true].map((serving) => (
              <Pressable
                key={String(serving)}
                onPress={() => setPerServing(serving)}
                accessibilityRole="button"
                accessibilityState={{ selected: perServing === serving }}
                style={[styles.segmentButton, perServing === serving && styles.segmentOn]}
              >
                <Text style={[styles.segmentText, perServing === serving && { color: colors.ink, fontWeight: '700' }]}>
                  {serving ? `Per ${product.serving_size_g} ${unit}` : `Per 100 ${unit}`}
                </Text>
              </Pressable>
            ))}
          </View>
        )}
      </View>
      <Card style={[styles.padded, { gap: 14 }]}>
        {negatives.length > 0 && <Text style={[styles.overline, { color: colors.orangeText }]}>WATCH OUT</Text>}
        {negatives.map((n) => {
          const look = LEVEL_LOOK.negative[n.level ?? 'low'];
          return (
            <View key={n.key} style={{ gap: 6 }}>
              <View style={styles.nutrientRow}>
                <Text style={styles.nutrientName}>{n.label}</Text>
                <Text style={styles.nutrientValue}>{value(n)}</Text>
                <Tag label={look.label} color={look.color} background={look.bg} />
              </View>
              {n.percent_daily != null && (
                <View style={styles.barRow}>
                  <View style={styles.barTrack}>
                    <View style={[styles.barFill, { width: `${Math.min(100, dailyShare(n))}%`, backgroundColor: look.bar }]} />
                  </View>
                  <Text style={styles.barLabel}>{dailyShare(n)}% of daily limit</Text>
                </View>
              )}
            </View>
          );
        })}
        {positives.length > 0 && (
          <>
            <View style={styles.hr} />
            <Text style={[styles.overline, { color: colors.brand }]}>GOOD STUFF</Text>
            {positives.map((n) => {
              const look = LEVEL_LOOK.positive[n.level ?? 'low'];
              return (
                <View key={n.key} style={styles.nutrientRow}>
                  <Text style={styles.nutrientName}>{n.label}</Text>
                  <Text style={styles.nutrientValue}>{value(n)}</Text>
                  <Tag label={look.label} color={look.color} background={look.bg} />
                </View>
              );
            })}
          </>
        )}
        {energy && (
          <View style={styles.energy}>
            <Text style={styles.small}>
              Energy {value(energy)}
              {energy.percent_daily != null && !perServing ? ` · ${energy.percent_daily}% of a 2,000 kcal day` : ''}
            </Text>
            <Text style={styles.caption}>Daily limits use reference values for a 2,000 kcal diet.</Text>
          </View>
        )}
      </Card>
    </View>
  );
}

const RISK_LOOK: Record<Risk, { label: string; color: string; bg: string }> = {
  none: { label: 'None', color: colors.greenText, bg: colors.greenBg },
  low: { label: 'Low', color: colors.greenText, bg: colors.greenBg },
  moderate: { label: 'Moderate', color: colors.amberText, bg: colors.amberBg },
  high: { label: 'High', color: colors.redText, bg: colors.redBg },
  unknown: { label: 'Unknown', color: colors.ink3, bg: colors.lineSoft },
};
const RISK_ORDER: Record<Risk, number> = { high: 0, moderate: 1, unknown: 2, low: 3, none: 4 };

function Additives({ additives }: { additives: AdditiveFact[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const sorted = useMemo(() => [...additives].sort((a, b) => RISK_ORDER[a.risk] - RISK_ORDER[b.risk]), [additives]);
  const toWatch = additives.filter((a) => a.risk === 'moderate' || a.risk === 'high').length;
  return (
    <View>
      <SectionTitle title="Additives" aside={`${additives.length} found${toWatch ? ` · ${toWatch} to watch` : ''}`} />
      <Card>
        {sorted.map((a, i) => {
          const look = RISK_LOOK[a.risk];
          const expanded = open === a.code;
          return (
            <Pressable
              key={a.code}
              onPress={() => setOpen(expanded ? null : a.code)}
              accessibilityRole="button"
              accessibilityState={{ expanded }}
              style={[styles.additiveRow, i < sorted.length - 1 && styles.rowDivider]}
            >
              <View style={styles.additiveTop}>
                <View style={styles.insChip}>
                  <Text style={styles.insText}>INS {a.code}</Text>
                </View>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={styles.additiveName}>{a.name}</Text>
                  <Text style={styles.small}>{a.function}</Text>
                </View>
                <Tag label={look.label} color={look.color} background={look.bg} />
                <Icon name={expanded ? 'chevronDown' : 'chevronRight'} size={16} color="#7D8781" />
              </View>
              {expanded ? (
                <Text style={[styles.small, { marginTop: 8 }]}>{a.note ?? 'No known concern at normal intake.'}</Text>
              ) : null}
            </Pressable>
          );
        })}
      </Card>
    </View>
  );
}

function Message({
  icon,
  title,
  body,
  primary,
  secondary,
}: {
  icon: IconName;
  title: string;
  body: string;
  primary: { label: string; onPress: () => void };
  secondary: { label: string; onPress: () => void };
}) {
  return (
    <View style={styles.message}>
      <View style={styles.messageIcon}>
        <Icon name={icon} size={30} color={colors.amberText} />
      </View>
      <Text style={styles.messageTitle}>{title}</Text>
      <Text style={[styles.body, { textAlign: 'center' }]}>{body}</Text>
      <View style={styles.messageButtons}>
        <PrimaryButton label={primary.label} onPress={primary.onPress} />
      </View>
      <SecondaryButton label={secondary.label} onPress={secondary.onPress} />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ground },
  topBar: { height: 56, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  topTitle: { fontSize: 16, fontWeight: '600', color: colors.ink },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  content: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 32, gap: 18 },
  padded: { padding: 16, gap: 10 },
  body: { fontSize: 14, lineHeight: 20, color: colors.ink2 },
  small: { fontSize: 13, lineHeight: 19, color: colors.ink3 },
  caption: { fontSize: 12, lineHeight: 17, color: colors.caption },
  muted: { fontSize: 13, lineHeight: 19, color: colors.caption },
  bold: { fontWeight: '700', color: colors.ink2 },
  lowConf: {
    flexDirection: 'row',
    gap: 9,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E8CE8A',
    backgroundColor: colors.amberBg,
  },
  lowConfText: { flex: 1, fontSize: 13, lineHeight: 19, color: colors.amberText },
  overline: { fontSize: 12, fontWeight: '700', letterSpacing: 0.7 },
  productCard: { flexDirection: 'row', gap: 14, padding: 16 },
  productImage: { width: 84, height: 84, borderRadius: 14, backgroundColor: colors.placeholder, alignItems: 'center', justifyContent: 'center' },
  productName: { fontSize: 19, lineHeight: 23, fontWeight: '700', color: colors.ink },
  tags: { flexDirection: 'row', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  vegRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  vegMark: { width: 15, height: 15, borderWidth: 1.6, borderColor: '#1E7B34', borderRadius: 2, alignItems: 'center', justifyContent: 'center' },
  vegDot: { width: 7, height: 7, borderRadius: 3.5, backgroundColor: '#1E7B34' },
  vegText: { fontSize: 12, fontWeight: '600', color: '#1E6B30' },
  verdictCard: { padding: 20, paddingBottom: 8, gap: 16 },
  verdictRow: { flexDirection: 'row', alignItems: 'center', gap: 18 },
  verdictWord: { fontSize: 30, fontWeight: '800', letterSpacing: -0.5 },
  method: { gap: 6, paddingBottom: 12 },
  alertRow: { flexDirection: 'row', gap: 12, paddingVertical: 14, paddingHorizontal: 16 },
  rowDivider: { borderBottomWidth: 1, borderBottomColor: colors.lineSoft },
  alertIcon: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  alertTitle: { fontSize: 15, fontWeight: '700', color: colors.ink },
  altCard: { width: 152, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line, padding: 10, gap: 8 },
  altImage: { height: 88, borderRadius: 12, backgroundColor: '#E9EFDF' },
  altName: { fontSize: 14, fontWeight: '700', lineHeight: 18, height: 36, color: colors.ink },
  altDelta: { fontSize: 12, fontWeight: '600', color: colors.brand },
  nutritionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  sectionTitleInline: { fontSize: 19, fontWeight: '700', color: colors.ink },
  segment: { flexDirection: 'row', padding: 2, borderRadius: 22, backgroundColor: colors.line },
  segmentButton: { height: 40, paddingHorizontal: 12, borderRadius: 20, justifyContent: 'center' },
  segmentOn: { backgroundColor: colors.surface },
  segmentText: { fontSize: 13, fontWeight: '600', color: colors.ink2 },
  nutrientRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  nutrientName: { flex: 1, fontSize: 15, fontWeight: '600', color: colors.ink },
  nutrientValue: { fontSize: 15, fontWeight: '700', color: colors.ink },
  barRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  barTrack: { flex: 1, height: 6, borderRadius: 3, backgroundColor: colors.lineSoft, overflow: 'hidden' },
  barFill: { height: 6 },
  barLabel: { width: 124, fontSize: 12, textAlign: 'right', color: colors.caption },
  hr: { height: 1, backgroundColor: colors.lineSoft },
  energy: { paddingTop: 12, borderTopWidth: 1, borderTopColor: colors.lineSoft, gap: 4 },
  additiveRow: { paddingVertical: 12, paddingLeft: 16, paddingRight: 14 },
  additiveTop: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  insChip: { width: 78, paddingVertical: 6, borderRadius: radius.sm, backgroundColor: '#F1EDE3', alignItems: 'center' },
  insText: { fontSize: 12, fontWeight: '700', color: colors.ink2 },
  additiveName: { fontSize: 15, fontWeight: '600', color: colors.ink },
  ingredients: { fontSize: 14, lineHeight: 22, color: colors.ink2 },
  allergens: { paddingTop: 12, borderTopWidth: 1, borderTopColor: colors.lineSoft, gap: 4 },
  actions: { flexDirection: 'row', gap: 10, paddingTop: 4 },
  trust: { flexDirection: 'row', gap: 10, padding: 14, borderRadius: 16, backgroundColor: colors.brandSoft },
  trustText: { flex: 1, fontSize: 13, lineHeight: 19, color: colors.brand },
  attribution: { fontSize: 12, lineHeight: 18, color: colors.caption, paddingHorizontal: 2 },
  link: { color: colors.brand, fontWeight: '600', textDecorationLine: 'underline' },
  message: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28, gap: 14 },
  messageIcon: { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.amberBg, alignItems: 'center', justifyContent: 'center' },
  messageTitle: { fontSize: 22, fontWeight: '700', color: colors.ink, textAlign: 'center' },
  messageButtons: { flexDirection: 'row', alignSelf: 'stretch', marginTop: 8 },
});
