import { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '@/constants/colors';
import { api } from '@/services/api';

export default function ReportScreen() {
  const router = useRouter();
  const params = useLocalSearchParams() as { scan_id?: string };
  const scanId = params?.scan_id ?? '';
  const [scan, setScan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) {
      setError('No scan ID provided.');
      setLoading(false);
      return;
    }
    api.getScan(scanId)
      .then(setScan)
      .catch((err: any) => setError(err?.message || 'Failed to load report'))
      .finally(() => setLoading(false));
  }, [scanId]);

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading report…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <View style={styles.errorWrapper}>
          <Text style={styles.errorTitle}>Unable to load report</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => router.replace('/')}>
            <Text style={styles.retryText}>Back to Home</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Product Report</Text>
          <Text style={styles.headerSub}>Scan ID: {scan.id}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.fieldLabel}>Product Name</Text>
          <Text style={styles.fieldValue}>{scan.product_name || 'Not identified'}</Text>
          <Text style={styles.fieldLabel}>Brand</Text>
          <Text style={styles.fieldValue}>{scan.brand || 'Not identified'}</Text>
          <Text style={styles.fieldLabel}>Status</Text>
          <Text style={[styles.fieldValue, { color: COLORS.primary, fontWeight: '700' }]}>
            {scan.status}
          </Text>
          <Text style={styles.fieldLabel}>Images Captured</Text>
          <Text style={styles.fieldValue}>{scan.images?.length ?? 0}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Next Steps</Text>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/ocr-results?scan_id=${scanId}`)}
          >
            <Text style={styles.actionText}>View OCR Results</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>View ingredient explanations (Phase 3)</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Translate report (Phase 4)</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.backButton} onPress={() => router.replace('/')}>
          <Text style={styles.backText}>← Back to Home</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 12,
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
  },
  errorWrapper: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: SIZES.spacingLg,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.error,
    textAlign: 'center',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 18,
  },
  retryButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  retryText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  scrollContent: {
    paddingHorizontal: SIZES.spacing,
    paddingBottom: SIZES.spacingLg,
  },
  header: {
    alignItems: 'center',
    marginTop: SIZES.spacing,
    marginBottom: SIZES.spacingLg,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  headerSub: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    marginTop: 4,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    padding: SIZES.spacing,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    marginBottom: SIZES.spacing,
  },
  fieldLabel: {
    fontSize: 12.5,
    fontWeight: '700',
    color: COLORS.onSurfaceVariant,
    marginTop: 12,
  },
  fieldValue: {
    fontSize: 15,
    color: COLORS.onSurface,
    marginTop: 2,
  },
  section: {
    marginBottom: SIZES.spacing,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.onSurface,
    marginBottom: SIZES.spacingSm,
  },
  actionButton: {
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    color: COLORS.primaryDark,
    fontWeight: '600',
  },
  backButton: {
    alignItems: 'center',
    marginTop: 14,
  },
  backText: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
    fontWeight: '600',
  },
});
