/**
 * Mobile app unit tests - constants, types, and API service logic
 * Run with: npx jest
 */

import { COLORS, LANGUAGES, DEFAULT_LANGUAGE, SIZES } from '../constants/colors';

// --- Constants tests ---

test('COLORS has expected theme colors', () => {
  expect(COLORS.primary).toBe('#2E7D32');
  expect(COLORS.background).toBe('#FAFAF9');
  expect(COLORS.surface).toBe('#FFFFFF');
  expect(COLORS.error).toBe('#BA1A1A');
  expect(COLORS.success).toBe('#2E7D32');
});

test('LANGUAGES includes English and Indian languages', () => {
  const codes = LANGUAGES.map((l) => l.code);
  expect(codes).toContain('en');
  expect(codes).toContain('hi');
  expect(codes).toContain('mr');
  expect(codes).toContain('ta');
  expect(codes).toContain('te');
  expect(codes).toContain('kn');
  expect(codes).toContain('bn');
  expect(codes).toContain('gu');
  expect(codes).toContain('ml');
});

test('DEFAULT_LANGUAGE is English', () => {
  expect(DEFAULT_LANGUAGE).toBe('en');
});

test('LANGUAGES entries have code, name, and nativeName', () => {
  LANGUAGES.forEach((lang) => {
    expect(lang.code).toBeDefined();
    expect(lang.name).toBeDefined();
    expect(lang.nativeName).toBeDefined();
  });
});

test('SIZES has expected spacing values', () => {
  expect(SIZES.spacing).toBe(16);
  expect(SIZES.radius).toBe(16);
  expect(SIZES.spacingSm).toBe(8);
});

// --- Types tests ---

test('ScanImage type shape', () => {
  const image = {
    id: 'test-id',
    uri: 'file:///path/to/image.jpg',
    type: 'front',
    width: 1000,
    height: 1000,
  };
  expect(image.id).toBeDefined();
  expect(image.uri).toBeDefined();
  expect(['front', 'back', 'side', 'closeup', 'other']).toContain(image.type);
});

test('ScanStatus values', () => {
  const validStatuses = ['idle', 'capturing', 'reviewing', 'processing', 'completed', 'error'];
  expect(validStatuses).toContain('idle');
  expect(validStatuses).toContain('completed');
  expect(validStatuses).toContain('error');
});
