// Original illustrated Collegiate Gothic scenes (no photos, no real logos).
// Used as the fallback for hero and campus photo slots until real photos are added.
import type { ReactNode } from "react";
import type { SceneKind, Tone } from "../campusPhotos.ts";

type Palette = { sky: [string, string, string]; glow: string; stone: string; stoneFar: string; window: string; tree: string; ground: string };

const PALETTES: Record<Tone, Palette> = {
  dusk:   { sky: ["#0b1d3f", "#3b3f75", "#e59a6a"], glow: "#ffcf8a", stone: "#1a2238", stoneFar: "#39406b", window: "#ffd27a", tree: "#121a2e", ground: "#141c30" },
  autumn: { sky: ["#f3d9a6", "#e9b47c", "#c8734a"], glow: "#fff1c9", stone: "#5b4636", stoneFar: "#a0785a", window: "#ffe2a0", tree: "#8a3b1c", ground: "#6b4a2b" },
  stone:  { sky: ["#dfe6ef", "#c7d2df", "#aebbcb"], glow: "#ffffff", stone: "#6c6f78", stoneFar: "#9aa2ae", window: "#f6e2b0", tree: "#3f5a45", ground: "#7b8a76" },
  snow:   { sky: ["#c9d6e8", "#e8eef6", "#f7f9fc"], glow: "#ffffff", stone: "#4b5568", stoneFar: "#8a95a8", window: "#ffe3a3", tree: "#3b4658", ground: "#f4f7fb" },
  green:  { sky: ["#a8d0f0", "#d3e8f7", "#f4f1e3"], glow: "#fffbe6", stone: "#6e6458", stoneFar: "#a59a8b", window: "#fbe6b0", tree: "#2f6b3e", ground: "#5f9a4f" },
  night:  { sky: ["#030a1c", "#0b1f45", "#1d3b74"], glow: "#9fc3ff", stone: "#0c1428", stoneFar: "#1d2c52", window: "#ffcf6a", tree: "#08101f", ground: "#08101f" },
  river:  { sky: ["#f6c58f", "#f2a37a", "#7f86b8"], glow: "#fff0c2", stone: "#2a2f4a", stoneFar: "#585f8a", window: "#ffd98c", tree: "#1f2a3e", ground: "#3a4b78" },
};

// A pointed (lancet) arch window.
function lancet(x: number, y: number, w: number, h: number, fill: string, key: string) {
  const r = w / 2;
  return <path key={key} d={`M${x} ${y + h} V${y + r} Q${x} ${y} ${x + r} ${y - r * 0.6} Q${x + w} ${y} ${x + w} ${y + r} V${y + h} Z`} fill={fill} />;
}

// A spiky pinnacle.
function pinnacle(x: number, base: number, w: number, h: number, fill: string, key: string) {
  return <path key={key} d={`M${x} ${base} V${base - h * 0.55} L${x + w / 2} ${base - h} L${x + w} ${base - h * 0.55} V${base} Z`} fill={fill} />;
}

function elm(cx: number, base: number, s: number, fill: string, key: string) {
  return (
    <g key={key} fill={fill}>
      <rect x={cx - 6 * s} y={base - 120 * s} width={12 * s} height={120 * s} />
      <ellipse cx={cx} cy={base - 170 * s} rx={110 * s} ry={80 * s} />
      <ellipse cx={cx - 70 * s} cy={base - 130 * s} rx={70 * s} ry={55 * s} />
      <ellipse cx={cx + 75 * s} cy={base - 135 * s} rx={72 * s} ry={58 * s} />
      <ellipse cx={cx + 10 * s} cy={base - 230 * s} rx={80 * s} ry={55 * s} />
    </g>
  );
}

function hall(x: number, base: number, w: number, h: number, p: Palette, key: string, windows = 6) {
  const els = [<rect key={`${key}-b`} x={x} y={base - h} width={w} height={h} fill={p.stone} />];
  // crenellated parapet
  for (let i = 0; i < w / 24; i++) els.push(<rect key={`${key}-c${i}`} x={x + i * 24} y={base - h - 12} width={14} height={12} fill={p.stone} />);
  const gap = w / windows;
  for (let i = 0; i < windows; i++) els.push(lancet(x + gap * i + gap * 0.28, base - h * 0.78, gap * 0.44, h * 0.55, p.window, `${key}-w${i}`));
  els.push(pinnacle(x - 8, base - h, 16, 60, p.stone, `${key}-p1`), pinnacle(x + w - 8, base - h, 16, 60, p.stone, `${key}-p2`));
  return <g key={key}>{els}</g>;
}

function tower(cx: number, base: number, w: number, h: number, p: Palette, key: string) {
  const x = cx - w / 2;
  const els = [<rect key="t" x={x} y={base - h} width={w} height={h} fill={p.stone} />];
  // stages, buttresses, belfry openings
  els.push(<rect key="s1" x={x - 10} y={base - h * 0.45} width={w + 20} height={10} fill={p.stone} />);
  els.push(<rect key="s2" x={x - 6} y={base - h * 0.75} width={w + 12} height={8} fill={p.stone} />);
  els.push(lancet(cx - w * 0.16, base - h * 0.4, w * 0.32, h * 0.25, p.window, "w1"));
  els.push(lancet(x + w * 0.12, base - h * 0.95, w * 0.3, h * 0.17, p.window, "b1"), lancet(x + w * 0.58, base - h * 0.95, w * 0.3, h * 0.17, p.window, "b2"));
  // crown with pinnacles
  for (let i = 0; i < 4; i++) els.push(pinnacle(x - 12 + i * ((w + 8) / 3), base - h, 16, 90, p.stone, `p${i}`));
  els.push(pinnacle(cx - 14, base - h - 10, 28, 150, p.stone, "spire"));
  return <g key={key}>{els}</g>;
}

