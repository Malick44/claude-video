import React from "react";
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {evolvePath} from "@remotion/paths";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {House} from "../components/House";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const WORDS = [
  {t: "Mortgage.", c: C.coral, at: 6},
  {t: "Daycare.", c: C.gold, at: 22},
  {t: "Mom's prescriptions.", c: C.violet, at: 36},
  {t: "College fund.", c: C.teal, at: 48},
  {t: "Roof repairs.", c: C.white, at: 58},
];
const CRACK = "M236 178 L226 214 L248 238 L222 272 L244 300 L230 330";

export const Hook: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const stackOut = ease(frame, [84, 104], [0, 1]);
  const shake = frame > 170 && frame < 200 ? Math.sin(frame * 3.1) * (200 - frame) * 0.12 : 0;
  const crack = evolvePath(ease(frame, [160, 182], [0, 1]), CRACK);
  const beam = spring({frame: frame - 118, fps, config: {damping: 12, stiffness: 90}});
  const final = ease(frame, [196, 220], [0, 1]);

  return (
    <Scene variant="deep" frames={frames} push={0.04}>
      {/* Phase A: slam stack */}
      <AbsoluteFill
        style={{
          alignItems: "center",
          justifyContent: "center",
          opacity: 1 - stackOut,
          transform: `translateY(${-stackOut * 120}px) scale(${1 - stackOut * 0.2})`,
          filter: `blur(${stackOut * 16}px)`,
        }}
      >
        <div style={{textAlign: "center"}}>
          {WORDS.map((w, i) => {
            const s = spring({frame: frame - w.at, fps, config: {damping: 9, stiffness: 260, mass: 0.6}});
            const hit = frame >= w.at ? 1 : 0;
            const jolt = frame >= w.at && frame < w.at + 8 ? Math.sin(frame * 5) * (8 - (frame - w.at)) * 1.4 : 0;
            return (
              <div
                key={w.t}
                style={{
                  fontFamily: display,
                  fontWeight: 800,
                  fontSize: 118,
                  lineHeight: 1.04,
                  color: w.c,
                  opacity: hit,
                  transform: `scale(${1.9 - 0.9 * s}) translateX(${jolt}px)`,
                  letterSpacing: "-0.03em",
                }}
              >
                {w.t}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Phase B: load-bearing wall */}
      <div style={{position: "absolute", left: 0, right: 0, top: 110, textAlign: "center", transform: `translateX(${shake}px)`}}>
        <KineticText text="You're the" size={88} delay={100} color={C.mute} align="center" weight={600} />
        <KineticText
          text="load-bearing wall."
          size={150}
          delay={112}
          align="center"
          highlight={{"load-bearing": C.gold}}
        />
      </div>

      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 56,
          transform: `translateX(calc(-50% + ${shake}px)) scale(${0.55 + 0.45 * beam}) translateY(${(1 - beam) * 200}px)`,
          opacity: beam,
        }}
      >
        <div style={{position: "relative"}}>
          <House width={520} glow={1 - ease(frame, [182, 196], [0, 0.8])} />
          {/* the beam */}
          <div
            style={{
              position: "absolute",
              left: 520 * 0.5 - 22,
              top: 520 * 0.4 + 6,
              width: 44,
              height: 520 * 0.4 - 14,
              borderRadius: 8,
              background: `linear-gradient(90deg, ${C.teal}, #0E8F86)`,
              boxShadow: `0 0 ${24 + Math.sin(frame / 6) * 10}px ${C.teal}`,
              opacity: ease(frame, [190, 230], [1, 0.55]),
            }}
          />
          <svg
            viewBox="0 0 400 340"
            width={520}
            height={520 * 0.85}
            style={{position: "absolute", inset: 0, overflow: "visible"}}
          >
            <path d={CRACK} stroke={C.coral} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round" {...crack} />
          </svg>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 110,
          bottom: 130,
          width: 520,
          fontFamily: body,
          fontWeight: 600,
          fontSize: 34,
          lineHeight: 1.3,
          color: C.white,
          opacity: final,
          transform: `translateX(${(1 - final) * 40}px)`,
        }}
      >
        Life insurance is the <span style={{color: C.teal, fontWeight: 800}}>backup beam</span> that keeps the house standing.
      </div>
    </Scene>
  );
};
