import { useEffect, useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  SectionList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES, LANGUAGES, DEFAULT_LANGUAGE } from '@/constants/colors';
import { api } from '@/services/api';

type Tab = 'overview' | 'ingredients' | 'nutrition' | 'allergens' | 'claims' | 'complete';

const TAB_LABELS: Record<Tab, string> = {
  overview: 'Overview',
  ingredients: 'Ingredients',
  nutrition: 'Nutrition',
  allergens: 'Allergens',
  claims: 'Claims',
  complete: 'Complete label',
};

export default function ReportScreen() {
  const router = useRouter();
  const params = useLocalSearchParams() as { scan_id?: string };
  const scanId = params?.scan_id ?? '';
  const [language, setLanguage] = useState(DEFAULT_LANGUAGE);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedIngredients, setExpandedIngredients] = useState<Set<string>>(new Set());
  const [explainingEverything, setExplainingEverything] = useState(false);
  const [explainEverythingText, setExplainEverythingText] = useState<string>('');

  useEffect(() => {
    if (!scanId) {
      setError('No scan ID provided.');
      setLoading(false);
      return;
    }
    loadReport();
  }, [scanId, language]);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFullReport(scanId);
      setReport(data);
      // Translate if not English
      if (language !== 'en') {
        const translated = await api.translateReport(scanId, language);
        setReport(translated);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = (code: string) => {
    setLanguage(code);
    if (code !== 'en' && report) {
      api.translateReport(scanId, code)
        .then(setReport)
        .catch((err: any) => console.error('Translate failed:', err));
    } else if (code === 'en') {
      loadReport();
    }
  };

  const toggleIngredient = (id: string) => {
    setExpandedIngredients((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleExplainEverything = async () => {
    setExplainingEverything(true);
    setExplainEverythingText('');
    try {
      // The backend explain-everything is built into the report service;
      // we call translateReport to get the localized summary, then append explain-everything text.
      // For now, generate from the report data locally.
      const parts: string[] = [];
      parts.push(`Product: ${report?.product_name || 'Unknown product'}`);
      parts.push(`Brand: ${report?.brand || 'Not listed'}`);
      if (report?.summary) parts.push(`\nSummary: ${report.summary}`);
      const ings = report?.ingredients ?? [];
      if (ings.length) {
        parts.push(`\nIngredients (${ings.length}):`);
        ings.forEach((ing: any) => {
          const name = ing.ingredient || ing.raw_name || 'Unknown';
          const simple = ing.simple_name || name;
          parts.push(`  - ${name} (${simple})`);
        });
      }
      const alls = report?.allergens ?? {};
      if (alls && Object.keys(alls).length) {
        parts.push(`\nAllergens detected: ${Object.keys(alls).join(', ')}`);
      }
      parts.push('\nThis explanation is based on label text extracted via OCR. No health score is assigned.');
      setExplainEverythingText(parts.join('\n'));
    } catch (err: any) {
      setExplainEverythingText('Unable to generate explanation.');
    } finally {
      setExplainingEverything(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <StatusBar style="auto" />
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
        <StatusBar style="auto" />
        <View style={styles.errorWrapper}>
          <Text style={styles.errorTitle}>Unable to load report</Text>
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

  const images = report?.images ?? [];
  const ingredients = report?.ingredients ?? [];
  const nutrition = report?.nutrition ?? [];
  const allergens = report?.allergens ?? [];
  const claims = report?.claims ?? [];

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <StatusBar style="auto" />
      <View style={styles.header}>
        <Link href="/">
          <Text style={styles.backText}>← Back to Home</Text>
        </Link>
        <View style={styles.titleWrapper}>
          <Text style={styles.headerTitle}>Product Report</Text>
          <Text style={styles.headerSub}>Scan ID: {scanId}</Text>
        </View>
      </View>

      {/* Language selector */}
      <View style={styles.languageBar}>
        <Text style={styles.languageLabel}>Language:</Text>
        {LANGUAGES.map((lang) => (
          <TouchableOpacity
            key={lang.code}
            style={[
              styles.languageChip,
              language === lang.code && styles.languageChipActive,
            ]}
            onPress={() => handleLanguageChange(lang.code)}
          >
            <Text style={[styles.languageText, language === lang.code && styles.languageTextActive]}>
              {lang.nativeName}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Product overview card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Product Overview</Text>
        <View style={styles.fieldRow}>
          <Text style={styles.fieldLabel}>Product Name</Text>
          <Text style={styles.fieldValue}>{report?.product_name || 'Not identified'}</Text>
        </View>
        <View style={styles.fieldRow}>
          <Text style={styles.fieldLabel}>Brand</Text>
          <Text style={styles.fieldValue}>{report?.brand || 'Not identified'}</Text>
        </View>
        <View style={styles.fieldRow}>
          <Text style={styles.fieldLabel}>Status</Text>
          <Text style={[styles.fieldValue, { color: COLORS.primary, fontWeight: '700' }]}>
            {report?.status}
          </Text>
        </View>
        <View style={styles.fieldRow}>
          <Text style={styles.fieldLabel}>Images Captured</Text>
          <Text style={styles.fieldValue}>{images.length}</Text>
        </View>
        <View style={styles.fieldRow}>
          <Text style={styles.fieldLabel}>Language</Text>
          <Text style={styles.fieldValue}>
            {LANGUAGES.find((l) => l.code === language)?.nativeName || language}
          </Text>
        </View>
        {report?.summary && (
          <View style={styles.fieldRow}>
            <Text style={styles.fieldLabel}>Summary</Text>
            <Text style={styles.fieldValue}>{report.summary}</Text>
          </View>
        )}
      </View>

      {/* Warnings */}
      {report?.warnings?.length && (
        <View style={styles.warningCard}>
          {report.warnings.map((w: string, i: number) => (
            <Text key={i} style={styles.warningText}>
              • {w}
            </Text>
          ))}
        </View>
      )}

      {/* Tabs */}
      <View style={styles.tabBar}>
        {Object.entries(TAB_LABELS).map(([key, label]) => {
          const t = key as Tab;
          return (
            <TouchableOpacity
              key={key}
              style={[
                styles.tab,
                activeTab === t && styles.tabActive,
              ]}
              onPress={() => setActiveTab(t)}
            >
              <Text style={[styles.tabText, activeTab === t && styles.tabTextActive]}>
                {label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Tab content */}
      <View style={styles.tabContent}>
        {activeTab === 'overview' && (
          <>
            <Text style={styles.sectionTitle}>Product Summary</Text>
            <Text style={styles.bodyText}>
              {report?.summary || 'No summary available.'}
            </Text>
            {explainingEverything && (
              <View style={styles.explainCard}>
                <Text style={styles.explainTitle}>Explain Everything</Text>
                <Text style={styles.explainText}>{explainEverythingText}</Text>
              </View>
            )}
            {!explainingEverything && (
              <TouchableOpacity style={styles.explainButton} onPress={handleExplainEverything}>
                <Text style={styles.explainButtonText}>
                  {explainingEverything ? 'Generating…' : 'Explain everything'}
                </Text>
              </TouchableOpacity>
            )}
          </>
        )}

        {activeTab === 'ingredients' && (
          <>
            <Text style={styles.sectionTitle}>
              Ingredients ({ingredients.length})
            </Text>
            {ingredients.length === 0 ? (
              <Text style={styles.emptyText}>No ingredients extracted from this label.</Text>
            ) : (
              <FlatList
                data={ingredients}
                keyExtractor={(item, index) => String(index)}
                renderItem={({ item }: { item: any }) => (
                  <IngredientCard item={item} expanded={expandedIngredients.has(String(item.raw_name))} onToggle={toggleIngredient} />
                )}
                contentContainerStyle={{ paddingBottom: SIZES.spacingLg }}
              />
            )}
          </>
        )}

        {activeTab === 'nutrition' && (
          <>
            <Text style={styles.sectionTitle}>Nutrition Breakdown</Text>
            {nutrition.length === 0 ? (
              <Text style={styles.emptyText}>No nutrition values extracted from this label.</Text>
            ) : (
              <FlatList
                data={nutrition}
                keyExtractor={(item) => item.nutrient}
                renderItem={({ item }: { item: any }) => (
                  <View style={styles.nutritionRow}>
                    <Text style={styles.nutritionLabel}>{item.nutrient}</Text>
                    <View style={styles.nutritionValueWrapper}>
                      <Text style={styles.nutritionValue}>{item.value}</Text>
                      <Text style={styles.nutritionUnit}>{item.unit || ''}</Text>
                      <Text style={styles.nutritionBasis}>[{item.basis || ''}]</Text>
                    </View>
                  </View>
                )}
                contentContainerStyle={{ paddingBottom: SIZES.spacingLg }}
              />
            )}
          </>
        )}

        {activeTab === 'allergens' && (
          <>
            <Text style={styles.sectionTitle}>Allergen Information</Text>
            {allergens.length === 0 ? (
              <Text style={styles.emptyText}>
                No allergens detected in extracted text. This does not guarantee the product is allergen-free.
              </Text>
            ) : (
              <FlatList
                data={allergens}
                keyExtractor={(item) => item.allergen}
                renderItem={({ item }: { item: any }) => (
                  <View style={styles.allergenRow}>
                    <Text style={styles.allergenName}>{item.allergen}</Text>
                    <Text style={[
                      styles.allergenType,
                      item.warning_type === 'declared' && styles.allergenDeclared,
                      item.warning_type === 'may_contain' && styles.allergenMayContain,
                      item.warning_type === 'cross_contamination' && styles.allergenCross,
                    ]}>
                      {item.warning_type}
                    </Text>
                  </View>
                )}
                contentContainerStyle={{ paddingBottom: SIZES.spacingLg }}
              />
            )}
            <Text style={styles.noteText}>
              This does not guarantee the product is allergen-free. Always check the full packaging.
            </Text>
          </>
        )}

        {activeTab === 'claims' && (
          <>
            <Text style={styles.sectionTitle}>Marketing Claims Analysis</Text>
            {claims.length === 0 ? (
              <Text style={styles.emptyText}>No marketing claims detected on this label.</Text>
            ) : (
              <FlatList
                data={claims}
                keyExtractor={(item) => item.claim}
                renderItem={({ item }: { item: any }) => (
                  <View style={styles.claimCard}>
                    <Text style={styles.claimName}>{item.claim.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</Text>
                    <Text style={styles.claimMeaning}>{item.meaning}</Text>
                    <Text style={styles.claimCaveat}>{item.caveat}</Text>
                    <Text style={styles.claimVerified}>
                      Independently verified: {item.verified ? 'Yes' : 'No'}
                    </Text>
                  </View>
                )}
                contentContainerStyle={{ paddingBottom: SIZES.spacingLg }}
              />
            )}
          </>
        )}

        {activeTab === 'complete' && (
          <>
            <Text style={styles.sectionTitle}>Complete Label Data</Text>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Raw OCR Text</Text>
              <Text style={styles.bodyText}>
                {report?.images?.length ? `OCR performed on ${report.images.length} image(s). Per-image confidence available in OCR Results.` : 'No OCR data.'}
              </Text>
            </View>
            <View style={styles.fieldRow}>
              <Text style={styles.fieldLabel}>Total Ingredients</Text>
              <Text style={styles.fieldValue}>{ingredients.length}</Text>
            </View>
            <View style={styles.fieldRow}>
              <Text style={styles.fieldLabel}>Nutrition Values</Text>
              <Text style={styles.fieldValue}>{nutrition.length}</Text>
            </View>
            <View style={styles.fieldRow}>
              <Text style={styles.fieldLabel}>Allergens</Text>
              <Text style={styles.fieldValue}>{allergens.length}</Text>
            </View>
            <View style={styles.fieldRow}>
              <Text style={styles.fieldLabel}>Marketing Claims</Text>
              <Text style={styles.fieldValue}>{claims.length}</Text>
            </View>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

function IngredientCard({ item, expanded, onToggle }: { item: any; expanded: boolean; onToggle: (id: string) => void }) {
  const id = String(item.raw_name);
  const isAdditive = item.ingredient?.is_additive ?? false;
  const matchConfidence = item.confidence ?? 0;

  return (
    <View style={[styles.ingredientCard, isAdditive && styles.ingredientCardAdditive]}>
      <TouchableOpacity style={styles.ingredientHeader} onPress={() => onToggle(id)}>
        <View style={styles.ingredientHeaderRow}>
          <Text style={styles.ingredientName}>{item.ingredient || item.raw_name || 'Unknown'}</Text>
          {item.ingredient?.simple_name && (
            <Text style={styles.ingredientSimpleName}>({item.ingredient.simple_name})</Text>
          )}
        </View>
        <View style={styles.ingredientMeta}>
          <Text style={[
            styles.ingredientChip,
            isAdditive && styles.ingredientChipAdditive,
          ]}>
            {isAdditive ? 'ADDITIVE' : 'INGREDIENT'}
          </Text>
          {item.ingredient?.ins_number && (
            <Text style={styles.ingredientChip}>INS {item.ingredient.ins_number}</Text>
          )}
          {item.ingredient?.e_number && (
            <Text style={styles.ingredientChip}>{item.ingredient.e_number}</Text>
          )}
          <Text style={styles.ingredientConfidence}>Match: {matchConfidence}%</Text>
        </View>
        <Text style={styles.expandIcon}>{expanded ? '▲' : '▼'}</Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.ingredientBody}>
          {item.ingredient?.what_it_does && (
            <View style={styles.explainField}>
              <Text style={styles.explainFieldLabel}>What it does:</Text>
              <Text style={styles.explainFieldText}>{item.ingredient.what_it_does}</Text>
            </View>
          )}
          {item.ingredient?.why_manufacturers_use_it && (
            <View style={styles.explainField}>
              <Text style={styles.explainFieldLabel}>Why used:</Text>
              <Text style={styles.explainFieldText}>{item.ingredient.why_manufacturers_use_it}</Text>
            </View>
          )}
          {item.ingredient?.considerations && (
            <View style={styles.explainField}>
              <Text style={styles.explainFieldLabel}>Considerations:</Text>
              <Text style={styles.explainFieldText}>{item.ingredient.considerations}</Text>
            </View>
          )}
          {item.ingredient?.regulatory_info && (
            <View style={styles.explainField}>
              <Text style={styles.explainFieldLabel}>Regulatory info:</Text>
              <Text style={styles.explainFieldText}>{item.ingredient.regulatory_info}</Text>
            </View>
          )}
          {item.ingredient?.uncertain && (
            <View style={styles.explainFieldUncertain}>
              <Text style={styles.explainFieldText}>
                ⚠ No reliable knowledge-base information. Based on label text only.
              </Text>
            </View>
          )}
        </View>
      )}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SIZES.spacing,
    paddingTop: 8,
    marginBottom: 10,
  },
  backText: {
    color: COLORS.primaryDark,
    fontSize: 14,
    fontWeight: '600',
  },
  titleWrapper: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  headerSub: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    marginTop: 2,
  },
  languageBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SIZES.spacing,
    marginBottom: 10,
    gap: 8,
  },
  languageLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.onSurfaceVariant,
    marginRight: 6,
  },
  languageChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
  },
  languageChipActive: {
    backgroundColor: COLORS.primaryLight,
    borderColor: COLORS.primary,
  },
  languageText: {
    fontSize: 12.5,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  languageTextActive: {
    color: COLORS.primaryDark,
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
    marginHorizontal: SIZES.spacing,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 10,
  },
  fieldRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
    paddingHorizontal: -4,
  },
  fieldLabel: {
    fontSize: 13.5,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  fieldValue: {
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
    marginHorizontal: SIZES.spacing,
    marginBottom: 10,
  },
  warningText: {
    fontSize: 13,
    color: COLORS.warning,
    lineHeight: 18,
  },
  tabBar: {
    flexDirection: 'row',
    marginHorizontal: SIZES.spacing,
    marginBottom: 2,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.outlineVariant,
  },
  tabActive: {
    borderBottomColor: COLORS.primary,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '600',
    color: COLORS.onSurfaceVariant,
  },
  tabTextActive: {
    color: COLORS.primary,
    fontWeight: '800',
  },
  tabContent: {
    paddingHorizontal: SIZES.spacing,
    paddingBottom: SIZES.spacingLg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 8,
  },
  bodyText: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    lineHeight: 22,
    marginBottom: 12,
  },
  emptyText: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 24,
  },
  explainCard: {
    backgroundColor: COLORS.primaryLight,
    borderRadius: SIZES.radius,
    padding: SIZES.spacing,
    marginBottom: 12,
    marginHorizontal: SIZES.spacing,
  },
  explainTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 6,
  },
  explainText: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    lineHeight: 22,
  },
  explainButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    alignItems: 'center',
    marginHorizontal: SIZES.spacing,
    marginBottom: 12,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 4,
  },
  explainButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  nutritionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
    paddingHorizontal: -4,
  },
  nutritionLabel: {
    fontSize: 13.5,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  nutritionValueWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  nutritionValue: {
    fontSize: 13.5,
    color: COLORS.onSurface,
    fontWeight: '700',
  },
  nutritionUnit: {
    fontSize: 12,
    color: COLORS.onSurfaceVariant,
  },
  nutritionBasis: {
    fontSize: 10.5,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
  },
  allergenRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
    paddingHorizontal: -4,
  },
  allergenName: {
    fontSize: 14,
    color: COLORS.onSurface,
    fontWeight: '700',
  },
  allergenType: {
    fontSize: 11,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 12,
  },
  allergenDeclared: {
    backgroundColor: COLORS.errorContainer,
    color: COLORS.error,
  },
  allergenMayContain: {
    backgroundColor: COLORS.warningContainer,
    color: COLORS.warning,
  },
  allergenCross: {
    backgroundColor: COLORS.errorContainer,
    color: COLORS.error,
  },
  claimCard: {
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    padding: SIZES.spacingSm,
    marginBottom: 8,
  },
  claimName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 4,
  },
  claimMeaning: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    marginBottom: 4,
  },
  claimCaveat: {
    fontSize: 12.5,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  claimVerified: {
    fontSize: 11,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
  },
  noteText: {
    fontSize: 12,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
    marginTop: 8,
  },
  ingredientCard: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radiusSm,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    marginBottom: 8,
    marginHorizontal: -4,
    overflow: 'hidden',
  },
  ingredientCardAdditive: {
    borderLeftWidth: 4,
    borderLeftColor: COLORS.warning,
  },
  ingredientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SIZES.spacingSm,
  },
  ingredientHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  ingredientName: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  ingredientSimpleName: {
    fontSize: 12.5,
    color: COLORS.primaryDark,
    fontWeight: '600',
  },
  ingredientMeta: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 4,
  },
  ingredientChip: {
    fontSize: 9.5,
    fontWeight: '800',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    backgroundColor: COLORS.surfaceVariant,
    color: COLORS.onSurfaceVariant,
  },
  ingredientChipAdditive: {
    backgroundColor: COLORS.warningContainer,
    color: COLORS.warning,
  },
  ingredientConfidence: {
    fontSize: 9.5,
    color: COLORS.onSurfaceVariant,
  },
  expandIcon: {
    fontSize: 14,
    color: COLORS.primaryDark,
    fontWeight: '700',
  },
  ingredientBody: {
    padding: SIZES.spacingSm,
    backgroundColor: COLORS.surfaceVariant,
  },
  explainField: {
    marginBottom: 8,
  },
  explainFieldLabel: {
    fontSize: 11.5,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 2,
  },
  explainFieldText: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    lineHeight: 18,
  },
  explainFieldUncertain: {
    marginTop: 8,
    padding: 8,
    backgroundColor: COLORS.warningContainer,
    borderRadius: SIZES.radiusSm,
  },
});
