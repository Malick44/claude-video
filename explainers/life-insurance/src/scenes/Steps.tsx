import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {evolvePath} from "@remotion/paths";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const STEPS = [
  {t: "Size it", d: "Run DIME. Add a parents' care fund.", at: 50},
  {t: "Shop term quotes", d: "20–30 years. Compare 3+ insurers.", at: 120},
  {t: "Add the right riders", d: "Conversion + waiver of premium.", at: 190},
  {t: "Name beneficiaries", d: "Plus a guardian. Review each life event.", at: 260},
];
const LINES = [
  {k: "Insured", v: "You · age 34 · non-smoker", at: 50},
  {k: "Coverage", v: "$1,300,000", at: 120},
  {k: "Term", v: "25 years, level premium", at: 150},
  {k: "Riders", v: "Conversion · Waiver of premium", at: 190},
  {k: "Beneficiary", v: "Partner (primary) · Family trust", at: 260},
  {k: "Est. premium", v: "≈ $70 / month", at: 300},
];

export const Steps: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const spine = evolvePath(ease(frame, [40, 300], [0, 1], (t) => t), "M 168 330 L 168 790");
  const stamp = spring({frame: frame - 310, fps, config: {damping: 8, stiffness: 160}});
  const card = spring({frame: frame - 24, fps, config: {damping: 16}});

  return (
    <Scene variant="dark" frames={frames} chapter="07 · GET IT DONE">
      <div style={{position: "absolute", left: 120, top: 100}}>
        <KineticText text="Four steps. One afternoon." size={80} delay={4} highlight={{afternoon: C.gold}} />
      </div>

      <svg width="1920" height="1080" style={{position: "absolute", inset: 0}}>
        <path d="M 168 330 L 168 790" stroke="rgba(255,255,255,.15)" strokeWidth="6" strokeLinecap="round" />
        <path d="M 168 330 L 168 790" stroke={C.teal} strokeWidth="6" strokeLinecap="round" fill="none" {...spine} />
      </svg>

      {STEPS.map((s, i) => {
        const p = spring({frame: frame - s.at, fps, config: {damping: 12, stiffness: 130}});
        return (
          <div key={s.t} style={{position: "absolute", left: 120, top: 300 + i * 150, width: 860, opacity: p, transform: `translateX(${(1 - p) * -80}px)`}}>
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 4,
                width: 96,
                height: 96,
                borderRadius: 48,
                background: C.teal,
                color: C.ink,
                fontFamily: display,
                fontWeight: 800,
                fontSize: 54,
                textAlign: "center",
                lineHeight: "96px",
                boxShadow: `0 0 ${20 + 24 * (1 - p)}px ${C.teal}`,
                transform: `scale(${0.6 + 0.4 * p})`,
              }}
            >
              {i + 1}
            </div>
            <div style={{marginLeft: 140}}>
              <div style={{fontFamily: display, fontWeight: 800, fontSize: 54, color: C.white}}>{s.t}</div>
              <div style={{fontFamily: body, fontWeight: 400, fontSize: 28, color: C.mute, marginTop: 4}}>{s.d}</div>
            </div>
          </div>
        );
      })}

      {/* policy card */}
      <div
        style={{
          position: "absolute",
          right: 120,
          top: 260,
          width: 700,
          height: 620,
          borderRadius: 30,
          background: C.cream,
          padding: "40px 46px",
          boxSizing: "border-box",
          boxShadow: "0 40px 100px rgba(0,0,0,.5)",
          opacity: card,
          transform: `translateY(${(1 - card) * 120}px) rotate(${(1 - card) * 5 + 1.5}deg)`,
        }}
      >
        <div style={{fontFamily: body, fontWeight: 800, fontSize: 22, letterSpacing: "0.22em", color: C.navy3}}>TERM LIFE POLICY</div>
        <div style={{fontFamily: display, fontWeight: 800, fontSize: 44, color: C.navy, marginBottom: 20}}>Your family's backup beam</div>
        {LINES.map((l) => {
          const o = ease(frame, [l.at, l.at + 14], [0, 1]);
          return (
            <div key={l.k} style={{display: "flex", justifyContent: "space-between", borderTop: "2px solid rgba(10,20,40,.12)", padding: "13px 0", opacity: o, transform: `translateX(${(1 - o) * 30}px)`}}>
              <span style={{fontFamily: body, fontWeight: 800, fontSize: 22, color: "#4A5878"}}>{l.k}</span>
              <span style={{fontFamily: body, fontWeight: 600, fontSize: 26, color: C.navy, textAlign: "right"}}>{l.v}</span>
            </div>
          );
        })}
        <div
          style={{
            position: "absolute",
            right: 40,
            bottom: 40,
            fontFamily: display,
            fontWeight: 800,
            fontSize: 54,
            color: C.teal,
            border: `6px solid ${C.teal}`,
            borderRadius: 14,
            padding: "2px 22px",
            opacity: stamp,
            transform: `rotate(-9deg) scale(${2.2 - 1.2 * stamp})`,
          }}
        >
          PROTECTED
        </div>
      </div>
      <div style={{position: "absolute", right: 120, bottom: 70, fontFamily: body, fontSize: 20, color: C.mute}}>Illustration only, not a quote.</div>
    </Scene>
  );
};
