import { useEffect, useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  FlatList,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES } from '@/constants/colors';
import { api } from '@/services/api';

export default function CompareScreen() {
  const router = useRouter();
  const params = useLocalSearchParams() as { scan_id?: string };
  const preSelectedId = params?.scan_id;
  const [scans, setScans] = useState<any[]>([]);
  const [selectedA, setSelectedA] = useState<string | null>(null);
  const [selectedB, setSelectedB] = useState<string | null>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
    if (preSelectedId) {
      setSelectedA(preSelectedId);
    }
  }, [preSelectedId]);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHistory();
      setScans(data);
      // Auto-select first two if none pre-selected
      if (!selectedA && data.length >= 1) setSelectedA(data[0].id);
      if (!selectedB && data.length >= 2) setSelectedB(data[1].id);
      if (selectedA && selectedB) runComparison();
    } catch (err: any) {
      setError(err?.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const runComparison = async () => {
    if (!selectedA || !selectedB) return;
    setComparing(true);
    setError(null);
    try {
      const data = await api.compare(selectedA, selectedB);
      setComparison(data.comparison);
    } catch (err: any) {
      setError(err?.message || 'Failed to compare products');
    } finally {
      setComparing(false);
    }
  };

  const handleSelectA = (id: string) => {
    setSelectedA(id);
    if (id === selectedB) setSelectedB(null);
    if (selectedB) runComparison();
  };

  const handleSelectB = (id: string) => {
    setSelectedB(id);
    if (id === selectedA) setSelectedA(null);
    if (selectedA) runComparison();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <StatusBar style="auto" />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading scans…</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <StatusBar style="auto" />
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Link href="/">
            <Text style={styles.backText}>← Back to Home</Text>
          </Link>
          <Text style={styles.headerTitle}>Compare Products</Text>
          <Text style={styles.headerSub}>
            Choose two scans to compare side by side
          </Text>
        </View>

        {error && (
          <View style={styles.errorBanner}>{error}</View>
        )}

        {scans.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No scans to compare</Text>
            <Text style={styles.emptySubtext}>
              Scan at least two food packages to use comparison.
            </Text>
            <Link href="/">
              <TouchableOpacity style={styles.emptyButton}>
                <Text style={styles.emptyButtonText}>Scan a label</Text>
              </TouchableOpacity>
            </Link>
          </View>
        ) : (
          <>
            {/* Scan selection */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Select Products</Text>
              <View style={styles.selectionRow}>
                <SelectionColumn
                  title="Product A"
                  scans={scans}
                  selectedId={selectedA}
                  onSelect={handleSelectA}
                  color={COLORS.primary}
                />
                <View style={styles.vsDivider}>
                  <Text style={styles.vsText}>VS</Text>
                </View>
                <SelectionColumn
                  title="Product B"
                  scans={scans}
                  selectedId={selectedB}
                  onSelect={handleSelectB}
                  color={COLORS.primaryDark}
                />
              </View>
            </View>

            {(selectedA || selectedB) && (
              <TouchableOpacity style={styles.compareButton} onPress={runComparison} disabled={comparing}>
                <Text style={styles.compareButtonText}>
                  {comparing ? 'Comparing…' : 'Compare'}
                </Text>
              </TouchableOpacity>
            )}

            {/* Comparison results */}
            {comparison && (
              <View style={styles.resultsSection}>
                <Text style={styles.resultsTitle}>Comparison Results</Text>

                <View style={styles.productHeaders}>
                  <ProductHeader
                    product={comparison.scan_id_a}
                    color={COLORS.primary}
                  />
                  <ProductHeader
                    product={comparison.scan_id_b}
                    color={COLORS.primaryDark}
                  />
                </View>

                {/* Nutrition comparison */}
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Nutrition (per 100g)</Text>
                  {comparison.nutrition ? (
                    <FlatList
                      data={Object.entries(comparison.nutrition)}
                      keyExtractor={(item) => item[0]}
                      renderItem={({ item }: { item: [string, any] }) => (
                        <NutritionCompareRow
                          nutrient={item[0]}
                          data={item[1]}
                        />
                      )}
                      contentContainerStyle={{ paddingBottom: 8 }}
                    />
                  ) : (
                    <Text style={styles.emptyText}>No nutrition data to compare.</Text>
                  )}
                </View>

                {/* Ingredients comparison */}
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Ingredients</Text>
                  <IngredientsCompare data={comparison.ingredients} />
                </View>

                {/* Allergens comparison */}
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Allergens</Text>
                  <AllergensCompare data={comparison.allergens} />
                </View>

                {/* Claims comparison */}
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Marketing Claims</Text>
                  <ClaimsCompare data={comparison.claims} />
                </View>

                {/* Trade-offs */}
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>Trade-offs</Text>
                  {comparison.trade_offs && comparison.trade_offs.length > 0 ? (
                    <FlatList
                      data={comparison.trade_offs}
                      keyExtractor={(item, index) => String(index)}
                      renderItem={({ item }: { item: string }) => (
                        <View style={styles.tradeOffRow}>
                          <Text style={styles.tradeOffBullet}>•</Text>
                          <Text style={styles.tradeOffText}>{item}</Text>
                        </View>
                      )}
                      contentContainerStyle={{ paddingBottom: 8 }}
                    />
                  ) : (
                    <Text style={styles.emptyText}>No significant trade-offs identified.</Text>
                  )}
                </View>

                <Text style={styles.noteText}>
                  {comparison.note}
                </Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function SelectionColumn({
  title,
  scans,
  selectedId,
  onSelect,
  color,
}: {
  title: string;
  scans: any[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  color: string;
}) {
  return (
    <View style={styles.selectionColumn}>
      <Text style={styles.selectionTitle}>{title}</Text>
      <FlatList
        data={scans}
        keyExtractor={(item) => item.id}
        renderItem={({ item }: { item: any }) => (
          <TouchableOpacity
            style={[
              styles.selectionItem,
              selectedId === item.id && styles.selectionItemSelected,
            ]}
            onPress={() => onSelect(item.id)}
          >
            <View style={styles.selectionItemContent}>
              <Text style={[
                styles.selectionItemName,
                selectedId === item.id && { color: color },
              ]}>
                {item.product_name || 'Unnamed product'}
              </Text>
              {item.brand && (
                <Text style={styles.selectionItemBrand}>{item.brand}</Text>
              )}
            </View>
            {selectedId === item.id && (
              <Text style={styles.selectionCheck}>✓</Text>
            )}
          </TouchableOpacity>
        )}
        contentContainerStyle={{ paddingBottom: 8 }}
      />
    </View>
  );
}

function ProductHeader({ product, color }: { product: any; color: string }) {
  return (
    <View style={styles.productColumn}>
      <Text style={styles.productName}>{product.product_name || 'Unknown'}</Text>
      <Text style={styles.productBrand}>{product.brand || ''}</Text>
    </View>
  );
}

function NutritionCompareRow({ nutrient, data }: { nutrient: string; data: any }) {
  const label = nutrient
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');

  const aVal = data.product_a?.value ?? '—';
  const bVal = data.product_b?.value ?? '—';
  const unit = data.unit || '';

  let higherText = '';
  if (data.higher === 'a') higherText = 'A higher';
  else if (data.higher === 'b') higherText = 'B higher';
  else if (data.higher === 'equal') higherText = 'Equal';

  return (
    <View style={styles.nutritionCompareRow}>
      <Text style={styles.nutritionCompareLabel}>{label}</Text>
      <View style={styles.nutritionCompareValues}>
        <View style={styles.nutritionCompareCell}>
          <Text style={styles.nutritionCompareValue}>{aVal}</Text>
          <Text style={styles.nutritionCompareUnit}>{unit}</Text>
        </View>
        <View style={styles.nutritionCompareCell}>
          <Text style={styles.nutritionCompareValue}>{bVal}</Text>
          <Text style={styles.nutritionCompareUnit}>{unit}</Text>
        </View>
      </View>
      {higherText && (
        <Text style={[styles.nutritionCompareHigher, data.higher === 'a' && styles.higherA, data.higher === 'b' && styles.higherB]}>
          {higherText}
        </Text>
      )}
    </View>
  );
}

function IngredientsCompare({ data }: { data: any }) {
  return (
    <View style={styles.compareTwoColumns}>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product A</Text>
        <Text style={styles.compareValue}>
          {data.product_a_count} ingredients
        </Text>
        <Text style={styles.compareValueSmall}>
          {data.additives_a} additive{data.additives_a !== 1 ? 's' : ''}
        </Text>
      </View>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product B</Text>
        <Text style={styles.compareValue}>
          {data.product_b_count} ingredients
        </Text>
        <Text style={styles.compareValueSmall}>
          {data.additives_b} additive{data.additives_b !== 1 ? 's' : ''}
        </Text>
      </View>
    </View>
  );
}

function AllergensCompare({ data }: { data: any }) {
  return (
    <View style={styles.compareTwoColumns}>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product A</Text>
        {data.product_a.length === 0 ? (
          <Text style={styles.compareValueSmall}>None declared</Text>
        ) : (
          <Text style={styles.compareValueSmall}>
            {data.product_a.join(', ')}
          </Text>
        )}
      </View>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product B</Text>
        {data.product_b.length === 0 ? (
          <Text style={styles.compareValueSmall}>None declared</Text>
        ) : (
          <Text style={styles.compareValueSmall}>
            {data.product_b.join(', ')}
          </Text>
        )}
      </View>
    </View>
  );
}

function ClaimsCompare({ data }: { data: any }) {
  return (
    <View style={styles.compareTwoColumns}>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product A</Text>
        {data.product_a.length === 0 ? (
          <Text style={styles.compareValueSmall}>None</Text>
        ) : (
          <Text style={styles.compareValueSmall}>
            {data.product_a.join(', ')}
          </Text>
        )}
      </View>
      <View style={styles.compareColumn}>
        <Text style={styles.compareColumnTitle}>Product B</Text>
        {data.product_b.length === 0 ? (
          <Text style={styles.compareValueSmall}>None</Text>
        ) : (
          <Text style={styles.compareValueSmall}>
            {data.product_b.join(', ')}
          </Text>
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
  scrollContent: {
    paddingHorizontal: SIZES.spacing,
    paddingBottom: SIZES.spacingLg,
  },
  header: {
    paddingHorizontal: SIZES.spacing,
    paddingTop: 8,
    marginBottom: 16,
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
    marginBottom: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: SIZES.spacingLg,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.onSurfaceVariant,
    textAlign: 'center',
    marginBottom: 20,
  },
  emptyButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    paddingHorizontal: 28,
    alignItems: 'center',
  },
  emptyButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
    marginHorizontal: SIZES.spacing,
    marginBottom: 12,
    overflow: 'hidden',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 10,
    paddingHorizontal: SIZES.spacing,
  },
  selectionRow: {
    flexDirection: 'row',
    paddingHorizontal: SIZES.spacing,
    gap: 12,
  },
  selectionColumn: {
    flex: 1,
  },
  selectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.onSurfaceVariant,
    marginBottom: 8,
  },
  selectionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    padding: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.outlineVariant,
  },
  selectionItemSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryLight,
  },
  selectionItemContent: {
    flex: 1,
  },
  selectionItemName: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.onSurface,
  },
  selectionItemBrand: {
    fontSize: 12,
    color: COLORS.onSurfaceVariant,
  },
  selectionCheck: {
    fontSize: 14,
    fontWeight: '800',
    color: COLORS.primary,
  },
  compareButton: {
    backgroundColor: COLORS.primary,
    borderRadius: SIZES.radius,
    paddingVertical: 14,
    alignItems: 'center',
    marginHorizontal: SIZES.spacing,
    marginBottom: 16,
    shadowColor: COLORS.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.18,
    shadowRadius: 8,
    elevation: 4,
  },
  compareButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  resultsSection: {
    paddingHorizontal: SIZES.spacing,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 12,
  },
  productHeaders: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  productColumn: {
    flex: 1,
    alignItems: 'center',
  },
  productName: {
    fontSize: 16,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  productBrand: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
  },
  vsDivider: {
    justifyContent: 'center',
    width: 40,
  },
  vsText: {
    fontSize: 18,
    fontWeight: '900',
    color: COLORS.onSurfaceVariant,
  },
  nutritionCompareRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.outlineVariant,
    paddingHorizontal: -4,
  },
  nutritionCompareLabel: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    fontWeight: '600',
    width: 130,
  },
  nutritionCompareValues: {
    flexDirection: 'row',
    gap: 12,
    flex: 1,
  },
  nutritionCompareCell: {
    alignItems: 'center',
    flex: 1,
  },
  nutritionCompareValue: {
    fontSize: 14,
    color: COLORS.onSurface,
    fontWeight: '700',
  },
  nutritionCompareUnit: {
    fontSize: 11,
    color: COLORS.onSurfaceVariant,
  },
  nutritionCompareHigher: {
    fontSize: 11,
    fontWeight: '700',
    width: 70,
  },
  higherA: {
    color: COLORS.primary,
  },
  higherB: {
    color: COLORS.primaryDark,
  },
  compareTwoColumns: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  compareColumn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    marginBottom: 8,
    marginHorizontal: -4,
  },
  compareColumnTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.onSurfaceVariant,
    marginBottom: 6,
  },
  compareValue: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.onSurface,
  },
  compareValueSmall: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    marginTop: 2,
  },
  tradeOffRow: {
    flexDirection: 'row',
    paddingVertical: 6,
  },
  tradeOffBullet: {
    fontSize: 14,
    color: COLORS.primaryDark,
    fontWeight: '800',
    width: 16,
  },
  tradeOffText: {
    fontSize: 13.5,
    color: COLORS.onSurfaceVariant,
    lineHeight: 20,
    flex: 1,
  },
  noteText: {
    fontSize: 12,
    color: COLORS.onSurfaceVariant,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 12,
    paddingHorizontal: SIZES.spacing,
  },
  emptyText: {
    color: COLORS.onSurfaceVariant,
    fontSize: 14,
    textAlign: 'center',
    paddingVertical: 24,
  },
});
