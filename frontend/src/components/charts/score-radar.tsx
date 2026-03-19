"use client";

interface ScoreRadarProps {
  technical: number;
  momentum: number;
  ai: number;
  leadership: number;
  departure: number;
  size?: number;
}

export function ScoreRadar({
  technical,
  momentum,
  ai,
  leadership,
  departure,
  size = 160,
}: ScoreRadarProps) {
  const center = size / 2;
  const radius = (size / 2) * 0.75;
  const dims = [
    { label: "Tech", value: technical, angle: -90 },
    { label: "Momentum", value: momentum, angle: -18 },
    { label: "AI", value: ai, angle: 54 },
    { label: "Lead", value: leadership, angle: 126 },
    { label: "Depart", value: departure, angle: 198 },
  ];

  function polarToCart(angle: number, r: number) {
    const rad = (angle * Math.PI) / 180;
    return {
      x: center + r * Math.cos(rad),
      y: center + r * Math.sin(rad),
    };
  }

  // Background grid rings
  const rings = [0.25, 0.5, 0.75, 1.0];

  // Data polygon
  const dataPoints = dims
    .map((d) => {
      const p = polarToCart(d.angle, radius * (d.value || 0));
      return `${p.x},${p.y}`;
    })
    .join(" ");

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Grid rings */}
      {rings.map((r) => (
        <polygon
          key={r}
          points={dims
            .map((d) => {
              const p = polarToCart(d.angle, radius * r);
              return `${p.x},${p.y}`;
            })
            .join(" ")}
          fill="none"
          stroke="#e9ecef"
          strokeWidth="1"
        />
      ))}

      {/* Axis lines */}
      {dims.map((d) => {
        const p = polarToCart(d.angle, radius);
        return (
          <line
            key={d.label}
            x1={center}
            y1={center}
            x2={p.x}
            y2={p.y}
            stroke="#e9ecef"
            strokeWidth="1"
          />
        );
      })}

      {/* Data polygon */}
      <polygon
        points={dataPoints}
        fill="rgba(92, 124, 250, 0.15)"
        stroke="#5c7cfa"
        strokeWidth="2"
      />

      {/* Data points */}
      {dims.map((d) => {
        const p = polarToCart(d.angle, radius * (d.value || 0));
        return (
          <circle
            key={d.label}
            cx={p.x}
            cy={p.y}
            r="3"
            fill="#5c7cfa"
          />
        );
      })}

      {/* Labels */}
      {dims.map((d) => {
        const p = polarToCart(d.angle, radius + 16);
        return (
          <text
            key={d.label}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-[9px] fill-gray-500"
          >
            {d.label}
          </text>
        );
      })}
    </svg>
  );
}
