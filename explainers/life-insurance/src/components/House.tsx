import React from "react";
import {C} from "../theme";

export const House: React.FC<{
  width?: number;
  glow?: number;
  wall?: string;
  roof?: string;
}> = ({width = 400, glow = 1, wall = "#EADFCB", roof = C.coral}) => (
  <svg viewBox="0 0 400 340" width={width} height={(width * 340) / 400} style={{overflow: "visible"}}>
    <rect x="285" y="40" width="30" height="70" fill="#6B3B3B" />
    <rect x="65" y="165" width="270" height="155" rx="6" fill={wall} />
    <polygon points="200,25 385,165 15,165" fill={roof} />
    <polygon points="200,25 385,165 345,165 200,60" fill="rgba(0,0,0,.12)" />
    <rect x="165" y="225" width="70" height="95" rx="8" fill="#3B4A73" />
    <circle cx="222" cy="275" r="5" fill={C.gold} />
    {[100, 262].map((x) => (
      <g key={x}>
        <rect x={x} y="200" width="46" height="50" rx="5" fill="#2B3E6E" />
        <rect x={x} y="200" width="46" height="50" rx="5" fill={C.gold} opacity={glow * 0.9} />
        <line x1={x + 23} y1="200" x2={x + 23} y2="250" stroke="#2B3E6E" strokeWidth="3" />
        <line x1={x} y1="225" x2={x + 46} y2="225" stroke="#2B3E6E" strokeWidth="3" />
      </g>
    ))}
    <rect x="0" y="318" width="400" height="10" rx="5" fill="rgba(0,0,0,.25)" />
  </svg>
);

/** 8-segment cubic paths so the house can morph into a shield. */
const toPath = (pts: [number, number][]) => {
  let d = `M${pts[0][0]} ${pts[0][1]}`;
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i];
    const b = pts[(i + 1) % pts.length];
    const c1 = [a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3];
    const c2 = [a[0] + ((b[0] - a[0]) * 2) / 3, a[1] + ((b[1] - a[1]) * 2) / 3];
    d += ` C${c1[0]} ${c1[1]} ${c2[0]} ${c2[1]} ${b[0]} ${b[1]}`;
  }
  return d + "Z";
};

export const HOUSE_PATH = toPath([
  [200, 25], [385, 165], [335, 165], [335, 320], [200, 320], [65, 320], [65, 165], [15, 165],
]);
export const SHIELD_PATH = toPath([
  [200, 20], [350, 62], [356, 185], [300, 280], [200, 335], [100, 280], [44, 185], [50, 62],
]);
