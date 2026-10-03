import React from "react";
import {AbsoluteFill, Audio, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {TransitionSeries, linearTiming} from "@remotion/transitions";
import {fade} from "@remotion/transitions/fade";
import {slide} from "@remotion/transitions/slide";
import {wipe} from "@remotion/transitions/wipe";
import {flip} from "@remotion/transitions/flip";
import {clockWipe} from "@remotion/transitions/clock-wipe";
import {C, SCENES, TOTAL_FRAMES, TRANSITION} from "./theme";
import cues from "./vo.json";
import {Hook} from "./scenes/Hook";
import {Squeeze} from "./scenes/Squeeze";
import {Paycheck} from "./scenes/Paycheck";
import {Dime} from "./scenes/Dime";
import {Cost} from "./scenes/Cost";
import {Match} from "./scenes/Match";
import {Myths} from "./scenes/Myths";
import {Steps} from "./scenes/Steps";
import {Close} from "./scenes/Close";

// Music ducks under the narration: ramp down 8 frames before a line, back up 14 frames after.
const MUSIC = 0.8;
const DUCKED = 0.36;
const musicVolume = (frame: number) => {
  let duck = 0;
  for (const c of cues) {
    const d = Math.min(
      interpolate(frame, [c.start - 8, c.start], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}),
      interpolate(frame, [c.end, c.end + 14], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}),
    );
    duck = Math.max(duck, d);
  }
  return MUSIC + (DUCKED - MUSIC) * duck;
};

const f = (id: string) => SCENES.find((s) => s.id === id)!.frames;

export const Explainer: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const t = linearTiming({durationInFrames: TRANSITION});

  const pres = [
    slide({direction: "from-bottom"}),
    fade(),
    wipe({direction: "from-left"}),
    slide({direction: "from-right"}),
    clockWipe({width, height}),
    flip(),
    wipe({direction: "from-top"}),
    fade(),
  ];

  const scenes = [
    <Hook frames={f("hook")} />,
    <Squeeze frames={f("squeeze")} />,
    <Paycheck frames={f("paycheck")} />,
    <Dime frames={f("dime")} />,
    <Cost frames={f("cost")} />,
    <Match frames={f("match")} />,
    <Myths frames={f("myths")} />,
    <Steps frames={f("steps")} />,
    <Close frames={f("close")} />,
  ];

  return (
    <AbsoluteFill style={{background: C.ink}}>
      <TransitionSeries>
        {scenes.flatMap((s, i) => {
          const out = [
            <TransitionSeries.Sequence key={`s${i}`} durationInFrames={SCENES[i].frames}>
              {s}
            </TransitionSeries.Sequence>,
          ];
          if (i < pres.length) {
            out.push(<TransitionSeries.Transition key={`t${i}`} presentation={pres[i] as any} timing={t} />);
          }
          return out;
        })}
      </TransitionSeries>
      <Audio src={staticFile("score.mp3")} volume={musicVolume} />
      <Audio src={staticFile("vo.mp3")} volume={1} />
      <div style={{position: "absolute", left: 0, bottom: 0, height: 6, width: `${(frame / TOTAL_FRAMES) * 100}%`, background: `linear-gradient(90deg, ${C.teal}, ${C.gold})`}} />
    </AbsoluteFill>
  );
};
