import { useFocusEffect } from '@react-navigation/native';
import { CameraView, useCameraPermissions, type BarcodeScanningResult } from 'expo-camera';
import { useCallback, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, Vibration, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '../components/Icon';
import { IconButton } from '../components/ui';
import { DEMO_BARCODE, DEMO_MODE } from '../config';
import type { ScreenProps } from '../navigation/types';
import { colors } from '../theme';

const BARCODE_TYPES = ['ean13', 'ean8', 'upc_a'] as const;

/**
 * The lengths the backend will accept: EAN-8, UPC-A (12) and EAN-13.
 *
 * UPC-E is deliberately absent from BARCODE_TYPES. Its 8 digits carry a check
 * digit computed from the expanded UPC-A form, not an EAN-8 checksum, so the
 * backend would reject genuine UPC-E packs as malformed. Indian retail is
 * effectively all EAN-13 (prefix 890), so nothing is lost by leaving it off
 * until we expand UPC-E to UPC-A properly.
 */
const VALID_LENGTHS = [8, 12, 13];

function isScannableBarcode(digits: string): boolean {
  return /^\d+$/.test(digits) && VALID_LENGTHS.includes(digits.length);
}

export default function ScannerScreen({ navigation }: ScreenProps<'Scanner'>) {
  const [permission, requestPermission] = useCameraPermissions();
  const [torch, setTorch] = useState(false);
  const [active, setActive] = useState(true);
  const [manual, setManual] = useState(false);
  const [code, setCode] = useState('');
  const handled = useRef(false);

  // Re-arm the scanner each time the screen comes back into view.
  useFocusEffect(
    useCallback(() => {
      handled.current = false;
      setActive(true);
      return () => {
        setActive(false);
        setTorch(false);
      };
    }, []),
  );

  const open = (barcode: string) => {
    if (handled.current) return;
    handled.current = true;
    navigation.replace('Result', { barcode });
  };

  const onScanned = ({ data }: BarcodeScanningResult) => {
    if (handled.current || !isScannableBarcode(data)) return;
    Vibration.vibrate(40);
    open(data);
  };

  const submitManual = () => {
    const digits = code.replace(/\D/g, '');
    if (isScannableBarcode(digits)) open(digits);
  };

  const topBar = (
    <View style={styles.topBar}>
      <IconButton icon="close" label="Close scanner" onPress={() => navigation.goBack()} color={colors.darkText} background={colors.dark2} />
      <Text style={styles.title}>Scan</Text>
      {permission?.granted ? (
        <IconButton
          icon="bolt"
          label={torch ? 'Turn off torch' : 'Turn on torch'}
          onPress={() => setTorch((t) => !t)}
          color={torch ? colors.dark : colors.darkText}
          background={torch ? colors.scanAccent : colors.dark2}
        />
      ) : (
        <View style={{ width: 44 }} />
      )}
    </View>
  );

  if (!permission) {
    return <View style={styles.root} />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.root}>
        {topBar}
        <View style={styles.center}>
          <Icon name="scan" size={48} color={colors.scanAccent} />
          <Text style={styles.permTitle}>Allow the camera to scan barcodes</Text>
          <Text style={styles.permText}>Photos stay on your phone. We only read the barcode number.</Text>
          <Pressable onPress={requestPermission} accessibilityRole="button" style={styles.permButton}>
            <Text style={styles.permButtonText}>Allow camera</Text>
          </Pressable>
          <Pressable onPress={() => setManual(true)} accessibilityRole="button" style={styles.linkButton}>
            <Text style={styles.linkText}>Type the barcode instead</Text>
          </Pressable>
        </View>
        {manual ? <ManualEntry code={code} setCode={setCode} onSubmit={submitManual} onClose={() => setManual(false)} /> : null}
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.root}>
      {active ? (
        <CameraView
          style={StyleSheet.absoluteFill}
          facing="back"
          enableTorch={torch}
          barcodeScannerSettings={{ barcodeTypes: [...BARCODE_TYPES] }}
          onBarcodeScanned={manual ? undefined : onScanned}
        />
      ) : null}
      <SafeAreaView style={StyleSheet.absoluteFill} pointerEvents="box-none">
        {topBar}
        <View style={styles.center} pointerEvents="none">
          <View style={styles.status}>
            <View style={styles.dot} />
            <Text style={styles.statusText}>Looking for a barcode…</Text>
          </View>
          <View style={styles.frame}>
            <View style={[styles.corner, styles.tl]} />
            <View style={[styles.corner, styles.tr]} />
            <View style={[styles.corner, styles.bl]} />
            <View style={[styles.corner, styles.br]} />
            <View style={styles.scanLine} />
          </View>
          <Text style={styles.hint}>Point at the barcode — it scans on its own</Text>
        </View>
        <View style={styles.bottom}>
          <Pressable onPress={() => setManual(true)} accessibilityRole="button" style={styles.pill}>
            <Icon name="keypad" size={18} color={colors.darkText} />
            <Text style={styles.pillText}>Type barcode</Text>
          </Pressable>
          {DEMO_MODE ? (
            <Pressable onPress={() => open(DEMO_BARCODE)} accessibilityRole="button" style={styles.pill}>
              <Text style={styles.pillText}>Try a demo product</Text>
            </Pressable>
          ) : null}
        </View>
      </SafeAreaView>
      {manual ? <ManualEntry code={code} setCode={setCode} onSubmit={submitManual} onClose={() => setManual(false)} /> : null}
    </View>
  );
}

