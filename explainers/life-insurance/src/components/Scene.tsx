import React from "react";
import {AbsoluteFill, useCurrentFrame} from "remotion";
import {Background, Variant} from "./Background";
import {ease} from "../anim";
import {C, body} from "../theme";

/** Scene shell: background, slow camera push-in, chapter tag. */
export const Scene: React.FC<{
  variant?: Variant;
  frames: number;
  chapter?: string;
  push?: number;
  accent?: string;
  children: React.ReactNode;
}> = ({variant = "dark", frames, chapter, push = 0.05, accent, children}) => {
  const frame = useCurrentFrame();
  const light = variant === "light";
  const zoom = 1 + ease(frame, [0, frames], [0, push], (t) => t);
  const tag = ease(frame, [4, 24], [0, 1]);
  return (
    <AbsoluteFill>
      <Background variant={variant} accent={accent} />
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>{children}</AbsoluteFill>
      {chapter && (
        <div
          style={{
            position: "absolute",
            left: 72,
            top: 52,
            fontFamily: body,
            fontWeight: 800,
            fontSize: 22,
            letterSpacing: "0.28em",
            color: light ? C.navy3 : C.mute,
            opacity: tag,
            transform: `translateX(${(1 - tag) * -30}px)`,
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <span style={{display: "inline-block", width: 44 * tag, height: 3, background: light ? C.coral : C.gold}} />
          {chapter}
        </div>
      )}
    </AbsoluteFill>
  );
};
