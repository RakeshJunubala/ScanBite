import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { colors } from '../theme';

export function Logo({ size = 30, background = colors.brand }: { size?: number; background?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 28 28">
      <Rect width={28} height={28} rx={8} fill={background} />
      <Circle cx={12.5} cy={12.5} r={6.5} fill="none" stroke="#FFFFFF" strokeWidth={2.2} />
      <Path d="M17.3 17.3 22 22" fill="none" stroke="#FFFFFF" strokeWidth={2.4} strokeLinecap="round" />
      <Path d="m9.6 12.7 2 2 3.5-3.8" fill="none" stroke="#9FE0BD" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" />
    </Svg>
  );
}
