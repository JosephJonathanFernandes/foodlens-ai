/**
 * API service tests
 * Run with: npx jest
 */

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

const { api } = require('../services/api');

// Reset mocks before each test
beforeEach(() => {
  mockFetch.mockClear();
});

describe('API service', () => {
  test('health endpoint calls fetch with correct URL', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'ok', service: 'foodlens-ai' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await api.health();

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('/api/health');
  });

  test('health returns parsed JSON', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    const result = await api.health();
    expect(result.status).toBe('ok');
  });

  test('translate endpoint sends correct body', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          translated_text: '[HI - demo placeholder] Hello',
          target_language: 'hi',
          source_language: 'en',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const result = await api.translate('Hello', 'hi', 'en');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].method).toBe('POST');
    const body = JSON.parse(callArgs[1].body);
    expect(body.text).toBe('Hello');
    expect(body.target_language).toBe('hi');

    expect(result.translated_text).toContain('Hello');
  });

  test('translate handles error responses', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Bad request' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    await expect(api.translate('', 'hi', 'en')).rejects.toThrow();
  });

  test('getIngredient calls correct endpoint', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          id: 'sodium_benzoate',
          name: 'Sodium Benzoate',
          ins_number: '211',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const result = await api.getIngredient('sodium_benzoate');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callUrl = mockFetch.mock.calls[0][0];
    expect(callUrl).toContain('/api/ingredients/sodium_benzoate');
    expect(result.name).toBe('Sodium Benzoate');
  });

  test('compare sends both scan IDs', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          scan_id_a: 'scan-a',
          scan_id_b: 'scan-b',
          comparison: { note: 'test' },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    );

    const result = await api.compare('scan-a', 'scan-b');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    expect(callArgs[1].method).toBe('POST');
    const body = JSON.parse(callArgs[1].body);
    expect(body.scan_id_a).toBe('scan-a');
    expect(body.scan_id_b).toBe('scan-b');
    expect(result.comparison.note).toBeDefined();
  });
});
