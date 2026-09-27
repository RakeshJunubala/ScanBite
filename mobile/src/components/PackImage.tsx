import { useState } from 'react';
import { Image, StyleSheet, Text, View, type ImageStyle, type StyleProp, type ViewStyle } from 'react-native';

import { colors } from '../theme';

/**
 * The pack photo for a product. Open Food Facts supplies these for most
 * products but not all, and a URL can still fail to load, so both cases fall
 * back to a placeholder of exactly the same size — the layout never shifts.
 *
 * `contain` rather than `cover`: these are photos of labels, and cropping one
 * hides the part a person is trying to recognise.
 */
export function PackImage({
  uri,
  style,
  caption,
  accessibilityLabel,
}: {
  uri?: string | null;
  /**
   * Box size and corner radius, applied to the photo and the placeholder alike.
   * Typed as an image style because `ImageStyle` is the narrower of the two and
   * so is safe to hand to the fallback `View` as well.
   */
  style: StyleProp<ImageStyle>;
  /** Shown in the placeholder when there is no photo. Omit for small thumbnails. */
  caption?: string;
  accessibilityLabel?: string;
}) {
  const [failed, setFailed] = useState(false);

  if (uri && !failed) {
    return (
      <Image
        source={{ uri }}
        style={[styles.box, style]}
        resizeMode="contain"
        onError={() => setFailed(true)}
        accessible={!!accessibilityLabel}
        accessibilityLabel={accessibilityLabel}
      />
    );
  }

  return (
    <View style={[styles.box, styles.empty, style as StyleProp<ViewStyle>]}>
      {caption ? <Text style={styles.captionText}>{caption}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { backgroundColor: colors.placeholder },
  empty: { alignItems: 'center', justifyContent: 'center' },
  captionText: { fontSize: 11, fontWeight: '600', color: colors.placeholderText, textAlign: 'center' },
});
