import React from "react";
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const X0 = 440;
const PX = 46; // px per year
const AGE0 = 34;
const rows = [
  {label: "Mortgage", from: 34, to: 64, color: C.coral, at: 40},
  {label: "Kids at home", from: 34, to: 52, color: C.violet, at: 70},
  {label: "Parents' care years", from: 42, to: 58, color: C.gold, at: 100},
];
const xAt = (age: number) => X0 + (age - AGE0) * PX;

export const Match: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const overlap = ease(frame, [165, 190], [0, 1]);
  const cover = ease(frame, [210, 255], [0, 1]);
  const cards = spring({frame: frame - 270, fps, config: {damping: 15}});
  const sweep = ease(frame, [150, 260], [AGE0, 64], (t) => t);

  return (
    <Scene variant="deep" frames={frames} chapter="05 · THE FIT" accent={C.teal}>
      <div style={{position: "absolute", left: 120, top: 100}}>
        <KineticText
          text="Match the policy to the pressure."
          size={76}
          delay={4}
          highlight={{policy: C.teal}}
        />
      </div>

      {/* axis */}
      <div style={{position: "absolute", left: 0, top: 0}}>
        {[34, 40, 45, 50, 55, 60, 64].map((a) => (
          <React.Fragment key={a}>
            <div style={{position: "absolute", left: xAt(a), top: 300, width: 2, height: 360, background: "rgba(255,255,255,.1)"}} />
            <div style={{position: "absolute", left: xAt(a) - 40, top: 668, width: 80, textAlign: "center", fontFamily: body, fontWeight: 600, fontSize: 24, color: C.mute}}>
              {a}
            </div>
          </React.Fragment>
        ))}
        <div style={{position: "absolute", left: 120, top: 668, whiteSpace: "nowrap", fontFamily: body, fontWeight: 800, fontSize: 22, color: C.mute, letterSpacing: "0.1em"}}>
          YOUR AGE
        </div>
      </div>

      {/* danger zone */}
      <div
        style={{
          position: "absolute",
          left: xAt(34),
          width: (52 - 34) * PX * overlap,
          top: 290,
          height: 285,
          borderRadius: 18,
          background: "repeating-linear-gradient(135deg, rgba(255,107,91,.22) 0 14px, rgba(255,107,91,.07) 14px 28px)",
          border: `2px dashed ${C.coral}`,
          overflow: "hidden",
        }}
      />
      <div style={{position: "absolute", left: xAt(34) + 14, top: 252, fontFamily: body, fontWeight: 800, fontSize: 24, color: C.coral, opacity: overlap, letterSpacing: "0.06em"}}>
        EVERY OBLIGATION AT ONCE
      </div>

      {rows.map((r, i) => {
        const g = ease(frame, [r.at, r.at + 40], [0, 1]);
        return (
          <div key={r.label} style={{position: "absolute", left: 0, top: 305 + i * 92, width: 1920}}>
            <div style={{position: "absolute", left: 120, top: 8, width: 300, fontFamily: body, fontWeight: 800, fontSize: 26, color: C.white, opacity: ease(frame, [r.at, r.at + 15], [0, 1])}}>
              {r.label}
            </div>
            <div
              style={{
                position: "absolute",
                left: xAt(r.from),
                width: (r.to - r.from) * PX * g,
                height: 58,
                borderRadius: 29,
                background: `linear-gradient(90deg, ${r.color}, ${r.color}CC)`,
                boxShadow: `0 0 30px ${r.color}55`,
              }}
            />
          </div>
        );
      })}

      {/* coverage bar */}
      <div style={{position: "absolute", left: 0, top: 303 + 3 * 92 - 4, width: 1920}}>
        <div style={{position: "absolute", left: 120, top: 2, width: 310, fontFamily: body, fontWeight: 800, fontSize: 26, color: C.teal, opacity: cover}}>
          Your term policy
        </div>
        <div
          style={{
            position: "absolute",
            left: xAt(34),
            width: (64 - 34) * PX * cover,
            height: 74,
            borderRadius: 37,
            background: `linear-gradient(90deg, ${C.teal}, #19A090)`,
            boxShadow: `0 0 ${40 + Math.sin(frame / 8) * 12}px ${C.teal}88`,
            display: "flex",
            alignItems: "center",
            paddingLeft: 28,
            fontFamily: display,
            fontWeight: 800,
            fontSize: 36,
            color: C.ink,
            overflow: "hidden",
            whiteSpace: "nowrap",
          }}
        >
          30-year level term · covers the longest obligation
        </div>
      </div>

      {/* sweep line */}
      <div
        style={{
          position: "absolute",
          left: xAt(sweep),
          top: 285,
          width: 3,
          height: 390,
          background: C.white,
          opacity: ease(frame, [150, 160], [0, 0.8]) * ease(frame, [255, 262], [1, 0]),
          boxShadow: `0 0 18px ${C.white}`,
        }}
      />

      {/* term vs permanent */}
      <AbsoluteFill style={{opacity: cards, transform: `translateY(${(1 - cards) * 80}px)`}}>
        {[
          {x: 120, t: "TERM LIFE", c: C.teal, l1: "Pure protection for a set period", l2: "Lowest cost per $ of coverage", l3: "Built for the years of heavy obligations", pick: true},
          {x: 1000, t: "PERMANENT (WHOLE / UNIVERSAL)", c: C.mute, l1: "Lifelong cover + cash value", l2: "Much higher premiums", l3: "Fits estate planning or lifelong needs", pick: false},
        ].map((k) => (
          <div
            key={k.t}
            style={{
              position: "absolute",
              left: k.x,
              top: 770,
              width: 800,
              height: 230,
              borderRadius: 26,
              background: "rgba(255,255,255,.07)",
              border: `2px solid ${k.pick ? C.teal : "rgba(255,255,255,.2)"}`,
              boxShadow: k.pick ? `0 0 50px ${C.teal}44` : "none",
              padding: "26px 34px",
              boxSizing: "border-box",
              fontFamily: body,
              color: C.white,
            }}
          >
            <div style={{fontWeight: 800, fontSize: 24, letterSpacing: "0.14em", color: k.c, marginBottom: 12}}>
              {k.t} {k.pick && <span style={{background: C.teal, color: C.ink, borderRadius: 8, padding: "2px 12px", marginLeft: 10, fontSize: 20}}>FOR MOST FAMILIES</span>}
            </div>
            {[k.l1, k.l2, k.l3].map((l) => (
              <div key={l} style={{fontSize: 28, fontWeight: 600, lineHeight: 1.5}}>
                <span style={{color: k.c}}>● </span>
                {l}
              </div>
            ))}
          </div>
        ))}
      </AbsoluteFill>
    </Scene>
  );
};
