import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { LangkahPertama } from "./LangkahPertama";

registerRoot(() => {
  return (
    <Composition
      id="LangkahPertama"
      component={LangkahPertama}
      durationInFrames={900}
      fps={30}
      width={1920}
      height={1080}
    />
  );
});