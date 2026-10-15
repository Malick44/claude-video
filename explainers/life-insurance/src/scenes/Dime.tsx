import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {Count} from "../components/Count";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const ITEMS = [
  {k: "D", name: "Debt", note: "Car loan, cards, student loans", v: 40000, color: C.violet, at: 70},
  {k: "I", name: "Income", note: "$85K salary × 10 years", v: 850000, color: C.teal, at: 160},
  {k: "M", name: "Mortgage", note: "Remaining balance", v: 320000, color: C.coral, at: 250},
  {k: "E", name: "Education", note: "2 kids, 4 years each", v: 120000, color: C.gold, at: 340},
];
const TOTAL = ITEMS.reduce((a, b) => a + b.v, 0);
const TOWER_H = 620;

export const Dime: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const totalIn = spring({frame: frame - 430, fps, config: {damping: 12, stiffness: 100}});

  // tower segments stack bottom-up in the order D, I, M, E
  let acc = 0;
  const segs = ITEMS.map((it) => {
    const g = ease(frame, [it.at + 10, it.at + 50], [0, 1]);
    const h = (it.v / TOTAL) * TOWER_H * g;
    const seg = {...it, h, bottom: acc};
    acc += (it.v / TOTAL) * TOWER_H;
    return seg;
  });

  return (
    <Scene variant="light" frames={frames} chapter="03 · YOUR NUMBER" accent="#F5B8A0">
      <div style={{position: "absolute", left: 120, top: 120}}>
        <KineticText
          text="How much coverage? Start with"
          size={64}
          delay={4}
          color={C.navy}
          weight={600}
        />
        <div style={{display: "flex", gap: 14, marginTop: 14}}>
          {ITEMS.map((it, i) => {
            const s = spring({frame: frame - 26 - i * 6, fps, config: {damping: 9, stiffness: 180}});
            return (
              <div
                key={it.k}
                style={{
                  width: 100,
                  height: 100,
                  borderRadius: 24,
                  background: it.color,
                  color: it.color === C.gold ? C.navy : C.white,
                  fontFamily: display,
                  fontWeight: 800,
                  fontSize: 72,
                  textAlign: "center",
                  lineHeight: "100px",
                  transform: `scale(${s}) rotate(${(1 - s) * -25}deg)`,
                  boxShadow: `0 12px 30px ${it.color}66`,
                }}
              >
                {it.k}
              </div>
            );
          })}
        </div>
      </div>

      {/* rows */}
      <div style={{position: "absolute", left: 120, top: 370, width: 1000}}>
        {ITEMS.map((it, i) => {
          const s = spring({frame: frame - it.at, fps, config: {damping: 14, stiffness: 110}});
          const active = frame >= it.at && (i === ITEMS.length - 1 || frame < ITEMS[i + 1].at);
          return (
            <div
              key={it.k}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 26,
                height: 120,
                marginBottom: 12,
                padding: "0 28px",
                borderRadius: 26,
                background: active ? C.white : "rgba(255,255,255,.55)",
                boxShadow: active ? `0 18px 44px ${it.color}44` : "none",
                border: `2px solid ${active ? it.color : "transparent"}`,
                opacity: s,
                transform: `translateX(${(1 - s) * -160}px) scale(${active ? 1.02 : 1})`,
              }}
            >
              <div style={{width: 14, height: 70, borderRadius: 7, background: it.color}} />
              <div style={{flex: 1}}>
                <div style={{fontFamily: display, fontWeight: 800, fontSize: 44, color: C.navy}}>{it.name}</div>
                <div style={{fontFamily: body, fontWeight: 400, fontSize: 25, color: "#4A5878"}}>{it.note}</div>
              </div>
              <div style={{fontFamily: display, fontWeight: 800, fontSize: 54, color: C.navy}}>
                <Count to={it.v} start={it.at + 8} dur={40} prefix="$" />
              </div>
            </div>
          );
        })}
      </div>

      {/* tower */}
      <div style={{position: "absolute", right: 250, bottom: 130, width: 300, height: TOWER_H}}>
        <div style={{position: "absolute", inset: 0, borderRadius: 24, border: `3px dashed ${C.navy}33`}} />
        {segs.map((s) => (
          <div
            key={s.k}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: s.bottom,
              height: s.h,
              background: s.color,
              borderRadius: 4,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: display,
              fontWeight: 800,
              fontSize: 40,
              color: s.color === C.gold ? C.navy : C.white,
              overflow: "hidden",
            }}
          >
            {s.h > 40 ? s.k : ""}
          </div>
        ))}
      </div>

      {/* total */}
      <div
        style={{
          position: "absolute",
          right: 120,
          top: 150,
          width: 640,
          textAlign: "right",
          opacity: totalIn,
          transform: `translateY(${(1 - totalIn) * 40}px) scale(${0.9 + 0.1 * totalIn})`,
          transformOrigin: "right center",
        }}
      >
        <div style={{fontFamily: body, fontWeight: 800, fontSize: 24, letterSpacing: "0.2em", color: C.navy3}}>COVERAGE TARGET</div>
        <div style={{fontFamily: display, fontWeight: 800, fontSize: 118, color: C.navy, lineHeight: 1}}>
          <Count to={TOTAL} start={430} dur={40} prefix="$" />
        </div>
        <div style={{fontFamily: body, fontWeight: 600, fontSize: 28, color: C.coral}}>≈ 15× annual income</div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          bottom: 62,
          fontFamily: body,
          fontSize: 24,
          color: "#4A5878",
          opacity: ease(frame, [440, 470], [0, 1]),
        }}
      >
        Add a care fund for parents, a partner's retirement contributions and ~$10K final expenses as needed. Example only.
      </div>
    </Scene>
  );
};
