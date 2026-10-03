import React from "react";
import {AbsoluteFill, random, useCurrentFrame, useVideoConfig} from "remotion";
import {C} from "../theme";

export type Variant = "dark" | "deep" | "light";

const blobs = [
  {c: "#2B4FA3", x: 20, y: 25, r: 55, p: 0},
  {c: "#7A3FA0", x: 80, y: 70, r: 50, p: 2.1},
  {c: "#0E8F86", x: 55, y: 105, r: 60, p: 4.2},
];

export const Background: React.FC<{variant?: Variant; accent?: string}> = ({
  variant = "dark",
  accent,
}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const light = variant === "light";
  const base = light ? C.cream : variant === "deep" ? C.ink : C.navy;

  const gradients = blobs
    .map((b) => {
      const x = b.x + 14 * Math.sin(frame / 110 + b.p);
      const y = b.y + 12 * Math.cos(frame / 95 + b.p);
      const col = light ? (accent ?? "#F5C6A5") : b.c;
      const a = light ? "55" : variant === "deep" ? "40" : "66";
      return `radial-gradient(circle at ${x}% ${y}%, ${col}${a} 0%, transparent ${b.r}%)`;
    })
    .join(",");

  const grid = light ? "rgba(10,20,40,0.045)" : "rgba(255,255,255,0.045)";

  return (
    <AbsoluteFill style={{background: base}}>
      <AbsoluteFill style={{background: gradients}} />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${grid} 1px, transparent 1px), linear-gradient(90deg, ${grid} 1px, transparent 1px)`,
          backgroundSize: "96px 96px",
          backgroundPosition: `${-(frame * 0.35) % 96}px ${-(frame * 0.2) % 96}px`,
        }}
      />
      <svg width={width} height={height} style={{position: "absolute", inset: 0}}>
        {new Array(34).fill(0).map((_, i) => {
          const speed = 0.25 + random(`s${i}`) * 0.9;
          const size = 2 + random(`z${i}`) * 5;
          const x = random(`x${i}`) * width + Math.sin(frame / 60 + i) * 18;
          const y = height + 20 - ((frame * speed + random(`o${i}`) * (height + 40)) % (height + 40));
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={size}
              fill={light ? C.navy : C.white}
              opacity={light ? 0.09 : 0.16 + 0.12 * random(`a${i}`)}
            />
          );
        })}
      </svg>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.35) 100%)",
          opacity: light ? 0.25 : 1,
        }}
      />
    </AbsoluteFill>
  );
};
