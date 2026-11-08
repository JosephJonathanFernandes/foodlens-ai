export const COLORS = {
  primary: '#2E7D32',      // green accent
  primaryDark: '#1B5E20',
  primaryLight: '#E8F5E9',
  background: '#FAFAF9',   // warm neutral off-white
  surface: '#FFFFFF',
  surfaceVariant: '#F5F5F4',
  onSurface: '#1C1C1C',
  onSurfaceVariant: '#444440',
  outline: '#C7C7C5',
  outlineVariant: '#DADAD5',
  error: '#BA1A1A',
  errorContainer: '#FDECEA',
  onError: '#FFFFFF',
  onErrorContainer: '#4A0000',
  success: '#2E7D32',
  successContainer: '#E8F5E9',
  warning: '#9A5A00',
  warningContainer: '#FFF7E0',
  onWarning: '#FFFFFF',
  shadow: '#00000022',
} as const;

export const SIZES = {
  radius: 16,
  radiusSm: 10,
  radiusLg: 24,
  spacing: 16,
  spacingSm: 8,
  spacingLg: 24,
  headerHeight: 56,
} as const;

export const LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
  { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી' },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
] as const;

export const DEFAULT_LANGUAGE = 'en';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000';
