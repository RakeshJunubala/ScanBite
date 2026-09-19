import React from 'react';
import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';

import { colors, radius } from '../theme';
import { Icon, type IconName } from './Icon';

export function Card({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function SectionTitle({ title, aside }: { title: string; aside?: string }) {
  return (
    <View style={styles.sectionRow}>
      <Text style={styles.sectionTitle} accessibilityRole="header">
        {title}
      </Text>
      {aside ? <Text style={styles.aside}>{aside}</Text> : null}
    </View>
  );
}

export function PrimaryButton({ label, onPress, icon }: { label: string; onPress: () => void; icon?: IconName }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.primary, pressed && { backgroundColor: colors.brandDark }]}
    >
      {icon ? <Icon name={icon} size={19} color="#FFFFFF" /> : null}
      <Text style={styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({ label, onPress, icon }: { label: string; onPress: () => void; icon?: IconName }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.secondary, pressed && { backgroundColor: colors.brandSoft }]}
    >
      {icon ? <Icon name={icon} size={19} color={colors.brand} /> : null}
      <Text style={styles.secondaryText}>{label}</Text>
    </Pressable>
  );
}

export function TextButton({ label, onPress, icon, color = colors.brand }: { label: string; onPress: () => void; icon?: IconName; color?: string }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="button" hitSlop={8} style={styles.textButton}>
      {icon ? <Icon name={icon} size={17} color={color} /> : null}
      <Text style={[styles.textButtonLabel, { color }]}>{label}</Text>
    </Pressable>
  );
}

export function IconButton({
  icon,
  label,
  onPress,
  color = colors.ink,
  background = 'transparent',
}: {
  icon: IconName;
  label: string;
  onPress: () => void;
  color?: string;
  background?: string;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => [styles.iconButton, { backgroundColor: background, opacity: pressed ? 0.7 : 1 }]}
    >
      <Icon name={icon} size={21} color={color} />
    </Pressable>
  );
}

export function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: selected }}
      style={[styles.chip, selected ? styles.chipOn : styles.chipOff]}
    >
      {selected ? <Icon name="check" size={15} color="#FFFFFF" strokeWidth={3} /> : null}
      <Text style={[styles.chipText, { color: selected ? '#FFFFFF' : colors.ink }]}>{label}</Text>
    </Pressable>
  );
}

export function Tag({ label, color, background }: { label: string; color: string; background: string }) {
  return (
    <View style={[styles.tag, { backgroundColor: background }]}>
      <Text style={[styles.tagText, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.line },
  sectionRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 },
  sectionTitle: { fontSize: 19, fontWeight: '700', color: colors.ink },
  aside: { fontSize: 13, color: colors.caption },
  primary: {
    flexGrow: 1,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.brand,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 18,
  },
  primaryText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  secondary: {
    height: 52,
    borderRadius: 26,
    borderWidth: 1.5,
    borderColor: colors.brand,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 18,
  },
  secondaryText: { color: colors.brand, fontSize: 15, fontWeight: '700' },
  textButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 6 },
  textButtonLabel: { fontSize: 14, fontWeight: '600' },
  iconButton: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  chip: {
    height: 44,
    paddingHorizontal: 16,
    borderRadius: 22,
    borderWidth: 1.5,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  chipOn: { backgroundColor: colors.brand, borderColor: colors.brand },
  chipOff: { backgroundColor: colors.surface, borderColor: '#D9D2C2' },
  chipText: { fontSize: 15, fontWeight: '600' },
  tag: { height: 26, paddingHorizontal: 10, borderRadius: 13, alignItems: 'center', justifyContent: 'center', flexDirection: 'row' },
  tagText: { fontSize: 12, fontWeight: '700' },
});
