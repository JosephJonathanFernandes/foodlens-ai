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
import { Link, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { COLORS, SIZES } from '@/constants/colors';
import { api } from '@/services/api';

export default function HistoryScreen() {
  const router = useRouter();
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHistory();
      setScans(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    const confirmed = await Alert.alert(
      'Delete scan?',
      'This will permanently delete the scan and its report. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: async () => {
          setDeletingId(id);
          try {
            await api.deleteScan(id);
            setScans((prev) => prev.filter((s) => s.id !== id));
          } catch (err: any) {
            setError(err?.message || 'Failed to delete scan');
          } finally {
            setDeletingId(null);
          }
        }},
      ]
    );
  };

  const handleOpen = (scan: any) => {
    router.push(`/report?scan_id=${scan.id}`);
  };

  const handleCompare = (id: string) => {
    router.push(`/compare?scan_id=${id}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <StatusBar style="auto" />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading history…</Text>
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
          <Text style={styles.headerTitle}>Scan History</Text>
          <Text style={styles.headerSub}>
            {scans.length} scan{scans.length > 1 ? 's' : ''} saved
          </Text>
        </View>

        {error && (
          <View style={styles.errorBanner}>{error}</View>
        )}

        {scans.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>No scans yet</Text>
            <Text style={styles.emptySubtext}>
              Scan a food package to save it to your history.
            </Text>
            <Link href="/">
              <TouchableOpacity style={styles.emptyButton}>
                <Text style={styles.emptyButtonText}>Scan a label</Text>
              </TouchableOpacity>
            </Link>
          </View>
        ) : (
          <FlatList
            data={scans}
            keyExtractor={(item) => item.id}
            renderItem={({ item }: { item: any }) => (
              <HistoryItem
                item={item}
                onOpen={handleOpen}
                onDelete={handleDelete}
                onCompare={handleCompare}
                deleting={deletingId === item.id}
              />
            )}
            contentContainerStyle={{
              paddingHorizontal: SIZES.spacing,
              paddingBottom: SIZES.spacingLg,
            }}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function HistoryItem({
  item,
  onOpen,
  onDelete,
  onCompare,
  deleting,
}: {
  item: any;
  onOpen: (item: any) => void;
  onDelete: (id: string) => void;
  onCompare: (id: string) => void;
  deleting: boolean;
}) {
  return (
    <View style={styles.card}>
      <View style={styles.cardContent}>
        <View style={styles.info}>
          <Text style={styles.name}>{item.product_name || 'Unnamed product'}</Text>
          {item.brand && (
            <Text style={styles.brand}>{item.brand}</Text>
          )}
          <Text style={styles.meta}>
            {item.status} • {new Date(item.created_at).toLocaleDateString()}
          </Text>
          <Text style={styles.meta}>
            {item.images_count ?? 0} image{item.images_count ?? 0 > 1 ? 's' : ''} captured
          </Text>
        </View>
        <View style={styles.actions}>
          <TouchableOpacity style={styles.actionButton} onPress={() => onOpen(item)}>
            <Text style={styles.actionText}>Open</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => onCompare(item.id)}>
            <Text style={styles.actionText}>Compare</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => onDelete(item.id)}
            disabled={deleting}
          >
            <Text style={[styles.actionText, { color: COLORS.error }]}>
              {deleting ? 'Deleting…' : 'Delete'}
            </Text>
          </TouchableOpacity>
        </View>
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
  errorBannerText: {
    color: COLORS.error,
    fontSize: 13,
    fontWeight: '600',
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
  cardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SIZES.spacing,
  },
  info: {
    flex: 1,
    marginRight: 12,
  },
  name: {
    fontSize: 15,
    fontWeight: '800',
    color: COLORS.onSurface,
    marginBottom: 4,
  },
  brand: {
    fontSize: 13,
    color: COLORS.onSurfaceVariant,
    marginBottom: 4,
  },
  meta: {
    fontSize: 12,
    color: COLORS.onSurfaceVariant,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceVariant,
    borderRadius: SIZES.radiusSm,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  actionText: {
    fontSize: 12.5,
    fontWeight: '600',
    color: COLORS.primaryDark,
  },
  deleteButton: {
    backgroundColor: COLORS.errorContainer,
  },
});
