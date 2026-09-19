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
