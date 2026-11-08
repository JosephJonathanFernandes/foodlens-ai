import { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Dimensions, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, useRouter } from 'expo-router';
import {
  Camera,
  CameraView,
  useCameraPermissions,
} from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES, LANGUAGES } from '@/constants/colors';
import type { ScanImage } from '@/types';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type SectionType = 'front' | 'back' | 'side' | 'closeup' | 'other';

const SECTION_LABELS: Record<SectionType, string> = {
  front: 'Front of Package',
  back: 'Back of Package',
  side: 'Side of Package',
  closeup: 'Close-up (small text)',
  other: 'Other',
};

const SECTION_EMOJIS: Record<SectionType, string> = {
  front: '📦',
  back: '📋',
  side: '🔄',
  closeup: '🔍',
  other: '🖼️',
};

export default function ScanScreen() {
  const router = useRouter();
  const [cameraPermission, cameraPermissionGranted] = useCameraPermissions();
  const [section, setSection] = useState<SectionType>('front');
  const [images, setImages] = useState<ScanImage[]>([]);
  const [isCapturePending, setIsCapturePending] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cameraRef = useRef<any>(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        setError('Camera permission is required to capture package images.');
      }
    })();
  }, []);

  if (!cameraPermissionGranted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.permissionWrapper}>
          <View style={styles.permissionIcon}>📷</View>
          <Text style={styles.permissionTitle}>Camera Permission Needed</Text>
          <Text style={styles.permissionText}>
            FoodLens AI needs camera access to capture images of your food package.
          </Text>
          <TouchableOpacity
            style={styles.grantButton}
            onPress={async () => {
              const { status } = await Camera.requestCameraPermissionsAsync();
              if (status === 'granted') {
                setError(null);
              } else {
                setError('Camera permission was not granted.');
              }
            }}
          >
            <Text style={styles.grantText}>Grant Camera Access</Text>
          </TouchableOpacity>
          <Text style={styles.permissionNote}>
            You can also upload existing images from your gallery.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const handleCapture = async () => {
    if (isCapturePending || !cameraRef.current) return;
    setIsCapturePending(true);
    setError(null);

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.85,
        base64: false,
        processingMode: 'postProcess',
      });

      const newImage: ScanImage = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        uri: photo.uri,
        type: section,
        width: photo.width,
        height: photo.height,
      };

      setImages((prev) => [...prev, newImage]);
      setShowReview(true);
    } catch (err) {
      setError('Failed to capture image. Please try again.');
      console.error(err);
    } finally {
      setIsCapturePending(false);
    }
  };

  const handleRetake = (id: string) => {
    setImages((prev) => prev.filter((img) => img.id !== id));
  };

  const handleSectionChange = (next: SectionType) => {
    setSection(next);
  };

  const handlePickFromGallery = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (permission.granted !== true) {
      setError('Gallery access permission is required.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: 6,
      quality: 0.8,
    });

    if (!result.canceled && result.assets) {
      const added: ScanImage[] = result.assets.map(
        (asset: ImagePicker.ImagePickerAsset) => ({
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          uri: asset.uri,
          type: section,
          width: asset.width,
          height: asset.height,
        })
      );
      setImages((prev) => [...prev, ...added]);
      setShowReview(true);
    }
  };

  const handleSubmit = () => {
    if (images.length === 0) {
      setError('Please capture or upload at least one image before submitting.');
      return;
    }
    router.push({
      pathname: '/review',
      params: { images: JSON.stringify(images) },
    });
  };

  const isSectionCaptured = images.some((img) => img.type === section);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <StatusBar style="auto" />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Scan Package</Text>
        <Text style={styles.headerSub}>Capture front, back, sides &amp; close-ups</Text>
      </View>

      {/* Section selector */}
      <View style={styles.sectionBar}>
        {Object.entries(SECTION_LABELS).map(([key, label]) => {
          const s = key as SectionType;
          const captured = images.some((img) => img.type === s);
          const active = section === s;
          return (
            <TouchableOpacity
              key={key}
              style={[
                styles.sectionChip,
                active && styles.sectionChipActive,
                captured && styles.sectionChipCaptured,
              ]}
              onPress={() => handleSectionChange(s)}
            >
              <Text style={styles.sectionEmoji}>{SECTION_EMOJIS[s]}</Text>
              <Text style={[styles.sectionText, active && styles.sectionTextActive]}>
                {label}
              </Text>
              {captured && (
                <View style={styles.sectionDone}>
                  <Text style={styles.sectionDoneText}>✓</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {error && <View style={styles.errorBanner}>{error}</View>}

      {/* Camera preview */}
      <View style={styles.cameraContainer}>
        <CameraView
          ref={cameraRef}
          style={StyleSheet.absoluteFill}
          facing="back"
        />
        <View style={styles.cameraOverlay}>
          <View style={styles.frame}>
            <View style={[styles.corner, styles.cornerTopLeft]} />
            <View style={[styles.corner, styles.cornerTopRight]} />
            <View style={[styles.corner, styles.cornerBottomLeft]} />
            <View style={[styles.corner, styles.cornerBottomRight]} />
          </View>
          <Text style={styles.frameHint}>
            Frame the {SECTION_LABELS[section].toLowerCase()} within the guides
          </Text>
        </View>

        {/* Capture controls */}
        <View style={styles.captureBar}>
          <TouchableOpacity
            style={[styles.galleryButton, error ? styles.buttonDisabled : {}]}
            disabled={!!error}
            onPress={handlePickFromGallery}
          >
            <Text style={styles.galleryIcon}>🖼️</Text>
            <Text style={styles.galleryText}>Gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.shutter, isCapturePending ? styles.shutterPending : {}]}
            disabled={isCapturePending}
            onPress={handleCapture}
          />
        </View>
      </View>

      {/* Captured images review strip */}
      {showReview && images.length > 0 && (
        <View style={styles.reviewStripContainer}>
          <Text style={styles.reviewStripTitle}>Captured images</Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.reviewStrip}
          >
            {images.map((img) => (
              <View key={img.id} style={styles.reviewCard}>
                <ImagePreview uri={img.uri} />
                <TouchableOpacity
                  style={styles.removeButton}
                  onPress={() => handleRetake(img.id)}
                  hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                >
                  <Text style={styles.removeIcon}>✕</Text>
                </TouchableOpacity>
                <View style={styles.reviewType}>
                  <Text style={styles.reviewTypeText}>{SECTION_LABELS[img.type]}</Text>
                </View>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Submit button */}
      <TouchableOpacity
        style={[styles.submitButton, images.length === 0 ? styles.submitDisabled : {}]}
        disabled={images.length === 0}
        onPress={handleSubmit}
      >
        <Text style={styles.submitText}>
          Submit {images.length} Image{images.length > 1 ? 's' : ''} for Processing
        </Text>
      </TouchableOpacity>

      <Link href="/">
        <Text style={styles.backHome}>← Back to Home</Text>
      </Link>
    </SafeAreaView>
  );
}

function ImagePreview({ uri }: { uri: string }) {
  return <View style={styles.reviewImage} />;
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
  sectionBar: {
    paddingHorizontal: SIZES.spacing,
    marginBottom: 10,
  },
  sectionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    backgroundColor: COLORS.surface,
    marginRight: 8,
  },
  sectionChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  sectionChipCaptured: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryLight,
  },
  sectionEmoji: {
    fontSize: 16,
    marginRight: 6,
  },
  sectionText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.onSurfaceVariant,
  },
  sectionTextActive: {
    color: '#FFFFFF',
  },
  sectionDone: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: COLORS.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 6,
  },
  sectionDoneText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
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
  cameraContainer: {
    flex: 1,
    backgroundColor: '#000000',
    overflow: 'hidden',
  },
  cameraOverlay: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  frame: {
    width: SCREEN_WIDTH * 0.85,
    height: SCREEN_WIDTH * 0.85,
    borderRadius: SIZES.radiusLg,
    borderWidth: 2,
    borderColor: 'rgba(46, 125, 50, 0.9)',
    overflow: 'hidden',
  },
  corner: {
    position: 'absolute',
    width: 28,
    height: 28,
    borderWidth: 3,
    borderColor: '#2E7D32',
  },
  cornerTopLeft: {
    top: 0,
    left: 0,
    borderRightWidth: 0,
    borderBottomWidth: 0,
  },
  cornerTopRight: {
    top: 0,
    right: 0,
    borderLeftWidth: 0,
    borderBottomWidth: 0,
  },
  cornerBottomLeft: {
    bottom: 0,
    left: 0,
    borderRightWidth: 0,
    borderTopWidth: 0,
  },
  cornerBottomRight: {
    bottom: 0,
    right: 0,
    borderLeftWidth: 0,
    borderTopWidth: 0,
  },
  frameHint: {
    position: 'absolute',
    bottom: 16,
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    textShadowColor: '#000000',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  captureBar: {
    position: 'absolute',
    bottom: 30,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  galleryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(28, 28, 28, 0.55)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  galleryIcon: {
    fontSize: 18,
    marginRight: 6,
  },
  galleryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  shutter: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#FFFFFF',
    borderWidth: 3,
    borderColor: 'rgba(28, 28, 28, 0.25)',
  },
  shutterPending: {
    backgroundColor: '#DDDDDD',
  },
  reviewStripContainer: {
    paddingHorizontal: SIZES.spacing,
    paddingTop: 8,
  },
  reviewStripTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.onSurface,
    marginBottom: 8,
  },
  reviewStrip: {
    gap: 10,
    paddingRight: 4,
  },
  reviewCard: {
    width: 100,
    height: 100,
    borderRadius: SIZES.radius,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    backgroundColor: COLORS.surface,
    position: 'relative',
  },
  reviewImage: {
    width: '100%',
    height: '100%',
    backgroundColor: COLORS.surfaceVariant,
  },
  removeButton: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: 'rgba(28, 28, 28, 0.7)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeIcon: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  reviewType: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(28, 28, 28, 0.65)',
    paddingHorizontal: 4,
    paddingVertical: 3,
  },
  reviewTypeText: {
    fontSize: 9.5,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 16,
    alignItems: 'center',
    marginHorizontal: SIZES.spacing,
    marginTop: 12,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 4,
  },
  submitDisabled: {
    backgroundColor: COLORS.outlineVariant,
  },
  submitText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  backHome: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 14,
    marginBottom: 12,
  },
  permissionWrapper: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SIZES.spacingLg,
    backgroundColor: COLORS.background,
  },
  permissionIcon: {
    fontSize: 56,
    marginBottom: 16,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.onSurface,
    textAlign: 'center',
    marginBottom: 8,
  },
  permissionText: {
    fontSize: 14.5,
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 22,
  },
  grantButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    paddingHorizontal: 28,
    alignItems: 'center',
  },
  grantText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  permissionNote: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
    marginTop: 16,
    fontStyle: 'italic',
  },
});
