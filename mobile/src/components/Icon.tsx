import Svg, { Circle, Path, Rect } from 'react-native-svg';

import { colors } from '../theme';

type Shape =
  | { kind: 'path'; d: string }
  | { kind: 'circle'; cx: number; cy: number; r: number }
  | { kind: 'rect'; x: number; y: number; width: number; height: number; rx: number };

const p = (d: string): Shape => ({ kind: 'path', d });
const c = (cx: number, cy: number, r: number): Shape => ({ kind: 'circle', cx, cy, r });

const ICONS = {
  scan: [
    p('M3 7V5a2 2 0 0 1 2-2h2'), p('M17 3h2a2 2 0 0 1 2 2v2'), p('M21 17v2a2 2 0 0 1-2 2h-2'),
    p('M7 21H5a2 2 0 0 1-2-2v-2'), p('M7 8v8'), p('M10.5 8v8'), p('M13.5 8v8'), p('M17 8v8'),
  ],
  search: [c(11, 11, 7), p('m20 20-3.5-3.5')],
  close: [p('M18 6 6 18'), p('m6 6 12 12')],
  bolt: [p('M13 2 3 14h9l-1 8 10-12h-9z')],
  chevronLeft: [p('m15 18-6-6 6-6')],
  chevronRight: [p('m9 18 6-6-6-6')],
  chevronDown: [p('m6 9 6 6 6-6')],
  alert: [p('M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z'), p('M12 9v4'), p('M12 17h.01')],
  check: [p('M20 6 9 17l-5-5')],
  info: [c(12, 12, 9), p('M12 16v-4'), p('M12 8h.01')],
  shield: [p('M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'), p('m9 12 2 2 4-4')],
  lock: [{ kind: 'rect', x: 4, y: 11, width: 16, height: 10, rx: 2 } as Shape, p('M8 11V7a4 4 0 0 1 8 0v4')],
  keypad: [
    { kind: 'rect', x: 3, y: 5, width: 18, height: 14, rx: 2 } as Shape,
    p('M7 9h.01'), p('M11 9h.01'), p('M15 9h.01'), p('M7 13h.01'), p('M11 13h.01'), p('M15 13h.01'), p('M8 16h8'),
  ],
  flag: [p('M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z'), p('M4 22v-7')],
  question: [c(12, 12, 9), p('M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3'), p('M12 17h.01')],
} satisfies Record<string, Shape[]>;

export type IconName = keyof typeof ICONS;

interface Props {
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export function Icon({ name, size = 22, color = colors.ink, strokeWidth = 2 }: Props) {
  const stroke = { stroke: color, strokeWidth, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, fill: 'none' };
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      {ICONS[name].map((shape: Shape, i: number) => {
        if (shape.kind === 'circle') return <Circle key={i} cx={shape.cx} cy={shape.cy} r={shape.r} {...stroke} />;
        if (shape.kind === 'rect') {
          return <Rect key={i} x={shape.x} y={shape.y} width={shape.width} height={shape.height} rx={shape.rx} {...stroke} />;
        }
        return <Path key={i} d={shape.d} {...stroke} />;
      })}
    </Svg>
  );
}
