import React from "react";
import {Composition} from "remotion";
import {Explainer} from "./Explainer";
import {FPS, TOTAL_FRAMES} from "./theme";

export const Root: React.FC = () => (
  <Composition
    id="Explainer"
    component={Explainer}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