function ManualEntry({
  code,
  setCode,
  onSubmit,
  onClose,
}: {
  code: string;
  setCode: (s: string) => void;
  onSubmit: () => void;
  onClose: () => void;
}) {
  const digits = code.replace(/\D/g, '');
  const valid = isScannableBarcode(digits);
  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.sheetWrap}>
      <View style={styles.sheet}>
        <Text style={styles.sheetTitle}>Type the barcode number</Text>
        <TextInput
          value={code}
          onChangeText={setCode}
          onSubmitEditing={onSubmit}
          keyboardType="number-pad"
          autoFocus
          maxLength={13}
          placeholder="e.g. 8901234567890"
          placeholderTextColor="#8A938D"
          accessibilityLabel="Barcode number"
          style={styles.input}
        />
        <Text style={styles.sheetHint}>
          {digits.length > 0 && !valid
            ? `${digits.length} digit${digits.length === 1 ? '' : 's'} so far — a barcode is 8, 12 or 13 digits.`
            : 'Most Indian packs have 13 digits printed under the barcode.'}
        </Text>
        <View style={styles.sheetButtons}>
          <Pressable onPress={onClose} accessibilityRole="button" style={styles.sheetCancel}>
            <Text style={styles.sheetCancelText}>Cancel</Text>
          </Pressable>
          <Pressable
            onPress={onSubmit}
            disabled={!valid}
            accessibilityRole="button"
            accessibilityState={{ disabled: !valid }}
            style={[styles.sheetGo, !valid && { opacity: 0.4 }]}
          >
            <Text style={styles.sheetGoText}>Look up</Text>
          </Pressable>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const CORNER = 40;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.dark },
  topBar: { height: 60, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { fontSize: 17, fontWeight: '600', color: colors.darkText },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 22, paddingHorizontal: 24 },
  status: { flexDirection: 'row', alignItems: 'center', gap: 8, height: 32, paddingHorizontal: 14, borderRadius: 16, backgroundColor: 'rgba(28,37,32,0.85)' },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.scanAccent },
  statusText: { fontSize: 13, color: '#C9D4CD' },
  frame: { width: 300, height: 200 },
  corner: { position: 'absolute', width: CORNER, height: CORNER, borderColor: colors.scanAccent },
  tl: { left: 0, top: 0, borderLeftWidth: 4, borderTopWidth: 4, borderTopLeftRadius: 14 },
  tr: { right: 0, top: 0, borderRightWidth: 4, borderTopWidth: 4, borderTopRightRadius: 14 },
  bl: { left: 0, bottom: 0, borderLeftWidth: 4, borderBottomWidth: 4, borderBottomLeftRadius: 14 },
  br: { right: 0, bottom: 0, borderRightWidth: 4, borderBottomWidth: 4, borderBottomRightRadius: 14 },
  scanLine: { position: 'absolute', left: 12, right: 12, top: 99, height: 2, backgroundColor: colors.scanAccent },
  hint: { fontSize: 16, fontWeight: '500', color: colors.darkText, textAlign: 'center', textShadowColor: 'rgba(0,0,0,0.6)', textShadowRadius: 6 },
  bottom: { flexDirection: 'row', justifyContent: 'center', gap: 10, paddingBottom: 28, paddingHorizontal: 20, flexWrap: 'wrap' },
  pill: { height: 44, paddingHorizontal: 16, borderRadius: 22, backgroundColor: 'rgba(28,37,32,0.9)', flexDirection: 'row', alignItems: 'center', gap: 8 },
  pillText: { fontSize: 14, fontWeight: '600', color: colors.darkText },
  permTitle: { fontSize: 20, fontWeight: '700', color: colors.darkText, textAlign: 'center' },
  permText: { fontSize: 14, lineHeight: 20, color: colors.darkMuted, textAlign: 'center' },
  permButton: { height: 52, paddingHorizontal: 28, borderRadius: 26, backgroundColor: colors.darkText, justifyContent: 'center' },
  permButtonText: { fontSize: 16, fontWeight: '700', color: colors.dark },
  linkButton: { minHeight: 44, justifyContent: 'center' },
  linkText: { fontSize: 14, fontWeight: '600', color: colors.scanAccent },
  sheetWrap: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  sheet: { backgroundColor: colors.surface, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 32, gap: 14 },
  sheetTitle: { fontSize: 17, fontWeight: '700', color: colors.ink },
  sheetHint: { fontSize: 12, lineHeight: 17, color: colors.caption },
  input: {
    height: 52,
    borderWidth: 1.5,
    borderColor: colors.field,
    borderRadius: 14,
    paddingHorizontal: 16,
    fontSize: 20,
    letterSpacing: 2,
    color: colors.ink,
  },
  sheetButtons: { flexDirection: 'row', gap: 10 },
  sheetCancel: { flex: 1, height: 50, borderRadius: 25, borderWidth: 1.5, borderColor: colors.field, alignItems: 'center', justifyContent: 'center' },
  sheetCancelText: { fontSize: 15, fontWeight: '700', color: colors.ink3 },
  sheetGo: { flex: 1, height: 50, borderRadius: 25, backgroundColor: colors.brand, alignItems: 'center', justifyContent: 'center' },
  sheetGoText: { fontSize: 15, fontWeight: '700', color: '#FFFFFF' },
});
