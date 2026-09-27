// API mode with a fake network.
import assert from 'node:assert/strict';
import { test } from 'node:test';

process.env.EXPO_PUBLIC_API_URL = 'http://api.test/';

type Handler = (url: string) => Promise<Response>;
function mockFetch(handler: Handler): string[] {
  const calls: string[] = [];
  globalThis.fetch = (async (input: string | URL | Request) => {
    const url = String(input);
    calls.push(url);
    return handler(url);
  }) as typeof fetch;
  return calls;
}
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

test('API mode: calls the server, maps 404 to NotFoundError, falls back to demo data when offline', async () => {
  const client = await import('./client');
  const config = await import('../config');
  assert.equal(config.DEMO_MODE, false);
  assert.equal(config.API_URL, 'http://api.test'); // trailing slash trimmed

  const fake = { product: { name: 'From server' }, score: { verdict: 'good' } };
  let calls = mockFetch(async () => json(fake));
  const found = await client.getProduct('8900000000002');
  assert.equal(found.product.name, 'From server');
  assert.deepEqual(calls, ['http://api.test/v1/products/8900000000002']);

  mockFetch(async () => json({ detail: 'not_found' }, 404));
  await assert.rejects(client.getProduct('8900000000019'), client.NotFoundError);

  mockFetch(async () => {
    throw new TypeError('Network request failed');
  });
  const demo = await client.getProduct(config.DEMO_BARCODE);
  assert.equal(demo.product.status, 'sample');
  await assert.rejects(client.getProduct('8900000000019'), client.OfflineError);

  mockFetch(async () => json({ detail: 'boom' }, 500));
  await assert.rejects(client.getProduct('8900000000019'), client.OfflineError);

  calls = mockFetch(async () => json([]));
  await client.search('dal & rice');
  assert.deepEqual(calls, ['http://api.test/v1/search?q=dal%20%26%20rice']);
});

test('a 503 is not a missing product, and a 400 is not a network failure', async () => {
  const client = await import('./client');

  // Our server is up but could not reach Open Food Facts. We do not know
  // whether the product exists, so this must not read as "not in our database".
  mockFetch(async () => json({ detail: 'source_unavailable' }, 503));
  await assert.rejects(client.getProduct('8901719134845'), client.SourceUnavailableError);

  mockFetch(async () => json({ detail: 'source_unavailable' }, 503));
  await assert.rejects(client.getProduct('8901719134845'), (err: unknown) => {
    assert.ok(!(err instanceof client.NotFoundError), '503 must not become NotFoundError');
    assert.ok(!(err instanceof client.OfflineError), '503 must not become OfflineError');
    return true;
  });

  // A rejected barcode is bad input, not a connection problem.
  mockFetch(async () => json({ detail: 'invalid_barcode' }, 400));
  await assert.rejects(client.getProduct('12345'), client.InvalidBarcodeError);

  mockFetch(async () => json({ detail: 'invalid_barcode' }, 400));
  await assert.rejects(client.getProduct('12345'), (err: unknown) => {
    assert.ok(!(err instanceof client.OfflineError), '400 must not become OfflineError');
    return true;
  });
});
