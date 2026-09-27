// Personal alerts, worked out on the phone so the health profile never
// leaves the device. Pure functions: no React Native imports, so they run
// under Node for tests (npm run test:logic).

import type { NutrientFact, Product, ScoreResult } from '../api/types';
import type { Allergy, Condition, Diet, Profile } from './types';

export type AlertStatus = 'warn' | 'caution' | 'ok' | 'unknown';

export interface Alert {
  id: string;
  title: string;
  detail: string;
  status: AlertStatus;
}

const TEASPOON_G = 4;

// ---------- text matching ---------------------------------------------------

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Lower-cased ingredient text with look-alike phrases removed first. */
function cleaned(text: string, remove: string[] = []): string {
  let out = ` ${text.toLowerCase()} `;
  for (const phrase of remove) {
    out = out.split(phrase).join(' ');
  }
  return out;
}

/** Words found in the text, matched at a word start (so "eggs" matches "egg"). */
export function findWords(text: string, words: string[]): string[] {
  const found: string[] = [];
  for (const word of words) {
    const re = new RegExp(`(^|[^a-z])${escapeRegExp(word)}`, 'i');
    if (re.test(text) && !found.includes(word)) found.push(word);
  }
  return found;
}

function list(words: string[]): string {
  if (words.length <= 1) return words.join('');
  return `${words.slice(0, -1).join(', ')} and ${words[words.length - 1]}`;
}

// ---------- word lists --------------------------------------------------------

const MEAT_FISH = [
  'chicken', 'mutton', 'beef', 'pork', 'fish', 'prawn', 'shrimp', 'crab', 'meat', 'gelatin', 'gelatine',
  'anchovy', 'lard', 'tallow', 'animal fat', 'animal rennet', 'isinglass', 'collagen', 'shellfish',
];
const EGG = ['egg', 'albumen', 'albumin', 'mayonnaise'];
const DAIRY = [
  'milk', 'milk solids', 'milk powder', 'ghee', 'butter', 'cream', 'cheese', 'paneer', 'whey', 'casein',
  'curd', 'yogurt', 'yoghurt', 'khoya', 'lactose', 'condensed milk',
];
const PLANT_LOOKALIKES = [
  'coconut milk', 'almond milk', 'soy milk', 'soya milk', 'oat milk', 'rice milk', 'cocoa butter',
  'peanut butter', 'nut butter', 'coconut cream', 'shea butter',
];
const JAIN_AVOID = [
  'onion', 'garlic', 'potato', 'sweet potato', 'carrot', 'beetroot', 'beet root', 'radish', 'yam', 'arbi',
  'colocasia', 'mooli', 'lahsun', 'pyaz', 'honey',
];
const CAFFEINE = ['caffeine', 'coffee', 'guarana', 'green tea extract'];

const ALLERGY_RULES: Record<Allergy, { label: string; tags: string[]; words: string[]; traceTags: string[]; remove?: string[] }> = {
  peanut: {
    label: 'Peanut allergy',
    tags: ['peanut', 'peanuts'],
    words: ['peanut', 'groundnut', 'moongphali'],
    traceTags: ['peanut', 'peanuts', 'nuts', 'tree nuts'],
  },
  treenut: {
    label: 'Tree nut allergy',
    tags: ['tree nuts', 'nuts'],
    words: ['almond', 'cashew', 'walnut', 'pistachio', 'hazelnut', 'pecan', 'macadamia', 'badam', 'kaju', 'akhrot', 'pista'],
    traceTags: ['tree nuts', 'nuts'],
  },
  gluten: {
    label: 'Gluten',
    tags: ['gluten', 'wheat'],
    words: ['wheat', 'maida', 'atta', 'gluten', 'barley', 'rye', 'semolina', 'suji', 'sooji', 'rava', 'malt extract'],
    traceTags: ['gluten', 'wheat'],
    remove: ['buckwheat', 'gluten free', 'gluten-free'],
  },
  lactose: {
    label: 'Lactose',
    tags: ['milk'],
    words: ['milk', 'lactose', 'whey', 'cream', 'cheese', 'paneer', 'curd', 'yogurt', 'yoghurt', 'khoya', 'butter'],
    traceTags: ['milk'],
    remove: PLANT_LOOKALIKES,
  },
  soy: {
    label: 'Soy allergy',
    tags: ['soy', 'soybeans'],
    words: ['soy', 'soya', 'soybean'],
    traceTags: ['soy', 'soybeans'],
  },
  egg: {
    label: 'Egg allergy',
    tags: ['egg', 'eggs'],
    words: EGG,
    traceTags: ['egg', 'eggs'],
    remove: ['eggplant', 'eggless', 'egg-free', 'egg free'],
  },
  sesame: {
    label: 'Sesame allergy',
    tags: ['sesame'],
    words: ['sesame', 'til', 'gingelly'],
    traceTags: ['sesame'],
  },
};

// ---------- helpers --------------------------------------------------------------

