import React from "react";
import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import {Scene} from "../components/Scene";
import {KineticText} from "../components/KineticText";
import {Count} from "../components/Count";
import {ease} from "../anim";
import {C, body, display} from "../theme";

const STOP = 140;
const BILLS = [
  {n: "Mortgage", v: 2400, c: C.coral},
  {n: "Childcare", v: 1800, c: C.violet},
  {n: "Parents' care", v: 600, c: C.gold},
];

export const Paycheck: React.FC<{frames: number}> = ({frames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const stopped = frame >= STOP;
  const pc = spring({frame, fps, config: {damping: 14}});
  const flicker = frame > STOP - 6 && frame < STOP + 10 ? (frame % 3 === 0 ? 0.2 : 1) : 1;

  // coins travel along the conveyor until the paycheck stops
  const coins = new Array(14).fill(0).map((_, i) => {
    const speed = 5.2;
    const birth = i * 9;
    const t = (frame - birth) * speed;
    if (birth > STOP || t < 0 || t > 640) return null;
    if (stopped && birth + 640 / speed < STOP) return null;
    return {x: t, i};
  });

  const unpaid = ease(frame, [STOP, STOP + 160], [0, 14400], (t) => t);
  const runway = 1 - ease(frame, [STOP + 10, STOP + 190], [0, 1], (t) => t);
  const out = frame > STOP + 190;
  const end = ease(frame, [STOP + 200, STOP + 230], [0, 1]);

  return (
    <Scene variant="deep" frames={frames} chapter="02 · THE RISK" accent={C.coral}>
      <div style={{position: "absolute", top: 120, left: 0, right: 0}}>
        <KineticText
          text="Now imagine the paycheck stops."
          size={92}
          delay={6}
          align="center"
          highlight={{stops: C.coral}}
        />
      </div>

      {/* paycheck card */}
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 420,
          width: 400,
          height: 250,
          borderRadius: 28,
          background: stopped ? "#2A2F40" : `linear-gradient(135deg, ${C.teal}, #0E8F86)`,
          boxShadow: stopped ? "none" : `0 0 70px ${C.teal}66`,
          opacity: pc * flicker,
          transform: `translateY(${(1 - pc) * 80}px) rotate(${stopped ? -2 : 0}deg)`,
          padding: 30,
          boxSizing: "border-box",
          fontFamily: body,
          color: C.white,
        }}
      >
        <div style={{fontWeight: 800, letterSpacing: "0.18em", fontSize: 22, opacity: 0.85}}>PAYCHECK</div>
        <div style={{fontFamily: display, fontWeight: 800, fontSize: 96, marginTop: 14}}>
          {stopped ? "$0" : "$7,100"}
        </div>
        <div style={{fontSize: 24, opacity: 0.75}}>{stopped ? "income stopped" : "household / month"}</div>
      </div>

      {/* conveyor */}
      <div style={{position: "absolute", left: 540, top: 545, width: 640, height: 6, background: "rgba(255,255,255,.18)", borderRadius: 3}} />
      {coins.map(
        (c) =>
          c && (
            <div
              key={c.i}
              style={{
                position: "absolute",
                left: 540 + c.x - 24,
                top: 521,
                width: 48,
                height: 48,
                borderRadius: 24,
                background: C.gold,
                color: "#7A5A00",
                fontFamily: display,
                fontWeight: 800,
                fontSize: 28,
                textAlign: "center",
                lineHeight: "48px",
                boxShadow: `0 0 20px ${C.gold}99`,
                opacity: ease(c.x, [560, 640], [1, 0]),
              }}
            >
              $
            </div>
          ),
      )}

      {/* bills */}
      {BILLS.map((b, i) => {
        const s = spring({frame: frame - 30 - i * 10, fps, config: {damping: 14}});
        const shake = stopped ? Math.sin((frame + i * 9) * 1.4) * 2.2 : 0;
        return (
          <div
            key={b.n}
            style={{
              position: "absolute",
              left: 1210,
              top: 360 + i * 120,
              width: 580,
              height: 98,
              borderRadius: 22,
              background: "rgba(255,255,255,.08)",
              border: `2px solid ${stopped ? C.coral : b.c}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0 30px",
              boxSizing: "border-box",
              fontFamily: body,
              fontWeight: 800,
              fontSize: 32,
              color: C.white,
              opacity: s,
              transform: `translateX(${(1 - s) * 200 + shake}px)`,
            }}
          >
            <span style={{color: b.c}}>{b.n}</span>
            <span>
              ${b.v.toLocaleString()}
              <span style={{opacity: 0.6, fontSize: 24, fontWeight: 600}}> /mo</span>
            </span>
          </div>
        );
      })}

      {/* runway */}
      <div
        style={{
          position: "absolute",
          left: 120,
          right: 130,
          bottom: 150,
          opacity: ease(frame, [STOP + 4, STOP + 24], [0, 1]),
        }}
      >
        <div style={{display: "flex", justifyContent: "space-between", fontFamily: body, fontWeight: 800, fontSize: 28, color: C.white, marginBottom: 14}}>
          <span>
            Emergency fund <span style={{color: C.mute, fontWeight: 600}}>(3 months of expenses)</span>
          </span>
          <span style={{color: C.coral}}>
            Unpaid bills: <Count to={14400} start={STOP} dur={160} prefix="$" />
          </span>
        </div>
        <div style={{height: 34, borderRadius: 17, background: "rgba(255,255,255,.12)", overflow: "hidden"}}>
          <div
            style={{
              width: `${runway * 100}%`,
              height: "100%",
              borderRadius: 17,
              background: runway > 0.4 ? C.gold : C.coral,
              boxShadow: `0 0 24px ${runway > 0.4 ? C.gold : C.coral}`,
            }}
          />
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 44,
          textAlign: "center",
          fontFamily: display,
          fontWeight: 800,
          fontSize: 54,
          color: C.white,
          opacity: end,
          transform: `translateY(${(1 - end) * 30}px)`,
        }}
      >
        Savings buy <span style={{color: C.gold}}>months</span>. Your family needs <span style={{color: C.teal}}>decades</span>.
      </div>
      {out && <div style={{position: "absolute", inset: 0, background: "rgba(255,107,91,0.05)"}} />}
    </Scene>
  );
};
