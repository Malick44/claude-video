import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {ease, INOUT} from "../anim";
import {C, body, display} from "../theme";

const CARDS = [
  {myth: "“My employer already covers me.”", truth: "Group life is often just 1–2× salary, and it usually ends when you change jobs.", icon: "🏢"},
  {myth: "“I'm young. I'll do it later.”", truth: "Young and healthy is exactly when it's cheapest. Every birthday raises the price.", icon: "⏳"},
  {myth: "“My stay-at-home partner doesn't need it.”", truth: "Replacing a full-time parent's work (childcare, meals, logistics) costs tens of thousands a year.", icon: "🏡"},
  {myth: "“The payout gets taxed away.”", truth: "Death benefits are generally income-tax-free to your named beneficiaries and skip probate.", icon: "🧾"},
];
const W = 800;
const H = 320;

export const Myths: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <Scene variant="light" frames={frames} chapter="06 · MYTHS VS. FACTS" accent="#F5B8A0">
      <div style={{position: "absolute", left: 120, top: 98}}>
        <KineticText text="Four things millennials tell themselves." size={62} delay={4} color={C.navy} highlight={{tell: C.coral}} />
      </div>
      {CARDS.map((c, i) => {
        const col = i % 2;
        const row = Math.floor(i / 2);
        const enter = spring({frame: frame - 30 - i * 8, fps, config: {damping: 14, stiffness: 110}});
        const flipAt = 90 + i * 70;
        const flip = ease(frame, [flipAt, flipAt + 26], [0, 180], INOUT);
        const lift = Math.sin((flip / 180) * Math.PI) * 24;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 120 + col * (W + 80),
              top: 245 + row * (H + 36),
              width: W,
              height: H,
              perspective: 1600,
              opacity: enter,
              transform: `translateY(${(1 - enter) * 90 - lift}px)`,
            }}
          >
            <div style={{position: "relative", width: "100%", height: "100%", transformStyle: "preserve-3d", transform: `rotateY(${flip}deg)`}}>
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  backfaceVisibility: "hidden",
                  borderRadius: 30,
                  background: `linear-gradient(135deg, ${C.coral}, #E0483A)`,
                  boxShadow: "0 24px 60px rgba(224,72,58,.35)",
                  padding: 40,
                  boxSizing: "border-box",
                  color: C.white,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div style={{fontFamily: body, fontWeight: 800, fontSize: 22, letterSpacing: "0.22em", opacity: 0.85}}>MYTH</div>
                <div style={{fontFamily: display, fontWeight: 800, fontSize: 50, lineHeight: 1.12}}>{c.myth}</div>
                <div style={{fontSize: 44}}>{c.icon}</div>
              </div>
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  backfaceVisibility: "hidden",
                  transform: "rotateY(180deg)",
                  borderRadius: 30,
                  background: `linear-gradient(135deg, ${C.navy}, ${C.navy3})`,
                  border: `3px solid ${C.teal}`,
                  boxShadow: `0 24px 60px ${C.teal}44`,
                  padding: 40,
                  boxSizing: "border-box",
                  color: C.white,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div style={{fontFamily: body, fontWeight: 800, fontSize: 22, letterSpacing: "0.22em", color: C.teal}}>✓ THE REALITY</div>
                <div style={{fontFamily: body, fontWeight: 600, fontSize: 36, lineHeight: 1.28}}>{c.truth}</div>
              </div>
            </div>
          </div>
        );
      })}
    </Scene>
  );
};
