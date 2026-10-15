import React from "react";
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {interpolatePath} from "@remotion/paths";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {Person} from "../components/Person";
import {HOUSE_PATH, SHIELD_PATH} from "../components/House";
import {ease, INOUT} from "../anim";
import {C, body, display} from "../theme";

export const Close: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const morph = ease(frame, [60, 120], [0, 1], INOUT);
  const d = interpolatePath(morph, HOUSE_PATH, SHIELD_PATH);
  const pop = spring({frame: frame - 6, fps, config: {damping: 12, stiffness: 90}});
  const fam = ease(frame, [30, 60], [0, 1]);
  const check = ease(frame, [125, 150], [0, 1]);
  const cta = spring({frame: frame - 220, fps, config: {damping: 13}});
  const fillCol = morph < 0.5 ? "#EADFCB" : C.teal;

  return (
    <Scene variant="deep" frames={frames} accent={C.teal} push={0.03}>
      {/* rotating light rays */}
      <AbsoluteFill
        style={{
          background: `repeating-conic-gradient(from ${frame * 0.4}deg at 500px 500px, ${C.teal}22 0deg 8deg, transparent 8deg 24deg)`,
          maskImage: "radial-gradient(circle at 500px 500px, black 0%, transparent 55%)",
          WebkitMaskImage: "radial-gradient(circle at 500px 500px, black 0%, transparent 55%)",
          opacity: morph,
        }}
      />
      <div style={{position: "absolute", left: 160, top: 150, transform: `scale(${pop})`}}>
        <svg viewBox="0 0 400 360" width={680} height={612} style={{overflow: "visible"}}>
          <path
            d={d}
            fill={fillCol}
            fillOpacity={morph < 0.5 ? 1 : 0.22 + 0.5 * (1 - check)}
            stroke={C.teal}
            strokeWidth={morph * 9}
            strokeLinejoin="round"
            style={{filter: `drop-shadow(0 0 ${morph * 34}px ${C.teal})`}}
          />
          <polyline
            points="150,118 185,152 252,84"
            fill="none"
            stroke={C.white}
            strokeWidth="14"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={260}
            strokeDashoffset={260 * (1 - check)}
            opacity={0.95}
          />
        </svg>
        <div style={{position: "absolute", left: 100, top: 330, display: "flex", opacity: fam * (1 - morph * 0.0), gap: 0}}>
          <div style={{transform: "translateX(40px)"}}><Person kind="elder" shirt="#8FA3C7" height={170} phase={0} /></div>
          <Person kind="adult" shirt={C.teal} height={190} phase={5} />
          <div style={{transform: "translateX(-30px)"}}><Person kind="adult" shirt={C.gold} hair="#5A3B2A" height={185} phase={11} /></div>
          <div style={{transform: "translateX(-50px)"}}><Person kind="child" shirt={C.coral} height={190} phase={17} /></div>
        </div>
      </div>

      <div style={{position: "absolute", left: 960, top: 150, width: 840}}>
        <KineticText text="Protect the people" size={92} delay={110} />
        <KineticText text="who depend on you." size={92} delay={126} color={C.teal} />
        <div style={{height: 34}} />
        <KineticText text="The best time was before the mortgage." size={40} delay={160} color={C.mute} weight={600} family={body} style={{whiteSpace: "nowrap"}} />
        <KineticText text="The next best time is this week." size={46} delay={190} color={C.gold} family={body} />
      </div>

      <div
        style={{
          position: "absolute",
          left: 960,
          top: 720,
          whiteSpace: "nowrap",
          display: "flex",
          gap: 14,
          alignItems: "center",
          opacity: cta,
          transform: `translateY(${(1 - cta) * 50}px)`,
          fontFamily: body,
          fontWeight: 800,
          fontSize: 26,
        }}
      >
        {["Get your number", "Get quotes", "Name beneficiaries"].map((t, i) => (
          <React.Fragment key={t}>
            <div style={{background: i === 0 ? C.teal : "rgba(255,255,255,.1)", color: i === 0 ? C.ink : C.white, border: `2px solid ${C.teal}`, borderRadius: 999, padding: "14px 26px"}}>{t}</div>
            {i < 2 && <span style={{color: C.mute}}>→</span>}
          </React.Fragment>
        ))}
      </div>

      <div
        style={{
          position: "absolute",
          left: 120,
          right: 120,
          bottom: 40,
          textAlign: "center",
          fontFamily: body,
          fontSize: 19,
          lineHeight: 1.45,
          color: C.mute,
          opacity: ease(frame, [240, 270], [0, 0.9]),
        }}
      >
        Educational content only. Not financial, tax or insurance advice. Figures are illustrative; actual rates and needs vary by age, health, insurer and state. Consult a licensed professional.
      </div>
      <div style={{position: "absolute", right: 72, top: 52, fontFamily: display, fontWeight: 800, fontSize: 26, color: C.white, opacity: 0.0}}>.</div>
    </Scene>
  );
};