function nutrient(score: ScoreResult, key: string): NutrientFact | undefined {
  return score.nutrients.find((n) => n.key === key);
}

function per100(product: Product): string {
  return product.is_drink ? '100 ml' : '100 g';
}

function teaspoons(grams: number): string {
  const tsp = grams / TEASPOON_G;
  if (tsp < 1) return 'under 1 teaspoon';
  const rounded = Math.round(tsp);
  return `about ${rounded} teaspoon${rounded === 1 ? '' : 's'}`;
}

function hasIngredients(product: Product): boolean {
  return Boolean(product.ingredients_text && product.ingredients_text.trim().length > 0);
}

// ---------- conditions ----------------------------------------------------------

function conditionAlert(id: Condition, product: Product, score: ScoreResult): Alert {
  const unknown = (title: string): Alert => ({
    id, title, status: 'unknown', detail: 'The label data we have is not enough to check this.',
  });
  switch (id) {
    case 'diabetes': {
      const sugar = nutrient(score, 'sugars_g');
      if (!sugar) return unknown('Diabetes');
      const serving = product.serving_size_g
        ? ` One ${product.serving_size_g} ${product.is_drink ? 'ml' : 'g'} serving has ${teaspoons((sugar.value * product.serving_size_g) / 100)}.`
        : '';
      const base = `${sugar.value} g sugar per ${per100(product)}, ${teaspoons(sugar.value)}.${serving}`;
      if (sugar.level === 'high') return { id, title: 'Diabetes — high sugar', status: 'warn', detail: base };
      // Sugar in drinks hits the blood fastest, so flag it earlier than in food.
      if (product.is_drink && sugar.value >= 5) return { id, title: 'Diabetes — sugary drink', status: 'warn', detail: base };
      if (sugar.level === 'medium') return { id, title: 'Diabetes — some sugar', status: 'caution', detail: base };
      return { id, title: 'Diabetes — low sugar', status: 'ok', detail: `${sugar.value} g sugar per ${per100(product)}.` };
    }
    case 'bp': {
      const sodium = nutrient(score, 'sodium_mg');
      if (!sodium) return unknown('High BP');
      const salt = Math.round(((sodium.value * 2.5) / 1000) * 10) / 10;
      const detail = `${sodium.value} mg sodium per ${per100(product)} (about ${salt} g salt).`;
      if (sodium.level === 'high') return { id, title: 'High BP — high salt', status: 'warn', detail };
      if (sodium.level === 'medium') return { id, title: 'High BP — some salt', status: 'caution', detail };
      return { id, title: 'High BP — low salt', status: 'ok', detail };
    }
    case 'cholesterol': {
      const sat = nutrient(score, 'saturated_fat_g');
      const trans = nutrient(score, 'trans_fat_g');
      const hydrogenated = score.processing.some((p) => p.key === 'hydrogenated_fat');
      if (trans || hydrogenated) {
        return {
          id, title: 'Cholesterol — trans fat risk', status: 'warn',
          detail: hydrogenated ? 'Contains hydrogenated fat (vanaspati), a source of trans fat.' : `${trans!.value} g trans fat per ${per100(product)}.`,
        };
      }
      if (!sat) return unknown('Cholesterol');
      const detail = `${sat.value} g saturated fat per ${per100(product)}.`;
      if (sat.level === 'high') return { id, title: 'Cholesterol — high saturated fat', status: 'warn', detail };
      if (sat.level === 'medium') return { id, title: 'Cholesterol — some saturated fat', status: 'caution', detail };
      return { id, title: 'Cholesterol — low saturated fat', status: 'ok', detail };
    }
    case 'pregnancy': {
      // Pregnancy is where a wrong or overconfident line does the most harm, so
      // these state what the label says and refer the decision onward. They never
      // tell someone to avoid a food, and never claim a judgement as ours.
      const restricted = score.additives.filter((a) => a.risk === 'high');
      if (restricted.length) {
        return {
          id,
          title: 'Pregnancy — additive to discuss',
          status: 'warn',
          detail: `Contains ${restricted.map((a) => a.name).join(', ')}. A food regulator has prohibited ${restricted.length > 1 ? 'these' : 'this'} elsewhere. Worth raising with your doctor or midwife.`,
        };
      }
      if (!hasIngredients(product)) return unknown('Pregnancy');
      const caffeine = findWords(cleaned(product.ingredients_text!), CAFFEINE);
      if (caffeine.length) {
        return { id, title: 'Pregnancy — contains caffeine', status: 'caution', detail: 'The ingredients list caffeine. Amounts are rarely printed, so check your daily limit with your doctor.' };
      }
      return { id, title: 'Pregnancy — nothing flagged', status: 'ok', detail: 'No caffeine or restricted additives in the ingredients we can read.' };
    }
    case 'weight': {
      const energy = nutrient(score, 'energy_kcal');
      const sugar = nutrient(score, 'sugars_g');
      if (!energy) return unknown('Weight goals');
      if (sugar?.level === 'high') {
        return { id, title: 'Weight goals — high sugar', status: 'warn', detail: `${energy.value} kcal and ${sugar.value} g sugar per ${per100(product)}.` };
      }
      if (!product.is_drink && energy.value >= 400) {
        return { id, title: 'Weight goals — energy-dense', status: 'caution', detail: `${energy.value} kcal per ${per100(product)}. Watch the portion.` };
      }
      return { id, title: 'Weight goals — fits', status: 'ok', detail: `${energy.value} kcal per ${per100(product)}.` };
    }
  }
}

