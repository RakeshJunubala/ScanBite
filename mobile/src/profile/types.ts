export type Condition = 'diabetes' | 'bp' | 'cholesterol' | 'pregnancy' | 'weight';
export type Allergy = 'peanut' | 'treenut' | 'gluten' | 'lactose' | 'soy' | 'egg' | 'sesame';
export type Diet = 'vegetarian' | 'eggetarian' | 'jain' | 'vegan';

export interface Profile {
  conditions: Condition[];
  allergies: Allergy[];
  diets: Diet[];
}

export const EMPTY_PROFILE: Profile = { conditions: [], allergies: [], diets: [] };

export const CONDITION_OPTIONS: { id: Condition; label: string }[] = [
  { id: 'diabetes', label: 'Diabetes' },
  { id: 'bp', label: 'High BP' },
  { id: 'cholesterol', label: 'Cholesterol' },
  { id: 'pregnancy', label: 'Pregnancy' },
  { id: 'weight', label: 'Weight goals' },
];

export const ALLERGY_OPTIONS: { id: Allergy; label: string }[] = [
  { id: 'peanut', label: 'Peanut' },
  { id: 'treenut', label: 'Tree nuts' },
  { id: 'gluten', label: 'Gluten' },
  { id: 'lactose', label: 'Lactose' },
  { id: 'soy', label: 'Soy' },
  { id: 'egg', label: 'Egg' },
  { id: 'sesame', label: 'Sesame' },
];

export const DIET_OPTIONS: { id: Diet; label: string }[] = [
  { id: 'vegetarian', label: 'Vegetarian' },
  { id: 'eggetarian', label: 'Eggetarian' },
  { id: 'jain', label: 'Jain' },
  { id: 'vegan', label: 'Vegan' },
];

export function profileLabels(profile: Profile): string[] {
  const find = <T extends string>(options: { id: T; label: string }[], id: T) =>
    options.find((o) => o.id === id)?.label ?? id;
  return [
    ...profile.conditions.map((c) => find(CONDITION_OPTIONS, c)),
    ...profile.allergies.map((a) => `${find(ALLERGY_OPTIONS, a)} allergy`),
    ...profile.diets.map((d) => find(DIET_OPTIONS, d)),
  ];
}

export function profileSize(profile: Profile): number {
  return profile.conditions.length + profile.allergies.length + profile.diets.length;
}
