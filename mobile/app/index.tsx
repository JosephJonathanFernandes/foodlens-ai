import { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, FlatList, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES, LANGUAGES, DEFAULT_LANGUAGE } from '@/constants/colors';
import type { ScanImage } from '@/types';

export default function HomeScreen() {
  const router = useRouter();
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);
  const [recentScans, setRecentScans] = useState<ScanImage[]>([]);

  const handleScan = () => {
    router.push('/scan');
  };

  const handleUpload = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (permission.granted !== true) {
      Alert.alert('Camera permission', 'Camera permission is required to upload images.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: 6,
      quality: 0.8,
    });

    if (!result.canceled && result.assets) {
      const images: ScanImage[] = result.assets.map(
        (asset: ImagePicker.ImagePickerAsset) => ({
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          uri: asset.uri,
          type: 'other',
          width: asset.width,
          height: asset.height,
        })
      );
      setRecentScans((prev) => [...images, ...prev]);
      router.push('/review');
    }
  };

  const handleLanguageChange = (code: string) => {
    setLanguage(code);
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Branding */}
        <View style={styles.header}>
          <View style={styles.brandLogo}>
            <Text style={styles.brandMark}>FL</Text>
          </View>
          <Text style={styles.appName}>FoodLens AI</Text>
          <Text style={styles.tagline}>Intelligent Food Label Scanner &amp; Simplifier</Text>
        </View>

        {/* Short explanation */}
        <View style={styles.explanationCard}>
          <Text style={styles.explanationTitle}>Understand everything on your food package</Text>
          <Text style={styles.explanationText}>
            Scan the front, back, sides, and close-ups of any food label. FoodLens AI reads the
            ingredients, nutrition facts, allergens, and marketing claims — then explains them in
            simple language, translated into your preferred Indian language.
          </Text>
        </View>

        {/* Primary actions */}
        <View style={styles.actions}>
          <TouchableOpacity style={styles.primaryButton} onPress={handleScan}>
            <View style={styles.buttonIcon}>📷</View>
            <Text style={styles.buttonTitle}>Scan Food Label</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryButton} onPress={handleUpload}>
            <View style={styles.buttonIcon}>🖼️</View>
            <Text style={styles.buttonTitle}>Upload Package Image</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryButton} onPress={() => router.push('/history')}>
            <View style={styles.buttonIcon}>📜</View>
            <Text style={styles.buttonTitle}>Scan History</Text>
          </TouchableOpacity>
        </View>

        {/* Language selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Language</Text>
          <View style={styles.languageRow}>
            {LANGUAGES.map((lang) => (
              <TouchableOpacity
                key={lang.code}
                style={[styles.languageChip, language === lang.code && styles.languageChipActive]}
                onPress={() => handleLanguageChange(lang.code)}
              >
                <Text style={[styles.languageText, language === lang.code && styles.languageTextActive]}>
                  {lang.nativeName}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.languageNote}>
            Translations applied to explanations. Original ingredient names and values are preserved.
          </Text>
        </View>

        {/* Recent scans */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Scans</Text>
          </View>
          {recentScans.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No recent scans yet.</Text>
              <Text style={styles.emptySubtext}>Scan a food package to get started.</Text>
            </View>
          ) : (
            <FlatList
              data={recentScans}
              keyExtractor={(item) => item.id}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.recentList}
              renderItem={({ item }) => (
                <TouchableOpacity style={styles.recentCard} onPress={handleScan}>
                  <View style={styles.recentPlaceholder} />
                  <View style={styles.recentOverlay}>
                    <Text style={styles.recentLabel}>{item.type}</Text>
                  </View>
                </TouchableOpacity>
              )}
            />
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    paddingHorizontal: SIZES.spacing,
    paddingBottom: SIZES.spacingLg,
    gap: SIZES.spacing,
  },
  header: {
    alignItems: 'center',
    marginTop: SIZES.spacing,
    marginBottom: SIZES.spacingLg,
  },
  brandLogo: {
    width: 56,
    height: 56,
    borderRadius: SIZES.radiusLg,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SIZES.spacingSm,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
  brandMark: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '800',
  },
  appName: {
    fontSize: 30,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 4,
  },
  tagline: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
    fontWeight: '500',
  },
  explanationCard: {
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
  },
  explanationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.onSurface,
    marginBottom: SIZES.spacingSm,
  },
  explanationText: {
    fontSize: 13.5,
    color: COLORS.onSurfaceVariant,
    lineHeight: 20,
  },
  actions: {
    gap: SIZES.spacingSm,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 16,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 4,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    paddingVertical: 16,
    borderWidth: 1.5,
    borderColor: COLORS.outline,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  buttonIcon: {
    fontSize: 22,
    marginRight: 10,
  },
  buttonTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  section: {
    marginTop: SIZES.spacing,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.onSurface,
    marginBottom: SIZES.spacingSm,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SIZES.spacingSm,
  },
  languageRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
  },
  languageChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
  },
  languageChipActive: {
    backgroundColor: COLORS.primaryLight,
    borderColor: COLORS.primary,
  },
  languageText: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  languageTextActive: {
    color: COLORS.primaryDark,
  },
  languageNote: {
    fontSize: 11.5,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
    marginTop: 4,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 24,
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radius,
  },
  emptyText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.onSurface,
  },
  emptySubtext: {
    fontSize: 12.5,
    color: COLORS.onSurfaceVariant,
    marginTop: 4,
  },
  recentList: {
    gap: 10,
    paddingRight: 4,
  },
  recentCard: {
    width: 110,
    height: 110,
    borderRadius: SIZES.radius,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    position: 'relative',
    backgroundColor: COLORS.surface,
  },
  recentPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: COLORS.surfaceVariant,
  },
  recentOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(28, 28, 28, 0.65)',
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  recentLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
