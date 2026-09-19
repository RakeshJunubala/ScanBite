// Demo mode: no API URL set, bundled products only.
import assert from 'node:assert/strict';
import { test } from 'node:test';

process.env.EXPO_PUBLIC_API_URL = '';

test('demo mode serves bundled products and alternatives', async () => {
  const client = await import('./client');
  const config = await import('../config');
  assert.equal(config.DEMO_MODE, true);

  const biscuit = await client.getProduct(config.DEMO_BARCODE);
  assert.equal(biscuit.product.name, 'Multigrain Digestive Biscuits');
  assert.equal(biscuit.score.verdict, 'avoid');

  const alternatives = await client.getAlternatives(config.DEMO_BARCODE);
  assert.deepEqual(alternatives.map((a) => a.product.name), ['Jowar & Millet Thins', 'Ragi Oat Cookies']);

  await assert.rejects(client.getProduct('8900000000019'), client.NotFoundError);
  assert.equal((await client.search('cola')).length, 2);
});
