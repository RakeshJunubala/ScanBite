// Run: npm run test:logic
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test } from 'node:test';

import type { Product, ProductResult } from '../api/types';
import { findWords, profileAlerts } from './alerts';
import { EMPTY_PROFILE, type Profile } from './types';

const demo = JSON.parse(readFileSync(join(__dirname, '..', 'demo', 'demoData.json'), 'utf8')) as {
  products: Record<string, ProductResult>;
};
const byName = (name: string): ProductResult => {
  const found = Object.values(demo.products).find((r) => r.product.name === name);
  if (!found) throw new Error(`demo product missing: ${name}`);
  return found;
};
const profile = (p: Partial<Profile>): Profile => ({ ...EMPTY_PROFILE, ...p });
const alertsFor = (name: string, p: Partial<Profile>) => {
  const r = byName(name);
  return profileAlerts(profile(p), r.product, r.score);
};
const withIngredients = (r: ProductResult, ingredients_text: string | null, extra: Partial<Product> = {}): ProductResult => ({
  ...r,
  product: { ...r.product, ingredients_text, allergens: [], traces: [], labels: [], ...extra },
});

test('empty profile gives no alerts', () => {
  assert.deepEqual(alertsFor('Rolled Oats', {}), []);
});

test('biscuit: diabetes warns, peanut traces caution, Jain fits — most serious first', () => {
  const alerts = alertsFor('Multigrain Digestive Biscuits', { conditions: ['diabetes'], allergies: ['peanut'], diets: ['jain'] });
  assert.deepEqual(alerts.map((a) => [a.id, a.status]), [
    ['diabetes', 'warn'],
    ['peanut', 'caution'],
    ['jain', 'ok'],
  ]);
  assert.equal(alerts[0].title, 'Diabetes — high sugar');
  assert.equal(alerts[0].detail, '24 g sugar per 100 g, about 6 teaspoons. One 30 g serving has about 2 teaspoons.');
  assert.match(alerts[1].detail, /may contain nuts/);
  assert.equal(alerts[2].title, 'Jain — fits');
});

test('makhana seasoning with onion and garlic is flagged for Jains', () => {
  const [jain] = alertsFor('Roasted Makhana, Peri Peri', { diets: ['jain'] });
  assert.equal(jain.status, 'warn');
  assert.equal(jain.title, 'Jain — contains onion and garlic');
});

test('cola is a sugary drink for diabetes, with teaspoons per bottle', () => {
  const [diabetes] = alertsFor('Cola', { conditions: ['diabetes'] });
  assert.equal(diabetes.status, 'warn');
  assert.equal(diabetes.title, 'Diabetes — sugary drink');
  assert.match(diabetes.detail, /One 300 ml serving has about 8 teaspoons/);
});

test('noodles: high salt for BP, wheat for gluten', () => {
  const alerts = alertsFor('Instant Masala Noodles', { conditions: ['bp'], allergies: ['gluten'] });
  const bp = alerts.find((a) => a.id === 'bp')!;
  const gluten = alerts.find((a) => a.id === 'gluten')!;
  assert.equal(bp.status, 'warn');
  assert.equal(bp.title, 'High BP — high salt');
  assert.equal(gluten.status, 'warn');
  assert.equal(gluten.title, 'Gluten — contains wheat, maida and gluten'); // "wheat gluten" is listed
});

test('green vegetarian mark is trusted, but vegans are told to check maybe-animal additives', () => {
  const [veg] = alertsFor('Instant Masala Noodles', { diets: ['vegetarian'] });
  assert.equal(veg.status, 'ok');
  assert.equal(veg.detail, 'Green vegetarian mark on the pack.');
  const [vegan] = alertsFor('Instant Masala Noodles', { diets: ['vegan'] });
  assert.equal(vegan.status, 'caution');
  assert.match(vegan.detail, /INS 627 and INS 631/);
});

test('ragi cookies contain milk and butter for lactose and vegan', () => {
  const alerts = alertsFor('Ragi Oat Cookies', { allergies: ['lactose'], diets: ['vegan'] });
  const lactose = alerts.find((a) => a.id === 'lactose')!;
  const vegan = alerts.find((a) => a.id === 'vegan')!;
  assert.equal(lactose.title, 'Lactose — contains milk and butter');
  assert.equal(vegan.status, 'warn');
});

test('coconut milk and cocoa butter are not dairy', () => {
  const r = withIngredients(byName('Rolled Oats'), 'Oats, coconut milk powder, cocoa butter, sugar');
  const alerts = profileAlerts(profile({ allergies: ['lactose'], diets: ['vegan'] }), r.product, r.score);
  assert.ok(alerts.every((a) => a.status === 'ok'), JSON.stringify(alerts));
});

test('eggless is not egg', () => {
  const r = withIngredients(byName('Rolled Oats'), 'Refined wheat flour, sugar, eggless cake premix');
  const alerts = profileAlerts(profile({ allergies: ['egg'], diets: ['vegetarian'] }), r.product, r.score);
  assert.deepEqual(alerts.map((a) => a.status), ['ok', 'ok']);
});

test('gelatin fails vegetarian and carmine fails vegetarian via additive data', () => {
  const r = withIngredients(byName('Rolled Oats'), 'Sugar, gelatin, colour');
  const [veg] = profileAlerts(profile({ diets: ['vegetarian'] }), r.product, r.score);
  assert.equal(veg.status, 'warn');
  const carmine = { ...r, score: { ...r.score, additives: [{ code: '120', name: 'Carmine (cochineal)', function: 'Colour', risk: 'low' as const, known: true, animal: 'yes' as const }] } };
  const withCarmine = withIngredients(carmine, 'Sugar, colour [120]');
  const [veg2] = profileAlerts(profile({ diets: ['vegetarian'] }), withCarmine.product, withCarmine.score);
  assert.equal(veg2.title, 'Vegetarian — contains Carmine (cochineal)');
});

test('missing ingredient list gives unknown, not a false all-clear', () => {
  const r = withIngredients(byName('Rolled Oats'), null);
  const alerts = profileAlerts(profile({ allergies: ['peanut'], diets: ['jain'] }), r.product, r.score);
  assert.deepEqual(alerts.map((a) => a.status), ['unknown', 'unknown']);
});

test('findWords matches at word starts only', () => {
  assert.deepEqual(findWords(' shellfish, buckwheat ', ['fish', 'wheat']), []);
  assert.deepEqual(findWords(' eggs, wheat flour ', ['egg', 'wheat']), ['egg', 'wheat']);
});
