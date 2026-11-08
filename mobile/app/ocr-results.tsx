import { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES } from '@/constants/colors';
import { api } from '@/services/api';

export default function OcrResultsScreen() {
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
      .then((data: any) => {
        setScan(data);
      })
      .catch((err: any) => setError(err?.message || 'Failed to load OCR results'))
      .finally(() => setLoading(false));
  }, [scanId]);

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <StatusBar style="auto" />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading OCR results…</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <StatusBar style="auto" />
        <View style={styles.errorWrapper}>
          <Text style={styles.errorTitle}>Unable to load OCR results</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Link href="/">
            <TouchableOpacity style={styles.retryButton}>
              <Text style={styles.retryText}>Back to Home</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </SafeAreaView>
    );
  }

  const images = scan?.images ?? [];
  const totalOcr = images.reduce((sum: number, img: any) => sum + (img.ocr_results?.length ?? 0), 0);
  const blurryImages = images.filter((img: any) => img.quality?.is_blurry);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Link href="/">
            <Text style={styles.backText}>← Back to Report</Text>
          </Link>
          <Text style={styles.headerTitle}>OCR Results</Text>
          <Text style={styles.headerSub}>Scan ID: {scanId}</Text>
        </View>

        {/* Summary */}
        <View style={styles.summaryCard}>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Images</Text>
            <Text style={styles.summaryValue}>{images.length}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Text regions found</Text>
            <Text style={styles.summaryValue}>{totalOcr}</Text>
          </View>
          <View style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>Blurry images</Text>
            <Text style={[styles.summaryValue, blurryImages.length > 0 && { color: COLORS.warning }]}>
              {blurryImages.length}
            </Text>
          </View>
        </View>

        {blurryImages.length > 0 && (
          <View style={styles.warningCard}>
            <Text style={styles.warningTitle}>⚠️ Image Quality</Text>
            <Text style={styles.warningText}>
              {blurryImages.length} image{blurryImages.length > 1 ? 's' : ''} may be too blurry for reliable OCR.
              Consider retaking close-ups of small text.
            </Text>
          </View>
        )}

        {/* OCR results per image */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Extracted Text by Image</Text>
          {images.length === 0 ? (
            <Text style={styles.emptyText}>No images found for this scan.</Text>
          ) : (
            <FlatList
              data={images}
              keyExtractor={(item: any) => item.id}
              renderItem={({ item }: { item: any }) => (
                <ImageOcrCard image={item} />
              )}
              contentContainerStyle={{ paddingBottom: SIZES.spacingLg }}
            />
          )}
        </View>

        <Link href="/">
          <TouchableOpacity style={styles.backButton}>
            <Text style={styles.backText}>← Back to Home</Text>
          </TouchableOpacity>
        </Link>
      </ScrollView>
    </SafeAreaView>
  );
}

function ImageOcrCard({ image }: { image: any }) {
  const ocrResults = image?.ocr_results ?? [];
  const quality = image?.quality ?? {};
  const isBlurry = quality?.is_blurry ?? false;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeText}>{image?.type ?? 'other'}</Text>
        </View>
        {isBlurry && (
          <View style={styles.blurBadge}>
            <Text style={styles.blurText}>⚠ Blurry</Text>
          </View>
        )}
      </View>

      <View style={styles.qualityInfo}>
        {quality.blur_score != null && (
          <Text style={styles.qualityText}>
            Blur score: {quality.blur_score.toFixed(0)}{isBlurry ? ' (low)' : ''}
          </Text>
        )}
        {quality.brightness != null && (
          <Text style={styles.qualityText}>
            Brightness: {quality.brightness.toFixed(0)}
          </Text>
        )}
        {quality.contrast != null && (
          <Text style={styles.qualityText}>
            Contrast: {quality.contrast.toFixed(0)}
          </Text>
        )}
      </View>

      <View style={styles.ocrList}>
        {ocrResults.length === 0 ? (
          <Text style={styles.noOcrText}>No text detected on this image.</Text>
        ) : (
            ocrResults.map((ocr: any) => (
              <View key={ocr.id} style={styles.ocrItem}>
                <Text style={styles.ocrText}>{ocr.text}</Text>
                {ocr.confidence != null && (
                  <Text style={styles.confidenceText}>
                    Confidence: {(ocr.confidence / 100).toFixed(0)}%
                  </Text>
                )}
              </View>
            ))
          )}
      </View>
    </View>
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
    marginTop: SIZES.spacing,
    marginBottom: SIZES.spacingLg,
  },
  backText: {
    color: COLORS.primaryDark,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  headerSub: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    marginTop: 4,
  },
  summaryCard: {
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
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
    marginHorizontal: -SIZES.spacingSm,
    paddingHorizontal: SIZES.spacingSm,
  },
  summaryLabel: {
    fontSize: 13.5,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  summaryValue: {
    fontSize: 13.5,
    color: COLORS.onSurface,
    fontWeight: '700',
  },
  warningCard: {
    backgroundColor: COLORS.warningContainer,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.warning,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: SIZES.spacing,
    paddingVertical: 10,
    marginBottom: SIZES.spacing,
  },
  warningTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.warning,
    marginBottom: 4,
  },
  warningText: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
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
  emptyText: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 20,
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
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  typeText: {
    fontSize: 11.5,
    fontWeight: '700',
    color: COLORS.primaryDark,
  },
  blurBadge: {
    backgroundColor: COLORS.warningContainer,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  blurText: {
    fontSize: 10.5,
    fontWeight: '800',
    color: COLORS.warning,
  },
  qualityInfo: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 10,
  },
  qualityText: {
    fontSize: 11.5,
    color: COLORS.onSurfaceVariant,
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  ocrList: {
    gap: 6,
  },
  noOcrText: {
    fontSize: 12.5,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
    paddingVertical: 12,
  },
  ocrItem: {
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
  },
  ocrText: {
    fontSize: 13,
    color: COLORS.onSurface,
  },
  confidenceText: {
    fontSize: 10.5,
    color: COLORS.onSurfaceVariant,
    marginTop: 2,
  },
  backButton: {
    alignItems: 'center',
    marginTop: 14,
  },
});
