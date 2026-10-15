import React from "react";
import {useCurrentFrame} from "remotion";

export type PersonProps = {
  kind: "adult" | "elder" | "child";
  shirt: string;
  pants?: string;
  skin?: string;
  hair?: string;
  mood?: "happy" | "stress";
  height?: number;
  phase?: number;
};

/** Flat vector character. viewBox 200x320, feet at y=300. */
export const Person: React.FC<PersonProps> = ({
  kind,
  shirt,
  pants = "#26334F",
  skin = "#F2C29B",
  hair = "#2A1F1A",
  mood = "happy",
  height = 300,
  phase = 0,
}) => {
  const frame = useCurrentFrame();
  const bob = Math.sin((frame + phase) / 14) * 3;
  const blink = (frame + phase * 3) % 120 < 5;
  const child = kind === "child";
  const elder = kind === "elder";
  const headR = child ? 34 : 29;
  const headY = child ? 118 : 68;
  const hairC = elder ? "#D9DEE8" : hair;

  const body = (
    <g transform={child ? "translate(100 300) scale(.66) translate(-100 -300)" : undefined}>
      <g transform={`translate(0 ${bob})`}>
        <g transform={elder ? "rotate(4 100 300)" : undefined}>
          {/* legs */}
          <rect x="72" y="190" width="24" height="110" rx="10" fill={pants} />
          <rect x="104" y="190" width="24" height="110" rx="10" fill={pants} />
          <rect x="66" y="288" width="34" height="14" rx="7" fill="#0F1A33" />
          <rect x="100" y="288" width="34" height="14" rx="7" fill="#0F1A33" />
          {/* arms */}
          <rect x="50" y="102" width="20" height="92" rx="10" fill={shirt} transform="rotate(8 60 104)" />
          <rect x="130" y="102" width="20" height="92" rx="10" fill={shirt} transform="rotate(-8 140 104)" />
          <circle cx="53" cy="196" r="10" fill={skin} />
          <circle cx="147" cy="196" r="10" fill={skin} />
          {/* torso */}
          <rect x="64" y="92" width="72" height="112" rx="32" fill={shirt} />
          {/* neck + head */}
          <rect x="91" y="84" width="18" height="20" rx="8" fill={skin} />
          <circle cx="100" cy={headY - (child ? 30 : 0)} r={headR} fill={skin} />
          {/* hair */}
          {kind === "adult" && (
            <path
              d={`M${100 - headR} ${headY - 4} C${100 - headR} ${headY - 42} ${100 + headR} ${headY - 42} ${100 + headR} ${headY - 4} C${100 + 14} ${headY - 22} ${100 - 14} ${headY - 22} ${100 - headR} ${headY - 4}Z`}
              fill={hairC}
            />
          )}
          {elder && (
            <>
              <path
                d={`M${100 - headR} ${headY - 2} C${100 - headR} ${headY - 40} ${100 + headR} ${headY - 40} ${100 + headR} ${headY - 2} C${100 + 16} ${headY - 20} ${100 - 16} ${headY - 20} ${100 - headR} ${headY - 2}Z`}
                fill={hairC}
              />
              <circle cx="90" cy={headY} r="8" fill="none" stroke="#4A5878" strokeWidth="2.5" />
              <circle cx="110" cy={headY} r="8" fill="none" stroke="#4A5878" strokeWidth="2.5" />
              <line x1="98" y1={headY} x2="102" y2={headY} stroke="#4A5878" strokeWidth="2.5" />
            </>
          )}
          {child && (
            <path
              d={`M${100 - headR} ${headY - 34} C${100 - headR} ${headY - 74} ${100 + headR} ${headY - 74} ${100 + headR} ${headY - 34} C${100 + 12} ${headY - 54} ${100 - 12} ${headY - 54} ${100 - headR} ${headY - 34}Z`}
              fill={hairC}
            />
          )}
          {/* face */}
          {(() => {
            const fy = child ? headY - 30 : headY;
            return (
              <>
                {!elder &&
                  (blink ? (
                    <>
                      <line x1="88" y1={fy} x2="96" y2={fy} stroke="#2A1F1A" strokeWidth="3" strokeLinecap="round" />
                      <line x1="104" y1={fy} x2="112" y2={fy} stroke="#2A1F1A" strokeWidth="3" strokeLinecap="round" />
                    </>
                  ) : (
                    <>
                      <circle cx="91" cy={fy} r="3.6" fill="#2A1F1A" />
                      <circle cx="109" cy={fy} r="3.6" fill="#2A1F1A" />
                    </>
                  ))}
                {elder && (
                  <>
                    <circle cx="90" cy={fy} r="2.6" fill="#2A1F1A" />
                    <circle cx="110" cy={fy} r="2.6" fill="#2A1F1A" />
                  </>
                )}
                {mood === "happy" ? (
                  <path d={`M91 ${fy + 14} Q100 ${fy + 22} 109 ${fy + 14}`} stroke="#2A1F1A" strokeWidth="3" fill="none" strokeLinecap="round" />
                ) : (
                  <path d={`M91 ${fy + 19} Q100 ${fy + 11} 109 ${fy + 19}`} stroke="#2A1F1A" strokeWidth="3" fill="none" strokeLinecap="round" />
                )}
                {mood === "stress" && (
                  <path
                    d={`M${100 + headR - 2} ${fy - 20 + ((frame + phase) % 40) * 0.5} q5 9 0 13 q-5 -4 0 -13z`}
                    fill="#7EC8FF"
                    opacity={0.9}
                  />
                )}
                {kind === "child" && <circle cx="82" cy={fy + 10} r="5" fill="#FF9C8F" opacity=".5" />}
              </>
            );
          })()}
          {elder && (
            <>
              <path d="M158 196 L158 300" stroke="#8A6A4A" strokeWidth="6" strokeLinecap="round" />
              <path d="M158 196 q0 -14 -14 -14" stroke="#8A6A4A" strokeWidth="6" fill="none" strokeLinecap="round" />
            </>
          )}
        </g>
      </g>
    </g>
  );

  return (
    <svg viewBox="0 0 200 320" height={height} width={(height * 200) / 320} style={{overflow: "visible"}}>
      {body}
    </svg>
  );
};
