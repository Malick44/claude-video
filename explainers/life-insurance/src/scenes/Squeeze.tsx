import React from "react";
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {Person} from "../components/Person";
import {House} from "../components/House";
import {Count} from "../components/Count";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const Panel: React.FC<{
  x: number;
  w: number;
  delay: number;
  color: string;
  title: string;
  chip: string;
  chipValue: number;
  chipSuffix: string;
  squeeze: number;
  children: React.ReactNode;
}> = ({x, w, delay, color, title, chip, chipValue, chipSuffix, squeeze, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: frame - delay, fps, config: {damping: 15, stiffness: 100}});
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: 250,
        width: w,
        height: 560,
        borderRadius: 36,
        background: "rgba(255,255,255,0.07)",
        border: `2px solid ${color}66`,
        boxShadow: `0 30px 80px rgba(0,0,0,.35), inset 0 0 60px ${color}18`,
        opacity: s,
        transform: `translateY(${(1 - s) * 140}px) translateX(${squeeze}px)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "34px 24px 30px",
        boxSizing: "border-box",
      }}
    >
      <div style={{fontFamily: body, fontWeight: 800, fontSize: 30, letterSpacing: "0.16em", color}}>{title}</div>
      <div style={{display: "flex", alignItems: "flex-end", gap: 8}}>{children}</div>
      <div
        style={{
          fontFamily: body,
          fontWeight: 600,
          fontSize: 28,
          color: C.white,
          background: `${color}26`,
          border: `1.5px solid ${color}`,
          borderRadius: 999,
          padding: "10px 26px",
          opacity: ease(frame, [delay + 30, delay + 45], [0, 1]),
        }}
      >
        {chip}{" "}
        <b style={{color}}>
          <Count to={chipValue} start={delay + 30} dur={30} prefix="$" suffix={chipSuffix} />
        </b>
      </div>
    </div>
  );
};

const Arrow: React.FC<{dir: 1 | -1; x: number; delay: number; color: string}> = ({dir, x, delay, color}) => {
  const frame = useCurrentFrame();
  const o = ease(frame, [delay, delay + 14], [0, 1]);
  const push = ((frame - delay) % 36) / 36;
  return (
    <div style={{position: "absolute", left: x, top: 500, opacity: o, transform: `translateX(${dir * push * 26}px)`}}>
      <svg width="86" height="70" viewBox="0 0 86 70">
        {[0, 1].map((i) => (
          <path
            key={i}
            d={dir === 1 ? `M${14 + i * 28} 10 L${44 + i * 28} 35 L${14 + i * 28} 60` : `M${72 - i * 28} 10 L${42 - i * 28} 35 L${72 - i * 28} 60`}
            stroke={color}
            strokeWidth="9"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
            opacity={1 - i * 0.4}
          />
        ))}
      </svg>
    </div>
  );
};

export const Squeeze: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const pulse = frame > 190 ? Math.sin((frame - 190) / 7) * 0.5 + 0.5 : 0;
  const squeeze = ease(frame, [180, 215], [0, 34]) + pulse * 10;
  const stress = frame > 205;
  const totalIn = ease(frame, [250, 280], [0, 1]);

  return (
    <Scene variant="dark" frames={frames} chapter="01 · THE SQUEEZE">
      <div style={{position: "absolute", top: 108, left: 0, right: 0}}>
        <KineticText
          text="Welcome to the Sandwich Generation."
          size={84}
          delay={8}
          align="center"
          highlight={{Sandwich: C.gold}}
        />
      </div>

      <Panel x={110} w={500} delay={40} color={C.gold} title="AGING PARENTS" chip="Care & help" chipValue={600} chipSuffix="/mo" squeeze={squeeze}>
        <Person kind="elder" shirt="#8FA3C7" phase={0} height={310} />
        <Person kind="elder" shirt="#C9A7D9" hair="#D9DEE8" skin="#E8B890" phase={9} height={290} />
      </Panel>
      <Panel x={710} w={500} delay={60} color={C.coral} title="YOU + THE MORTGAGE" chip="Mortgage" chipValue={2400} chipSuffix="/mo" squeeze={0}>
        <div style={{position: "relative", width: 440, height: 330, display: "flex", justifyContent: "center", alignItems: "flex-end"}}>
          <div style={{position: "absolute", bottom: 4, opacity: 0.9}}>
            <House width={330} glow={0.9} />
          </div>
          <div style={{position: "relative", transform: `scale(${1 - pulse * 0.025}, ${1 + pulse * 0.02})`, transformOrigin: "bottom"}}>
            <Person kind="adult" shirt={C.teal} mood={stress ? "stress" : "happy"} height={300} />
          </div>
        </div>
      </Panel>
      <Panel x={1310} w={500} delay={80} color={C.violet} title="YOUNG KIDS" chip="Childcare" chipValue={1800} chipSuffix="/mo" squeeze={-squeeze}>
        <Person kind="child" shirt={C.coral} hair="#5A3B2A" phase={4} height={310} />
        <Person kind="child" shirt={C.gold} hair="#2A1F1A" skin="#D9A074" phase={14} height={250} />
      </Panel>

      <Arrow dir={1} x={612} delay={190} color={C.gold} />
      <Arrow dir={-1} x={1210} delay={190} color={C.violet} />

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 78,
          textAlign: "center",
          opacity: totalIn,
          transform: `translateY(${(1 - totalIn) * 40}px)`,
        }}
      >
        <span style={{fontFamily: display, fontWeight: 800, fontSize: 86, color: C.white}}>
          <Count to={4800} start={250} dur={40} prefix="$" suffix=" / month" />
        </span>
        <span style={{fontFamily: body, fontWeight: 600, fontSize: 36, color: C.mute, marginLeft: 28}}>
          — riding on <span style={{color: C.gold}}>your income</span>.
        </span>
      </div>
      <div style={{position: "absolute", right: 72, bottom: 24, fontFamily: body, fontSize: 18, color: C.mute, opacity: 0.8}}>
        Illustrative household figures
      </div>
    </Scene>
  );
};
