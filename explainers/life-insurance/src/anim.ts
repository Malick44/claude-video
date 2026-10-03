import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

export const OUT = Easing.bezier(0.22, 1, 0.36, 1);
export const INOUT = Easing.bezier(0.65, 0, 0.35, 1);

type Cfg = {damping?: number; stiffness?: number; mass?: number};

export const useSpring = (delay = 0, config: Cfg = {damping: 14, stiffness: 120, mass: 0.8}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - delay, fps, config});
};

/** clamped interpolate with a nice default ease */
export const ease = (
  frame: number,
  [a, b]: [number, number],
  [x, y]: [number, number],
  easing: (t: number) => number = OUT,
) =>
  interpolate(frame, [a, b], [x, y], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });

export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
