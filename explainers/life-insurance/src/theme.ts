import {continueRender, delayRender, staticFile} from "remotion";
import timeline from "./timeline.json";

export const C = {
  navy: "#0B1B3A",
  navy2: "#14284F",
  navy3: "#1D3768",
  cream: "#F7F1E6",
  cream2: "#EDE4D3",
  ink: "#0A1428",
  coral: "#FF6B5B",
  teal: "#22C3B0",
  gold: "#FFC857",
  violet: "#8B7CF6",
  white: "#FFFFFF",
  mute: "#93A8CE",
};

// Fonts are vendored in public/fonts (variable woff2, latin subset) so renders work offline.
const FALLBACK = "'DejaVu Serif', Georgia, serif";
export const display = `Fraunces, ${FALLBACK}`;
export const body = "Inter, 'DejaVu Sans', Helvetica, Arial, sans-serif";

if (typeof document !== "undefined") {
  const handle = delayRender("fonts");
  Promise.all(
    [
      ["Fraunces", "Fraunces-latin.woff2", "100 900"],
      ["Inter", "Inter-latin.woff2", "100 900"],
    ].map(async ([name, file, weight]) => {
      const face = new FontFace(name, `url(${staticFile("fonts/" + file)}) format("woff2")`, {weight});
      await face.load();
      document.fonts.add(face);
    }),
  )
    .catch((e) => console.error("font load failed", e))
    .finally(() => continueRender(handle));
}

export const FPS = timeline.fps;
export const TRANSITION = timeline.transition;
export const SCENES = timeline.scenes;
export const TOTAL_FRAMES =
  SCENES.reduce((a, s) => a + s.frames, 0) - TRANSITION * (SCENES.length - 1);
