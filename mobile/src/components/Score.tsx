import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import type { Verdict } from '../api/types';
import { colors, verdictStyle } from '../theme';

/** Ring that fills to the score, with the number in the middle. */
export function ScoreRing({ score, verdict, size = 104 }: { score: number | null; verdict: Verdict; size?: number }) {
  const stroke = 10;
  const r = (size - stroke) / 2 - 2;
  const circumference = 2 * Math.PI * r;
  const filled = score === null ? 0 : (Math.max(0, Math.min(100, score)) / 100) * circumference;
  const tint = verdictStyle[verdict];
  return (
    <View
      style={{ width: size, height: size }}
      accessible
      accessibilityLabel={score === null ? 'Not scored' : `Score ${score} out of 100, ${tint.label}`}
    >
      <Svg width={size} height={size} style={{ transform: [{ rotate: '-90deg' }] }}>
        <Circle cx={size / 2} cy={size / 2} r={r} stroke={tint.bg} strokeWidth={stroke} fill="none" />
        {filled > 0 && (
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={tint.ring}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={[filled, circumference]}
            fill="none"
          />
        )}
      </Svg>
      <View style={[StyleSheet.absoluteFill, styles.center]}>
        <Text style={styles.number}>{score === null ? '–' : score}</Text>
        <Text style={styles.outOf}>out of 100</Text>
      </View>
    </View>
  );
}

const BANDS: { label: string; color: string; verdict: Verdict }[] = [
  { label: 'Avoid 0–24', color: colors.red, verdict: 'avoid' },
  { label: 'Limit 25–49', color: colors.orangeBar, verdict: 'limit' },
  { label: 'Good 50–74', color: colors.limeBar, verdict: 'good' },
  { label: 'Great 75–100', color: colors.great, verdict: 'great' },
];

/** The four bands with a marker at the score, so the number has context. */
export function VerdictScale({ score, verdict }: { score: number | null; verdict: Verdict }) {
  return (
    <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <View style={styles.scaleTrack}>
        {score !== null && <View style={[styles.marker, { left: `${Math.max(0, Math.min(100, score))}%` }]} />}
        <View style={styles.bars}>
          {BANDS.map((b) => (
            <View key={b.label} style={[styles.bar, { backgroundColor: b.color }]} />
          ))}
        </View>
      </View>
      <View style={styles.labels}>
        {BANDS.map((b) => (
          <Text
            key={b.label}
            style={[styles.bandLabel, b.verdict === verdict && { color: verdictStyle[verdict].text, fontWeight: '700' }]}
          >
            {b.label}
          </Text>
        ))}
      </View>
    </View>
  );
}

/** Small pill with the score and verdict word, used in lists. */
export function ScorePill({ score, verdict }: { score: number | null; verdict: Verdict }) {
  const tint = verdictStyle[verdict];
  return (
    <View style={[styles.pill, { backgroundColor: tint.bg }]}>
      {score !== null && <Text style={[styles.pillScore, { color: tint.text }]}>{score}</Text>}
      <Text style={[styles.pillWord, { color: tint.text }]}>{tint.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', justifyContent: 'center' },
  number: { fontSize: 36, fontWeight: '800', color: colors.ink, lineHeight: 40 },
  outOf: { fontSize: 12, color: colors.caption },
  scaleTrack: { height: 18, justifyContent: 'flex-end' },
  marker: {
    position: 'absolute',
    top: 0,
    marginLeft: -6,
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 6,
    borderTopWidth: 8,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: colors.ink,
  },
  bars: { flexDirection: 'row', gap: 4, height: 8 },
  bar: { flex: 1, borderRadius: 4 },
  labels: { flexDirection: 'row', gap: 4, marginTop: 6 },
  bandLabel: { flex: 1, fontSize: 11, color: colors.caption },
  pill: { flexDirection: 'row', alignItems: 'center', gap: 5, height: 30, paddingHorizontal: 10, borderRadius: 15 },
  pillScore: { fontSize: 15, fontWeight: '800' },
  pillWord: { fontSize: 13, fontWeight: '700' },
});
