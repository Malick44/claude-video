import React from "react";
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {TransitionSeries, linearTiming} from "@remotion/transitions";
import {fade} from "@remotion/transitions/fade";
import {slide} from "@remotion/transitions/slide";
import {wipe} from "@remotion/transitions/wipe";
import {flip} from "@remotion/transitions/flip";
import {clockWipe} from "@remotion/transitions/clock-wipe";
import {C, SCENES, TOTAL_FRAMES, TRANSITION} from "./theme";
import {Hook} from "./scenes/Hook";
import {Squeeze} from "./scenes/Squeeze";
import {Paycheck} from "./scenes/Paycheck";
import {Dime} from "./scenes/Dime";
import {Cost} from "./scenes/Cost";
import {Match} from "./scenes/Match";
import {Myths} from "./scenes/Myths";
import {Steps} from "./scenes/Steps";
import {Close} from "./scenes/Close";

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
      <Audio src={staticFile("score.mp3")} />
      <div style={{position: "absolute", left: 0, bottom: 0, height: 6, width: `${(frame / TOTAL_FRAMES) * 100}%`, background: `linear-gradient(90deg, ${C.teal}, ${C.gold})`}} />
    </AbsoluteFill>
  );
};
