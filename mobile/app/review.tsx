import { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Dimensions, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '@/constants/colors';
import { api } from '@/services/api';
import type { ScanImage } from '@/types';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const TYPE_LABELS: Record<string, string> = {
  front: 'Front of Package',
  back: 'Back of Package',
  side: 'Side of Package',
  closeup: 'Close-up (small text)',
  other: 'Other',
};

const TYPE_EMOJIS: Record<string, string> = {
  front: '📦',
  back: '📋',
  side: '🔄',
  closeup: '🔍',
  other: '🖼️',
};

export default function ReviewScreen() {
  const router = useRouter();
  const [images, setImages] = useState<ScanImage[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);

  const params = useLocalSearchParams() as { images?: string };
  const rawImages = params?.images ? JSON.parse(params.images) : [];

  useEffect(() => {
    setImages(rawImages);
  }, [rawImages]);

  const handleRemove = (id: string) => {
    setImages((prev) => prev.filter((img) => img.id !== id));
  };

  const handleRetake = () => {
    router.replace('/scan');
  };

  const handleSubmit = async () => {
    if (images.length === 0) {
      setError('Please add at least one image before submitting.');
      return;
    }
    setSubmitting(true);
    setError(null);

    try {
      // Upload images to backend
      const files = images.map((img) => ({
        uri: img.uri,
        name: `image-${img.id}.jpg`,
        type: 'image/jpeg',
      }));
      const uploadResult = await api.uploadScan(files);
      const newScanId = uploadResult.id;
      setScanId(newScanId);

      // Process with backend pipeline
      const processResult = await api.processScan(newScanId, 'en');
      if (processResult.status === 'completed') {
        router.push(`/report?scan_id=${newScanId}`);
      } else {
        setError('Processing did not complete. Please try again.');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to submit images. Make sure the backend is running.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Review &amp; Submit</Text>
        <Text style={styles.headerSub}>
          {images.length} image{images.length > 1 ? 's' : ''} captured for this product
        </Text>
      </View>

      {error && <View style={styles.errorBanner}>{error}</View>}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Captured Images</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.imageRow}
        >
          {images.length === 0 ? (
            <Text style={styles.emptyText}>No images captured yet.</Text>
          ) : (
            images.map((img) => (
              <View key={img.id} style={styles.imageCard}>
                <ImageTile uri={img.uri} />
                <TouchableOpacity
                  style={styles.removeButton}
                  onPress={() => handleRemove(img.id)}
                  hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}
                >
                  <Text style={styles.removeIcon}>✕</Text>
                </TouchableOpacity>
                <View style={styles.imageInfo}>
                  <Text style={styles.imageType}>{TYPE_EMOJIS[img.type]} {TYPE_LABELS[img.type]}</Text>
                </View>
              </View>
            ))
          )}
        </ScrollView>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.secondaryButton} onPress={handleRetake}>
          <Text style={styles.buttonTitle}>← Retake / Add More</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.primaryButton, submitting ? styles.buttonDisabled : {}]}
          disabled={submitting || images.length === 0}
          onPress={handleSubmit}
        >
          {submitting ? (
            <Text style={styles.buttonTitle}>Processing…</Text>
          ) : (
            <Text style={styles.buttonTitle}>
              Submit {images.length} Image{images.length > 1 ? 's' : ''}
            </Text>
          )}
        </TouchableOpacity>
      </View>

      {scanId && (
        <View style={styles.successBanner}>
          <Text style={styles.successText}>
            Scan submitted (ID: {scanId}). Opening report…
          </Text>
        </View>
      )}
    </SafeAreaView>
  );
}

function ImageTile({ uri }: { uri: string }) {
  return <View style={styles.imageTile} />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    paddingHorizontal: SIZES.spacing,
    paddingTop: 8,
    marginBottom: 10,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  headerSub: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    marginTop: 2,
  },
  errorBanner: {
    paddingHorizontal: SIZES.spacing,
    paddingVertical: 10,
    backgroundColor: COLORS.errorContainer,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.error,
    borderRadius: SIZES.radiusSm,
    marginHorizontal: SIZES.spacing,
    marginBottom: 8,
  },
  section: {
    paddingHorizontal: SIZES.spacing,
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.onSurface,
    marginBottom: SIZES.spacingSm,
  },
  imageRow: {
    gap: 12,
    paddingRight: 4,
  },
  imageCard: {
    width: 150,
    height: 150,
    borderRadius: SIZES.radius,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    backgroundColor: COLORS.surface,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageTile: {
    width: '100%',
    height: '80%',
    backgroundColor: COLORS.surfaceVariant,
  },
  removeButton: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(28, 28, 28, 0.75)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeIcon: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  imageInfo: {
    padding: 8,
    alignItems: 'center',
  },
  imageType: {
    fontSize: 11.5,
    fontWeight: '600',
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
  },
  emptyText: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: SIZES.spacing,
    marginBottom: SIZES.spacingLg,
    gap: 10,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    alignItems: 'center',
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 4,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: COLORS.outline,
  },
  buttonDisabled: {
    backgroundColor: COLORS.outlineVariant,
  },
  buttonTitle: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  successBanner: {
    backgroundColor: COLORS.successContainer,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.success,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: SIZES.spacing,
    paddingVertical: 10,
    marginHorizontal: SIZES.spacing,
    marginBottom: 10,
  },
  successText: {
    color: COLORS.primaryDark,
    fontSize: 13,
    fontWeight: '600',
  },
});
