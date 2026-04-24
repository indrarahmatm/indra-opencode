import { useCurrentFrame, useVideoConfig, interpolate, spring, AbsoluteFill } from "remotion";

const Particle: React.FC<{ x: number; y: number; delay: number; size: number }> = ({ x, y, delay, size }) => {
  const frame = useCurrentFrame();
  const progress = Math.max(0, frame - delay);
  const opacity = interpolate(progress, [0, 60], [0, 0.6], { extrapolateRight: "clamp" });
  const floatY = Math.sin(progress * 0.05) * 20;

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y + floatY}%`,
        width: size,
        height: size,
        borderRadius: "50%",
        background: "rgba(255, 255, 255, 0.8)",
        opacity,
      }}
    />
  );
};

const CodeFlowTitle: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bounce = spring({ frame, fps, config: { damping: 8, stiffness: 80 } });
  const scale = interpolate(bounce, [0, 1], [0.3, 1]);
  const opacity = interpolate(bounce, [0, 1], [0, 1]);
  const glow = interpolate(frame, [0, 90], [0, 20], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <h1
        style={{
          color: "#e94560",
          fontSize: "140px",
          fontFamily: "'Poppins', 'Arial Black', sans-serif",
          fontWeight: 900,
          textShadow: `0 0 ${glow}px #e94560, 0 0 ${glow * 2}px #e94560`,
          transform: `scale(${scale})`,
          opacity,
          letterSpacing: "8px",
          margin: 0,
        }}
      >
        CodeFlow
      </h1>
      <p
        style={{
          color: "rgba(255, 255, 255, 0.7)",
          fontSize: "32px",
          fontFamily: "'Poppins', sans-serif",
          fontWeight: 300,
          opacity: interpolate(bounce, [0.8, 1], [0, 1]),
          marginTop: "20px",
          letterSpacing: "12px",
          textTransform: "uppercase",
        }}
      >
        Code • Create • Ship
      </p>
    </div>
  );
};

export const CodeFlowIntro: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {[...Array(30)].map((_, i) => (
        <Particle
          key={i}
          x={Math.random() * 100}
          y={Math.random() * 100}
          delay={Math.random() * 30}
          size={Math.random() * 4 + 2}
        />
      ))}
      <CodeFlowTitle />
    </AbsoluteFill>
  );
};