// ---------- allergies ---------------------------------------------------------

function allergyAlert(id: Allergy, product: Product): Alert {
  const rule = ALLERGY_RULES[id];
  const tags = product.allergens.map((a) => a.toLowerCase());
  const traces = product.traces.map((t) => t.toLowerCase());
  const tagHit = rule.tags.some((t) => tags.includes(t));
  const words = hasIngredients(product) ? findWords(cleaned(product.ingredients_text!, rule.remove), rule.words) : [];

  if (tagHit || words.length) {
    const what = words.length ? list(words) : rule.tags[0];
    return { id, title: `${rule.label} — contains ${what}`, status: 'warn', detail: `The label lists ${what}.` };
  }
  const traceHit = traces.find((t) => rule.traceTags.includes(t));
  if (traceHit) {
    return {
      id, title: `${rule.label} — check traces`, status: 'caution',
      detail: `Not in the ingredients, but the pack says “may contain ${traceHit}”.`,
    };
  }
  if (!hasIngredients(product) && tags.length === 0) {
    return { id, title: rule.label, status: 'unknown', detail: 'No ingredient list yet, so we can’t check this.' };
  }
  return { id, title: `${rule.label} — none listed`, status: 'ok', detail: 'Not in the ingredients or allergen list.' };
}

// ---------- diets ---------------------------------------------------------------

function dietAlert(id: Diet, product: Product, score: ScoreResult): Alert {
  const label = { vegetarian: 'Vegetarian', eggetarian: 'Eggetarian', jain: 'Jain', vegan: 'Vegan' }[id];
  if (!hasIngredients(product)) {
    return { id, title: label, status: 'unknown', detail: 'No ingredient list yet, so we can’t check this.' };
  }
  const text = cleaned(product.ingredients_text!, ['eggplant', 'eggless', 'egg-free', 'egg free', ...PLANT_LOOKALIKES]);
  const hits: string[] = [...findWords(text, MEAT_FISH)];
  if (id !== 'eggetarian') hits.push(...findWords(text, EGG));
  if (id === 'vegan') hits.push(...findWords(text, [...DAIRY, 'honey']));
  if (id === 'jain') hits.push(...findWords(text, JAIN_AVOID));

  const animalAdditives = score.additives.filter((a) => a.animal === 'yes');
  const maybeAnimal = score.additives.filter((a) => a.animal === 'maybe');
  // Carmine (insects) is not vegetarian; shellac is only a problem for vegans.
  for (const a of animalAdditives) {
    if (a.code === '904' && id !== 'vegan') continue;
    hits.push(a.name);
  }
  const unique = Array.from(new Set(hits));
  if (unique.length) {
    return { id, title: `${label} — contains ${list(unique.slice(0, 3))}`, status: 'warn', detail: `The label lists ${list(unique)}.` };
  }
  const vegMark = product.labels.includes('vegetarian');
  if (maybeAnimal.length && (id === 'vegan' || !vegMark)) {
    const names = maybeAnimal.map((a) => `INS ${a.code}`);
    return {
      id, title: `${label} — check additives`, status: 'caution',
      detail: `${list(names)} can be made from animal or plant sources. The label doesn’t say which.`,
    };
  }
  if (id === 'jain') {
    const ginger = findWords(text, ['ginger']);
    if (ginger.length) {
      return { id, title: 'Jain — contains ginger', status: 'caution', detail: 'Ginger is listed; some Jains avoid it when fresh.' };
    }
    return { id, title: 'Jain — fits', status: 'ok', detail: 'No onion, garlic, root vegetables or honey listed.' };
  }
  const detail = vegMark && id !== 'vegan' ? 'Green vegetarian mark on the pack.' : 'Nothing from animals listed.';
  return { id, title: `${label} — fits`, status: 'ok', detail };
}

// ---------- entry point ----------------------------------------------------------

const ORDER: Record<AlertStatus, number> = { warn: 0, caution: 1, unknown: 2, ok: 3 };

/** One alert per item in the profile, most serious first. */
export function profileAlerts(profile: Profile, product: Product, score: ScoreResult): Alert[] {
  const alerts = [
    ...profile.conditions.map((c) => conditionAlert(c, product, score)),
    ...profile.allergies.map((a) => allergyAlert(a, product)),
    ...profile.diets.map((d) => dietAlert(d, product, score)),
  ];
  return alerts.sort((a, b) => ORDER[a.status] - ORDER[b.status]);
}
