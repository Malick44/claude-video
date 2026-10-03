import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {Count} from "../components/Count";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const BARS = [
  {age: 30, v: 48},
  {age: 35, v: 56},
  {age: 40, v: 82},
  {age: 45, v: 138},
  {age: 50, v: 245},
];
const MAX_H = 440;

export const Cost: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const callout = spring({frame: frame - 335, fps, config: {damping: 11, stiffness: 120}});

  return (
    <Scene variant="dark" frames={frames} chapter="04 · THE PRICE">
      <div style={{position: "absolute", left: 120, top: 120, width: 900}}>
        <KineticText text="The surprising part?" size={64} delay={4} color={C.mute} weight={600} />
        <KineticText text="It's cheap." size={170} delay={16} color={C.teal} />
      </div>

      {/* price card */}
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 540,
          width: 720,
          padding: "36px 44px",
          borderRadius: 32,
          background: "rgba(255,255,255,.07)",
          border: `2px solid ${C.teal}88`,
          opacity: ease(frame, [60, 80], [0, 1]),
          transform: `translateY(${ease(frame, [60, 90], [60, 0])}px)`,
        }}
      >
        <div style={{fontFamily: body, fontWeight: 800, fontSize: 19, letterSpacing: "0.1em", color: C.mute}}>
          $1,000,000 · 20-YEAR TERM · AGE 32, HEALTHY
        </div>
        <div style={{display: "flex", alignItems: "baseline", gap: 14, marginTop: 10}}>
          <span style={{fontFamily: display, fontWeight: 800, fontSize: 150, color: C.white, lineHeight: 1}}>
            <Count to={50} start={80} dur={40} prefix="≈$" />
          </span>
          <span style={{fontFamily: body, fontWeight: 600, fontSize: 40, color: C.mute}}>/ month</span>
        </div>
        <div style={{fontFamily: body, fontWeight: 600, fontSize: 30, color: C.gold, marginTop: 6, opacity: ease(frame, [130, 150], [0, 1])}}>
          That's about <b>$1.65 a day</b> to protect $1,000,000.
        </div>
      </div>

      {/* chart */}
      <div style={{position: "absolute", right: 120, top: 130, width: 860, height: 820}}>
        <div style={{fontFamily: display, fontWeight: 800, fontSize: 46, color: C.white, opacity: ease(frame, [90, 110], [0, 1])}}>
          What waiting costs
        </div>
        <div style={{fontFamily: body, fontSize: 24, color: C.mute, marginBottom: 20, opacity: ease(frame, [90, 110], [0, 1])}}>
          Monthly premium, same $1M / 20-year term
        </div>
        <div style={{position: "absolute", left: 0, right: 0, bottom: 90, height: MAX_H + 10, borderBottom: "3px solid rgba(255,255,255,.3)"}}>
          {BARS.map((b, i) => {
            const at = 110 + i * 22;
            const g = ease(frame, [at, at + 40], [0, 1]);
            const h = (b.v / 245) * MAX_H * g;
            const last = i === BARS.length - 1;
            const color = i === 0 ? C.teal : last ? C.coral : C.violet;
            return (
              <div key={b.age} style={{position: "absolute", left: i * 170 + 10, bottom: 0, width: 130}}>
                <div style={{position: "absolute", bottom: h + 10, width: "100%", textAlign: "center", fontFamily: display, fontWeight: 800, fontSize: 40, color: C.white, opacity: g}}>
                  <Count to={b.v} start={at} dur={40} prefix="$" />
                </div>
                <div
                  style={{
                    height: h,
                    borderRadius: "16px 16px 0 0",
                    background: `linear-gradient(180deg, ${color}, ${color}AA)`,
                    boxShadow: `0 0 36px ${color}55`,
                  }}
                />
                <div style={{position: "absolute", top: 18, width: "100%", textAlign: "center", fontFamily: body, fontWeight: 800, fontSize: 30, color: C.mute}}>
                  Age {b.age}
                </div>
              </div>
            );
          })}
        </div>
        <div
          style={{
            position: "absolute",
            right: 10,
            top: 80,
            fontFamily: display,
            fontWeight: 800,
            fontSize: 64,
            color: C.coral,
            transform: `scale(${callout}) rotate(${(1 - callout) * 12 - 3}deg)`,
            transformOrigin: "right center",
            opacity: callout,
            textAlign: "right",
            lineHeight: 1,
          }}
        >
          5× more
          <div style={{fontFamily: body, fontWeight: 600, fontSize: 28, color: C.white}}>for the same cover</div>
        </div>
      </div>
      <div style={{position: "absolute", left: 120, bottom: 54, fontFamily: body, fontSize: 20, color: C.mute, opacity: 0.85}}>
        Illustrative rates for a non-smoking, healthy applicant. Actual premiums vary by insurer, age, health and state.
      </div>
    </Scene>
  );
};