function arcade(x: number, base: number, w: number, h: number, count: number, p: Palette, key: string) {
  const els = [<rect key="wall" x={x} y={base - h - 40} width={w} height={h + 40} fill={p.stone} />];
  const gap = w / count;
  for (let i = 0; i < count; i++) els.push(lancet(x + gap * i + gap * 0.12, base - h * 0.85, gap * 0.76, h * 0.85, p.sky[0], `a${i}`));
  for (let i = 0; i < count; i++) els.push(lancet(x + gap * i + gap * 0.36, base - h - 30, gap * 0.28, 22, p.window, `c${i}`));
  return <g key={key}>{els}</g>;
}

export default function GothicScene({ kind, tone, className = "" }: { kind: SceneKind; tone: Tone; className?: string }) {
  const p = PALETTES[tone];
  const id = `${kind}-${tone}`;
  const base = 760;
  const far = (
    <path
      d="M0 600 L60 600 L60 520 L72 480 L84 520 L84 600 L180 600 L180 470 L196 410 L212 470 L212 600 L340 600 L340 540 L420 540 L420 600 L1180 600 L1180 500 L1196 440 L1212 500 L1212 600 L1320 600 L1320 520 L1400 520 L1400 455 L1414 400 L1428 455 L1428 600 L1600 600 L1600 900 L0 900 Z"
      fill={p.stoneFar} opacity=".55"
    />
  );

  let main: ReactNode;
  switch (kind) {
    case "tower":
      main = <>{hall(250, base, 380, 230, p, "h1")}{hall(970, base, 380, 230, p, "h2")}{tower(800, base, 170, 520, p, "t")}</>;
      break;
    case "cloister":
      main = <>{arcade(120, base, 1360, 300, 9, p, "arc")}{tower(1380, base - 340, 110, 200, p, "tt")}</>;
      break;
    case "gate":
      main = (
        <>
          {hall(180, base, 420, 280, p, "gl")}{hall(1000, base, 420, 280, p, "gr")}
          <rect x={600} y={base - 380} width={400} height={380} fill={p.stone} />
          {lancet(690, base - 300, 220, 300, p.sky[1], "arch")}
          {tower(620, base - 380, 70, 120, p, "g1")}{tower(980, base - 380, 70, 120, p, "g2")}
        </>
      );
      break;
    case "library":
      main = (
        <>
          {hall(200, base, 1200, 300, p, "lib", 11)}
          {tower(800, base - 300, 220, 300, p, "lt")}
          {lancet(745, base - 270, 110, 240, p.window, "rose")}
        </>
      );
      break;
    default: // quad
      main = <>{hall(80, base, 560, 210, p, "q1", 8)}{hall(960, base, 560, 210, p, "q2", 8)}{tower(800, base - 40, 130, 380, p, "qt")}</>;
  }

  const snow = tone === "snow";
  return (
    <svg className={`scene ${className}`} viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of Collegiate Gothic architecture">
      <defs>
        <linearGradient id={`sky-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={p.sky[0]} />
          <stop offset=".55" stopColor={p.sky[1]} />
          <stop offset="1" stopColor={p.sky[2]} />
        </linearGradient>
        <radialGradient id={`glow-${id}`} cx=".72" cy=".62" r=".45">
          <stop offset="0" stopColor={p.glow} stopOpacity=".85" />
          <stop offset="1" stopColor={p.glow} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`fade-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset=".6" stopColor="#000" stopOpacity="0" />
          <stop offset="1" stopColor="#000" stopOpacity=".35" />
        </linearGradient>
      </defs>
      <rect width="1600" height="900" fill={`url(#sky-${id})`} />
      <rect width="1600" height="900" fill={`url(#glow-${id})`} />
      {(tone === "night" || tone === "dusk") &&
        Array.from({ length: 40 }).map((_, i) => (
          <circle key={i} cx={(i * 397) % 1600} cy={(i * 131) % 380} r={i % 3 ? 1.2 : 2} fill="#fff" opacity={0.35 + (i % 5) / 10} />
        ))}
      {far}
      {elm(90, base + 20, 1.1, p.tree, "e1")}
      {elm(1530, base + 20, 1.2, p.tree, "e2")}
      {main}
      {elm(1460, base + 40, 0.8, p.tree, "e3")}
      <rect x="0" y={base} width="1600" height={900 - base} fill={p.ground} />
      <path d={`M700 ${base} L900 ${base} L1100 900 L500 900 Z`} fill={snow ? "#e3e9f2" : p.stoneFar} opacity=".45" />
      {snow && Array.from({ length: 90 }).map((_, i) => (
        <circle key={`s${i}`} cx={(i * 211) % 1600} cy={(i * 97) % 900} r={i % 4 ? 2 : 3.2} fill="#fff" opacity=".8" />
      ))}
      <rect width="1600" height="900" fill={`url(#fade-${id})`} />
    </svg>
  );
}
