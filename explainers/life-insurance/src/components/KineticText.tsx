import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {C, display} from "../theme";

type Props = {
  text: string;
  size: number;
  delay?: number;
  stagger?: number;
  color?: string;
  weight?: number;
  family?: string;
  align?: "left" | "center" | "right";
  highlight?: Record<string, string>;
  lineHeight?: number;
  style?: React.CSSProperties;
};

/** Word-by-word spring reveal with blur + rise + tilt. */
export const KineticText: React.FC<Props> = ({
  text,
  size,
  delay = 0,
  stagger = 4,
  color = C.white,
  weight = 800,
  family = display,
  align = "left",
  highlight = {},
  lineHeight = 1.08,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(" ");
  return (
    <div
      style={{
        fontFamily: family,
        fontSize: size,
        fontWeight: weight,
        color,
        textAlign: align,
        lineHeight,
        letterSpacing: "-0.02em",
        ...style,
      }}
    >
      {words.map((w, i) => {
        const s = spring({
          frame: frame - delay - i * stagger,
          fps,
          config: {damping: 13, stiffness: 140, mass: 0.7},
        });
        const clean = w.replace(/[.,!?']/g, "");
        const hl = highlight[clean];
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              marginRight: "0.26em",
              opacity: Math.min(1, s * 1.6),
              transform: `translateY(${(1 - s) * 0.55 * size}px) rotate(${(1 - s) * 5}deg) scale(${0.9 + 0.1 * s})`,
              filter: `blur(${(1 - s) * 14}px)`,
              color: hl ?? color,
              transformOrigin: "left bottom",
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};
