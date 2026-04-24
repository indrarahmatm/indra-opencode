import { useCurrentFrame, useVideoConfig, interpolate, spring, AbsoluteFill, Sequence } from "remotion";

const Footprint: React.FC<{ x: number; y: number; delay: number; flip?: boolean }> = ({ x, y, delay, flip }) => {
  const frame = useCurrentFrame();
  const progress = Math.max(0, frame - delay);
  const scale = spring({ frame: progress, fps: 30, config: { damping: 10, stiffness: 90 } });
  const opacity = interpolate(scale, [0, 0.5, 1], [0, 0, 1]);

  return (
    <svg
      width="40"
      height="60"
      viewBox="0 0 40 60"
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `scale(${scale}) rotate(${flip ? 15 : -15}deg)`,
        opacity,
      }}
    >
      <ellipse cx="20" cy="45" rx="12" ry="15" fill="#d4a5a5" opacity="0.6" />
      <circle cx="8" cy="12" r="6" fill="#d4a5a5" opacity="0.6" />
      <circle cx="20" cy="6" r="6" fill="#d4a5a5" opacity="0.6" />
      <circle cx="32" cy="12" r="6" fill="#d4a5a5" opacity="0.6" />
      <circle cx="14" cy="22" r="5" fill="#d4a5a5" opacity="0.6" />
      <circle cx="26" cy="22" r="5" fill="#d4a5a5" opacity="0.6" />
    </svg>
  );
};

const AnimatedCircleFrame: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rotate = interpolate(frame, [0, fps * 30], [0, 360]);

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        transform: "translate(-50%, -50%)",
        width: "500px",
        height: "500px",
        borderRadius: "50%",
        overflow: "hidden",
        boxShadow: "0 0 60px rgba(255, 182, 193, 0.5)",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "linear-gradient(135deg, #ffe4e1 0%, #fff0f5 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            color: "#b08080",
            fontSize: "24px",
            fontFamily: "cursive",
            textAlign: "center",
            opacity: 0.7,
          }}
        >
          [Video Clip]<br />Anak Belajar Berjalan
        </div>
      </div>

      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          transform: `rotate(${rotate}deg)`,
        }}
      >
        <circle
          cx="250"
          cy="250"
          r="245"
          fill="none"
          stroke="url(#borderGradient)"
          strokeWidth="8"
          strokeDasharray="20 10"
        />
        <defs>
          <linearGradient id="borderGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffb6c1" />
            <stop offset="50%" stopColor="#ffc0cb" />
            <stop offset="100%" stopColor="#ffd1dc" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const bounce = spring({ frame, fps, config: { damping: 8, stiffness: 60 } });
  const scale = interpolate(bounce, [0, 1], [0.5, 1]);
  const opacity = interpolate(bounce, [0, 1], [0, 1]);
  const yOffset = interpolate(bounce, [0, 1], [-50, 0]);

  const subtitleBounce = spring({ frame: frame - 40, fps, config: { damping: 10, stiffness: 70 } });
  const subtitleOpacity = interpolate(subtitleBounce, [0, 1], [0, 1]);

  return (
    <div
      style={{
        position: "absolute",
        top: "15%",
        left: "50%",
        transform: `translateX(-50%) translateY(${yOffset}px) scale(${scale})`,
        opacity,
        textAlign: "center",
      }}
    >
      <h1
        style={{
          color: "#8b5a5a",
          fontSize: "80px",
          fontFamily: "'Comic Sans MS', 'Segoe UI', cursive",
          fontWeight: "bold",
          textShadow: "2px 2px 4px rgba(0,0,0,0.1)",
          margin: 0,
        }}
      >
        Langkah Pertama Adek!
      </h1>
      <p
        style={{
          color: "#a08080",
          fontSize: "28px",
          fontFamily: "'Segoe UI', sans-serif",
          marginTop: "10px",
          opacity: subtitleOpacity,
        }}
      >
        Momen berharga si kecil
      </p>
    </div>
  );
};

const FootprintsPath: React.FC = () => {
  const footprints = [
    { x: 20, y: 70, delay: 60 },
    { x: 25, y: 75, delay: 90 },
    { x: 30, y: 72, delay: 120, flip: true },
    { x: 35, y: 68, delay: 150 },
    { x: 40, y: 70, delay: 180, flip: true },
    { x: 45, y: 73, delay: 210 },
    { x: 50, y: 75, delay: 240, flip: true },
    { x: 55, y: 72, delay: 270 },
    { x: 60, y: 70, delay: 300, flip: true },
    { x: 65, y: 73, delay: 330 },
    { x: 70, y: 75, delay: 360, flip: true },
    { x: 75, y: 72, delay: 390 },
    { x: 80, y: 70, delay: 420, flip: true },
    { x: 85, y: 68, delay: 450 },
  ];

  return (
    <>
      {footprints.map((fp, i) => (
        <Footprint key={i} x={fp.x} y={fp.y} delay={fp.delay} flip={fp.flip} />
      ))}
    </>
  );
};

export const LangkahPertama: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #fff5f5 0%, #ffe4e1 50%, #fff0f5 100%)",
      }}
    >
      <Title />
      <AnimatedCircleFrame />
      <FootprintsPath />
    </AbsoluteFill>
  );
};