import React, { useState } from 'react';
import { Alert as RNAlert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '../components/Icon';
import { Logo } from '../components/Logo';
import { Chip, PrimaryButton, TextButton } from '../components/ui';
import type { ScreenProps } from '../navigation/types';
import { useProfile } from '../profile/ProfileContext';
import {
  ALLERGY_OPTIONS,
  CONDITION_OPTIONS,
  DIET_OPTIONS,
  EMPTY_PROFILE,
  profileSize,
  type Profile,
} from '../profile/types';
import { colors } from '../theme';

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item];
}

export default function OnboardingScreen({ navigation, route }: ScreenProps<'Onboarding'>) {
  const editing = route.params?.editing ?? false;
  const { profile, setProfile, clearProfile } = useProfile();
  const [draft, setDraft] = useState<Profile>(editing ? profile : EMPTY_PROFILE);
  const count = profileSize(draft);

  const finish = async (next: Profile) => {
    await setProfile(next);
    if (editing) navigation.goBack();
    else navigation.reset({ index: 0, routes: [{ name: 'Home' }] });
  };

  const confirmDelete = () => {
    RNAlert.alert('Delete your health choices?', 'This removes them from this phone. Your scan history stays.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await clearProfile();
          setDraft(EMPTY_PROFILE);
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Logo size={26} />
          <Text style={styles.headerText}>{editing ? 'Your alerts' : 'Setup · 30 seconds'}</Text>
        </View>
        {editing ? (
          <TextButton label="Cancel" onPress={() => navigation.goBack()} />
        ) : (
          <TextButton label="Skip" onPress={() => finish(EMPTY_PROFILE)} />
        )}
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <View style={{ gap: 6 }}>
          <Text style={styles.title} accessibilityRole="header">
            What should we watch for?
          </Text>
          <Text style={styles.subtitle}>We'll flag these on every scan. Change them any time.</Text>
        </View>

        <Group title="Health">
          {CONDITION_OPTIONS.map((o) => (
            <Chip
              key={o.id}
              label={o.label}
              selected={draft.conditions.includes(o.id)}
              onPress={() => setDraft({ ...draft, conditions: toggle(draft.conditions, o.id) })}
            />
          ))}
        </Group>
        <Group title="Allergies & intolerances">
          {ALLERGY_OPTIONS.map((o) => (
            <Chip
              key={o.id}
              label={o.label}
              selected={draft.allergies.includes(o.id)}
              onPress={() => setDraft({ ...draft, allergies: toggle(draft.allergies, o.id) })}
            />
          ))}
        </Group>
        <Group title="Food preference">
          {DIET_OPTIONS.map((o) => (
            <Chip
              key={o.id}
              label={o.label}
              selected={draft.diets.includes(o.id)}
              onPress={() => setDraft({ ...draft, diets: toggle(draft.diets, o.id) })}
            />
          ))}
        </Group>

        <View style={styles.privacy}>
          <Icon name="lock" size={18} color={colors.brand} />
          <Text style={styles.privacyText}>Stays on your phone. We never sell or share your health choices.</Text>
        </View>
        <Text style={styles.disclaimer}>
          Alerts are information from the label, not medical advice. Follow your doctor's guidance.
        </Text>
        {editing && profileSize(profile) > 0 ? (
          <TextButton label="Delete my health choices" onPress={confirmDelete} color={colors.redText} />
        ) : null}
      </ScrollView>

      <View style={styles.footer}>
        <PrimaryButton
          label={count === 0 ? 'Continue without alerts' : `Continue with ${count} alert${count === 1 ? '' : 's'}`}
          onPress={() => finish(draft)}
        />
      </View>
    </SafeAreaView>
  );
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={{ gap: 10 }}>
      <Text style={styles.groupTitle}>{title.toUpperCase()}</Text>
      <View style={styles.chips}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.ground },
  header: { height: 56, paddingLeft: 20, paddingRight: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerText: { fontSize: 13, fontWeight: '600', color: colors.caption },
  content: { paddingHorizontal: 20, paddingBottom: 24, gap: 22 },
  title: { fontSize: 28, lineHeight: 32, fontWeight: '700', color: colors.ink, letterSpacing: -0.4 },
  subtitle: { fontSize: 15, lineHeight: 22, color: colors.ink3 },
  groupTitle: { fontSize: 12, fontWeight: '700', letterSpacing: 0.7, color: colors.caption },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  privacy: {
    flexDirection: 'row',
    gap: 10,
    padding: 14,
    borderRadius: 14,
    backgroundColor: colors.brandSoft,
    alignItems: 'flex-start',
  },
  privacyText: { flex: 1, fontSize: 13, lineHeight: 19, color: colors.brand },
  disclaimer: { fontSize: 12, lineHeight: 18, color: colors.caption },
  footer: { paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12, flexDirection: 'row' },
});
