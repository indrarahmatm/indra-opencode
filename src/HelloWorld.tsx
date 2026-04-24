import { useVideoConfig, Sequence, interpolate, useCurrentFrame, spring } from "remotion";

export const HelloWorld: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const titleProgress = spring({ frame, fps, config: { damping: 10 } });
  const scale = interpolate(titleProgress, [0, 1], [0.5, 1]);
  const opacity = interpolate(titleProgress, [0, 1], [0, 1]);

  const subtitleProgress = spring({
    frame: frame - 30,
    fps,
    config: { damping: 10 },
  });
  const subtitleOpacity = interpolate(subtitleProgress, [0, 1], [0, 1]);

  const barProgress = interpolate(frame - 60, [0, 90], [0, 1]);

  return (
    <div
      style={{
        flex: 1,
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Sequence name="Title" from={0}>
        <h1
          style={{
            color: "white",
            fontSize: "120px",
            fontFamily: "Arial",
            textAlign: "center",
            transform: `scale(${scale})`,
            opacity,
          }}
        >
          Hello World
        </h1>
      </Sequence>

      <Sequence name="Subtitle" from={30}>
        <p
          style={{
            color: "rgba(255,255,255,0.8)",
            fontSize: "48px",
            fontFamily: "Arial",
            marginTop: "20px",
            opacity: subtitleOpacity,
          }}
        >
          Made with Remotion
        </p>
      </Sequence>

      <Sequence name="ProgressBar" from={60}>
        <div
          style={{
            width: "600px",
            height: "20px",
            background: "rgba(255,255,255,0.3)",
            borderRadius: "10px",
            marginTop: "40px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${barProgress * 600}px`,
              height: "100%",
              background: "white",
              borderRadius: "10px",
            }}
          />
        </div>
      </Sequence>
    </div>
  );
};