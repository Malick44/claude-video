import React from "react";
import {Easing, interpolate, useCurrentFrame} from "remotion";

export const Count: React.FC<{
  to: number;
  from?: number;
  start: number;
  dur: number;
  prefix?: string;
  suffix?: string;
  style?: React.CSSProperties;
}> = ({to, from = 0, start, dur, prefix = "", suffix = "", style}) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [start, start + dur], [from, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <span style={{fontVariantNumeric: "tabular-nums", ...style}}>
      {prefix}
      {Math.round(v).toLocaleString("en-US")}
      {suffix}
    </span>
  );
};
