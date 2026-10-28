import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../kit/iso-kit.mjs";
import * as G from "../../kit/lathe.mjs";
import { tubePieces, tubeSvg, crossingsOf } from "../../kit/tube.mjs";
import * as A from "../../kit/audit.mjs";
import { pdfButton } from "../../kit/pdf-button.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const THEME = process.argv.includes("--light") ? "light" : "dark";
const DEG = Math.PI / 180;

const W = 940;
const H = 820;
const AZIMUTH = 36;
const ELEVATION = 26;
const Z_AXIS = 108;
const STACK_X = 106;
const STACK_TOP = Z_AXIS + 132;
const DECK = { x: -224, y: -118, w: 448, d: 236, r: 10 };
const DECK_H = 14;
const FOOT_H = 7;

const P = k.fitProjection(
  [
    ...k.boxCorners(DECK, -DECK_H - FOOT_H, 0),
    [-245, -125, Z_AXIS + 70],
    [195, 125, STACK_TOP + 42],
    [-190, 125, STACK_TOP + 30],
    [195, -125, STACK_TOP + 30],
  ],
  W,
  H,
  { pad: 28, azimuth: AZIMUTH, elevation: ELEVATION },
);
const V = G.viewOf(P);
const KS = G.scaleOf(P);
const at = (point) => k.iso(point, P);
const S = (paths, style) => k.solidSvg(paths, style);
const Ln = (d, style) => k.lineSvg(d, style);
const Dots = (points, style) => k.dotsSvg(points, style);
const FADE = [0.04, 0.42];
const Faded = (list, style) => k.fadedSvg(list, style);

// Main horizontal turbine frame: s along +X, u along +Y, v along +Z
const MAIN = G.frameOf([0, 0, Z_AXIS], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
// Vertical exhaust stack frame at x = STACK_X
const STACK = G.frameOf([STACK_X, 0, Z_AXIS], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
// Front-left lube oil cooler frame at y = +68, z = 36
const LUBE = G.frameOf([-58, 68, 36], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
// Rear-right fuel forwarding pump frame at y = -68, z = 38
const FUEL = G.frameOf([-54, -68, 38], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const DECKF = G.frameOf([0, 0, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);

const cylPt = (s, r, deg) => G.pointOf(MAIN, s, r, deg * DEG);
const cylDir = (deg) => [0, Math.cos(deg * DEG), Math.sin(deg * DEG)];
const stackPt = (h, r, deg) => G.pointOf(STACK, h, r, deg * DEG);
const stackDir = (deg) => [Math.cos(deg * DEG), Math.sin(deg * DEG), 0];
const lubePt = (s, r, deg) => G.pointOf(LUBE, s, r, deg * DEG);
const fuelPt = (s, r, deg) => G.pointOf(FUEL, s, r, deg * DEG);

const PIECES = {
  gearbox: { name: "Epicyclic reduction gearbox", say: "planetary 19.6 : 1 reduction · 29,400 rpm input to 1,500 rpm output flange", move: [-88, 0, 0] },
  intake: { name: "Radial intake bellmouth & IGVs", say: "aerodynamic bellmouth · 20 variable inlet guide vanes · anti-ice nose cone", move: [-52, 0, 0] },
  compressor: { name: "6-stage axial compressor & bleed ring", say: "6 axial Ti-6Al-4V stages · 14.8 : 1 pressure ratio · 360° mid-stage bleed torus", move: [-18, 0, 0] },
  combustor: { name: "10-can annular combustor & fuel rail", say: "10 reverse-flow combustor cans · stainless fuel ring · dual high-energy igniters", move: [14, 0, 0] },
  turbine: { name: "2-stage HP & power turbine module", say: "Inconel 718 gas generator & power turbine · 640 °C EGT thermocouple array", move: [48, 0, 0] },
  exhaust: { name: "Exhaust collector & fluted uptake stack", say: "upturned diffuser plenum · 64-flute conical exhaust stack & eductor ring", move: [86, 0, 14] },
  lube: { name: "Shell-and-tube oil cooler & twin filters", say: "finned shell-and-tube heat exchanger · duplex spin-on filters & scavenge volute", move: [-16, 54, 6] },
  fuel: { name: "High-pressure fuel pump & metering skid", say: "brushless fuel pump · spiral volute · proportional globe metering valve", move: [-16, -54, 10] },
  plumbing: { name: "Anti-surge bleed, lube & sense manifold", say: "hydroformed bellows bleed duct · lube loop · 7 sense lines into gauge block", move: [0, 16, 52] },
  controller: { name: "FADEC controller & clamped harness", say: "dual-channel FADEC enclosure · 6 circular connectors & 4-clamp braided harness", move: [24, -52, 42] },
  stand: { name: "Stand", say: "", move: [0, 0, 0] },
};

const STAGGER = ["gearbox", "intake", "lube", "fuel", "controller", "plumbing", "combustor", "turbine", "exhaust", "compressor", "stand"];
const SPRING = { stagger: 0.035, stiffness: 64, damping: 14.2, substeps: 4 };
const R = A.recorder(P, { order: STAGGER, spring: SPRING });
const { items, nameFor } = R;
const record = R.solid;
const rideOf = (piece, move) => (move ? Object.keys(PIECES).find((id) => PIECES[id].move === move) ?? piece : piece);
function put(piece, ref, svg, { bias = 0, move, ride, shapes = [], name, route, chunk } = {}) {
  R.put({ piece, ride: ride ?? rideOf(piece, move), at: ref, bias, svg, move: move ?? PIECES[piece].move, shapes, name: name ?? nameFor(`${piece}.item`), route, chunk });
}
function tubeItems(piece, route, r, { name, tone = "hi", bias = 0, move, maxLength, spacing, closed = false, owner, touch, bundle, limp = false, breaks = [], gaps = [], caps = true, ends = [true, true], rims, free = [false, false] } = {}) {
  const id = nameFor(name ?? `${piece}.tube`);
  R.route(id, route, r, { owner: owner ?? id, touch, bundle, limp, gaps, closed, ends, rims, free, piece, move: move ?? PIECES[piece].move, ride: rideOf(piece, move) });
  tubePieces(route, r, P, { maxLength, spacing, closed, breaks, gaps, caps }).forEach((part, index) =>
    put(piece, part.mid, tubeSvg(part, { tone }), { bias, move, name: `${id}:${index}`, route: id, chunk: index, shapes: [A.tube(part.points, part.radii)] }),
  );
  return id;
}

function turned(piece, F, profile, style = {}, { extra = "", inner = "", bias = 0, move, rims, bevel = 0, steps, name, owner, smooth = profile.some((point) => point[2]) } = {}) {
  const paths = G.solidOf(profile, F, P, { bevel, smooth: smooth === true ? { rows: Math.max(...profile.map(([, r]) => r)) < 20 ? 3 : 5 } : smooth, ...(rims ? { rims } : {}), ...(steps ? { steps } : {}) });
  const mid = (profile[0][0] + profile[profile.length - 1][0]) / 2;
  const id = nameFor(name ?? `${piece}.turned${Math.round(profile[0][0])}`);
  const shape = record(A.solid(F, profile, { name: id, owner, curve: smooth && !smooth.slope ? profile : undefined }));
  put(piece, G.add3(F.o, G.mul3(F.a, mid)), S(paths, { tone: "hi", ...style, inner: inner ? Ln(inner, { tone: "faint" }) : "" }) + extra, { bias, move, name: id, shapes: [shape] });
  return shape;
}

function band(piece, F, s0, s1, r, style = {}, options = {}) {
  return turned(piece, F, [
    [s0, r],
    [s1, r],
  ], style, options);
}

function flangeAt(piece, centre, axis, r, thick, { bolts = 8, tone = "hi", move, bias = 0, boltR, name, owner } = {}) {
  const F = G.frameAlong(centre, axis);
  const id = nameFor(name ?? `${piece}.flange`);
  const paths = G.disc(-thick / 2, thick / 2, r, F, P);
  const faces = [];
  const towards = G.dot3(F.a, V) > 0 ? thick / 2 : -thick / 2;
  if (Math.abs(G.dot3(F.a, V)) > 0.12 && bolts) faces.push(Dots(G.dotsOf(F, towards, boltR ?? r * 0.74, bolts, P, { all: true }), { size: 0.42, tone: "mid" }));
  put(piece, centre, S(paths, { tone }) + faces.join(""), { bias, move, name: id, shapes: [record(A.disc(F, -thick / 2, thick / 2, r, { name: id, owner }))] });
}

function pipe(piece, control, r, { bend = 2.4, tone = "hi", flanges = [true, true], flangeR = 1.55, coupling = false, bands = [], bellows = null, valve = null, move, bias = 0, maxLength = 22, spacing, name, touch, breaks = [], gaps: extra = [], free } = {}) {
  const flangeRs = [flangeR].flat().length > 1 ? [flangeR].flat() : [flangeR, flangeR].flat();
  if (coupling) flanges = [flanges[0], false];
  const line = G.fillet(control, Math.max(r * bend, 3), r > 3 ? 24 : 12, { P, tube: r });
  const total = G.pathLength(line);
  const collars = [];
  [[0, -1], [total, 1]].forEach(([along, sign], index) => {
    if (!flanges[index]) return;
    const thick = Math.max(0.9, r * 0.55);
    const tangent = G.tangentAlong(line, along);
    collars.push({ kind: "flange", centre: G.add3(G.pointAlong(line, along), G.mul3(tangent, (-sign * thick) / 2)), tangent, radius: r * flangeRs[index], thick, gap: sign < 0 ? [0, thick] : [total - thick, total] });
  });
  if (coupling) {
    const thick = Math.max(1.6, r * 1.4);
    collars.push({ kind: "coupling", centre: G.pointAlong(line, total - thick / 2), tangent: G.tangentAlong(line, total), radius: r * 1.5, thick, gap: [total - thick, total] });
  }
  const ring = (along, radius, thick, kind) => collars.push({ kind, centre: G.pointAlong(line, along), tangent: G.tangentAlong(line, along), radius, thick, gap: [along - thick / 2, along + thick / 2] });
  for (const share of bands) ring(total * share, r * 1.18, Math.max(0.8, r * 0.7), "band");
  if (bellows) {
    const [from, to, count] = bellows;
    for (let index = 0; index < count; index++) ring(total * (from + ((to - from) * index) / (count - 1)), r * 1.26, Math.max(0.6, r * 0.3), "bellows");
  }
  const gaps = [...collars.map(({ gap }) => gap), ...extra];
  if (valve) {
    const along = valve[0] > 1 ? valve[0] : total * valve[0];
    gaps.push([along - valve[1] * 2.4, along + valve[1] * 2.4]);
  }
  const owner = tubeItems(piece, line, r, { name: name ?? `${piece}.pipe`, tone, bias, move, maxLength, spacing: spacing ?? Math.max(0.8, Math.min(2.4, r * 0.18)), touch, gaps, breaks, free, rims: flanges.map((flanged, index) => (flanged ? r * flangeRs[index] : index && coupling ? r * 1.5 : r)) });
  for (const { kind, centre, tangent, radius, thick } of collars)
    flangeAt(piece, centre, tangent, radius, thick, { bolts: kind === "flange" && r > 3 ? 8 : 0, tone: kind === "flange" || kind === "coupling" ? tone : "mid", move, bias, name: `${owner}.${kind}`, owner });
  line.owner = owner;
  return line;
}

function boxAt(piece, plan, z, h, style = {}, { extra = "", bias = 0, move, bevel = 0.5, steps = 3, name, owner } = {}) {
  const centre = [plan.x + plan.w / 2, plan.y + plan.d / 2, z + h / 2];
  const id = nameFor(name ?? `${piece}.box`);
  put(piece, centre, S(k.slabOf(plan, z, h, P, steps, bevel), { tone: "hi", ...style }) + extra, { bias, move, name: id, shapes: [record(A.box([plan.x, plan.y, z], [plan.x + plan.w, plan.y + plan.d, z + h], { name: id, owner }))] });
}

function valveOn(piece, line, share, r, { move, tone = "hi", name, side = [0, 0, 1] } = {}) {
  const total = G.pathLength(line);
  const along = share > 1 ? share : total * share;
  const centre = G.pointAlong(line, along);
  const tangent = G.tangentAlong(line, along);
  const F = G.frameAlong(centre, tangent);
  const body = r * 1.85;
  const id = nameFor(name ?? `${line.owner}.valve`);
  const owner = line.owner;
  const crown = body * 1.08;
  const bulge = (x) => r * 1.45 + (crown - r * 1.45) * Math.sqrt(Math.max(0, 1 - (x / (r * 1.6)) ** 2));
  const bulgeSlope = (x) => {
    if (Math.abs(x) >= r * 1.6 - 1e-9) return 0;
    const t = Math.max(-0.995, Math.min(0.995, x / (r * 1.6)));
    return (-(crown - r * 1.45) * t) / (r * 1.6 * Math.sqrt(1 - t * t));
  };
  const meridian = [
    [-r * 2.4, 0],
    [-r * 2.4, r * 1.45],
    ...Array.from({ length: 17 }, (_, index) => {
      const x = r * 1.6 * Math.sin(((index - 8) / 8) * (Math.PI / 2));
      return [x, bulge(x), index && index < 16 ? 1 : 0];
    }),
    [r * 2.4, r * 1.45],
    [r * 2.4, 0],
  ];
  put(
    piece,
    centre,
    S(G.lathe(meridian, F, P, { steps: 36, smooth: { slope: bulgeSlope, rows: 3 } }), { tone }) + Dots([...G.dotsOf(F, -r * 2.4, r * 1.2, 8, P, { all: true }), ...G.dotsOf(F, r * 2.4, r * 1.2, 8, P, { all: true })].filter((_, index) => index % 2 === 0), { size: 0.4, tone: "mid" }),
    { move, name: id, shapes: [record(A.body(F, meridian, { name: id, owner }))] },
  );
  const up = G.unit3(side);
  const NF = G.frameAlong(centre, up);
  const s0 = body * 1.08 - 0.25;
  const s1 = body * 1.08 + body * 0.45;
  put(piece, G.add3(centre, G.mul3(up, (s0 + s1) / 2)), S(G.disc(s0, s1, r * 0.5, NF, P), { tone }), { move, bias: 0.2, name: `${id}.neck`, shapes: [record(A.disc(NF, s0, s1, r * 0.5, { name: `${id}.neck`, owner }))] });
  if (up[2] > 0.99) {
    const top = G.add3(centre, [0, 0, s1]);
    const plan = { x: top[0] - r * 1.5, y: top[1] - r * 1.5, w: r * 3, d: r * 3, r: 0.8 };
    const lid = top[2] + r * 2.2;
    boxAt(piece, plan, top[2], r * 2.2, { tone }, {
      move,
      bias: 0.3,
      name: `${id}.actuator`,
      owner,
      extra: Ln(k.planOutline(k.insetPlan(plan, 0.8), lid, P, 2), { tone: "faint" }) + Dots([at([plan.x + 1.2, plan.y + 1.2, lid]), at([plan.x + plan.w - 1.2, plan.y + plan.d - 1.2, lid])], { size: 0.4 }),
    });
    const port = [top[0], top[1], lid];
    return { port, approach: G.add3(port, [0, 0, 5]), lid };
  }
  const can = [[s1, 0], [s1, r * 1.5], [s1 + r * 2.2, r * 1.5], [s1 + r * 2.2, 0]];
  const end = s1 + r * 2.2;
  put(piece, G.add3(centre, G.mul3(up, (s1 + end) / 2)), S(G.lathe(can, NF, P, { steps: 32, bevel: 0.6 }), { tone }) + Ln(G.circleOf(NF, end, r * 1.1, P, 24), { tone: "faint" }) + Dots(G.dotsOf(NF, end, r * 1.25, 4, P, { all: true, phase: Math.PI / 4 }), { size: 0.4 }), { move, bias: 0.3, name: `${id}.actuator`, shapes: [record(A.body(NF, can, { name: `${id}.actuator`, owner }))] });
  const port = G.add3(centre, G.mul3(up, end));
  return { port, approach: G.add3(port, G.mul3(up, 5)) };
}

function ballAt(piece, centre, r, { move, tone = "mid", bias = 0, name, owner } = {}) {
  const id = nameFor(name ?? `${piece}.ball`);
  put(piece, centre, S(G.sphereOf(centre, r, P, { steps: G.stepsFor(r, 32) }), { tone }), { move, bias, name: id, shapes: [record(A.ball(centre, r, { name: id, owner }))] });
}

function boss(piece, centre, outward, r, length, { move, tone = "hi", bias = 0.1, name, ring = true, owner } = {}) {
  const F = G.frameAlong(centre, outward);
  const id = nameFor(name ?? `${piece}.boss`);
  put(piece, G.add3(centre, G.mul3(F.a, length / 2)), S(G.disc(0, length, r, F, P), { tone }) + (ring && G.dot3(F.a, V) > 0.15 ? Ln(G.circleOf(F, length, r * 0.55, P, 16), { tone: "faint" }) : ""), { bias, move, name: id, shapes: [record(A.disc(F, 0, length, r, { name: id, owner }))] });
  return G.add3(centre, G.mul3(F.a, length));
}

const CABLES = [];
function cable(piece, points, { move, bias = 0.2, r = 0.62, bend = 5, name, bundle, touch, clamps = [], shells = [false, false], free } = {}) {
  const route = G.fillet(points, bend, 12, { P, tube: r });
  CABLES.push({ piece, route });
  const total = G.pathLength(route);
  const SHELL = 2.2;
  const gaps = [...clamps.flatMap(({ centre, axis, radius }) => crossingsOf(route, centre, axis, radius).map((at) => [at - CLAMP_HALF - 0.05, at + CLAMP_HALF + 0.05])), ...(shells[0] ? [[0, SHELL]] : []), ...(shells[1] ? [[total - SHELL, total]] : [])];
  const id = tubeItems(piece, route, r, { name: name ?? `${piece}.cable`, tone: "mid", bias, move, maxLength: 14, spacing: 1, bundle, touch, gaps, free, limp: true, rims: shells.map((on) => (on ? r * 2 : r)) });
  [0, 1].forEach((index) => {
    const end = index ? route[route.length - 1] : route[0];
    if (!shells[index]) {
      put(piece, end, Dots([at(end)], { size: 0.5, tone: "hi" }), { bias: bias + 0.15, move, name: `${id}.end`, shapes: [A.ball(end, 0.5 / KS)] });
      return;
    }
    const tangent = G.tangentAlong(route, index ? total : 0);
    const F = G.frameAlong(end, tangent);
    const [s0, s1] = index ? [-SHELL, 0] : [0, SHELL];
    const outer = index ? s0 : s1;
    put(piece, G.add3(end, G.mul3(tangent, (s0 + s1) / 2)), S(G.disc(s0, s1, r * 2, F, P, { bevel: 0.25 }), { tone: "mid" }) + (G.dot3(G.mul3(F.a, index ? -1 : 1), V) > 0.2 ? Ln(G.circleOf(F, outer, r * 1.1, P, 12), { tone: "faint" }) : ""), { bias: bias + 0.1, move, name: `${id}.shell`, shapes: [record(A.disc(F, s0, s1, r * 2, { name: `${id}.shell`, owner: id }))] });
  });
  return route;
}

const CLAMP_HALF = 0.9;
function clampAt(piece, centre, axis, r, { move, bias = 0.3, name = `${piece}.clamp`, bundle } = {}) {
  const F = G.frameAlong(centre, axis);
  const id = nameFor(name);
  put(piece, centre, S(G.disc(-CLAMP_HALF, CLAMP_HALF, r, F, P), { tone: "mid" }), { bias, move, name: id, shapes: [record(A.disc(F, -CLAMP_HALF, CLAMP_HALF, r, { name: id, anchor: false, bundle, fitting: true }))] });
}

// ============================================================================
// 0. HEAVY WELDED STEEL SKID BASE & PEDESTAL TRUNNIONS (stand)
// ============================================================================
const back = [];
back.push(`<path class="iso-halo" d="${k.haloOf(DECK, -DECK_H - FOOT_H, DECK_H, P)}"/>`);
const FEET = [
  [-204, -100],
  [-102, -100],
  [0, -100],
  [102, -100],
  [204, -100],
  [-204, 100],
  [-102, 100],
  [0, 100],
  [102, 100],
  [204, 100],
].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
for (const [x, y] of FEET) {
  back.push(S(k.cylinder(x, y, 9.5, -DECK_H - FOOT_H, 2, P, 28), { tone: "lo" }));
  back.push(S(k.cylinder(x, y, 7, -DECK_H - FOOT_H + 2, FOOT_H - 2, P, 28), { tone: "mid" }));
}
back.push(S(k.slabOf(DECK, -DECK_H, DECK_H, P, 8, 1.5), { tone: "mid" }));
record(A.box([DECK.x, DECK.y, -DECK_H], [DECK.x + DECK.w, DECK.y + DECK.d, 0], { name: "stand.deck" }));
back.push(Ln(k.planOutline(k.insetPlan(DECK, 7), 0, P), { tone: "lo" }));
const DECK_SCREWS = k.corners(DECK, 14);
back.push(Ln(DECK_SCREWS.map(([x, y]) => k.ring(x, y, 3, 0, P, 18)).join(""), { tone: "lo" }));
back.push(Dots(DECK_SCREWS.map(([x, y]) => at([x, y, 0])), { size: 0.55 }));
back.push(Ln(k.sideTicks(DECK.y + 20, DECK.y + DECK.d - 20, 10, 5, DECK.x + DECK.w, 0, [2.4, 4.6], P, "y").minor, { tone: "lo" }));
back.push(Ln(k.sideTicks(DECK.y + 20, DECK.y + DECK.d - 20, 10, 5, DECK.x + DECK.w, 0, [2.4, 4.6], P, "y").major, { tone: "mid" }));

const GRATE = { x: -156, y: -44, w: 296, d: 88, r: 5 };
back.push(Ln(k.planOutline(GRATE, 0, P), { tone: "lo" }));
for (let x = GRATE.x + 14; x < GRATE.x + GRATE.w - 4; x += 14) back.push(Ln(k.lineOnTop([x, GRATE.y], [x, GRATE.y + GRATE.d], 0, P), { tone: "faint" }));

const STRIP = { x: -202, y: DECK.y + DECK.d - 15, w: 260, d: 8, r: 1 };
back.push(S(k.slabOf(STRIP, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
const TICKS = k.topTicks(STRIP.x + 4, STRIP.x + STRIP.w - 4, 4, 5, STRIP.y + 1, 0.8, [2.2, 4.4], P);
back.push(Ln(TICKS.minor, { tone: "lo" }), Ln(TICKS.major, { tone: "mid" }));
back.push(Dots([at([STRIP.x + 2.2, STRIP.y + 4, 0.8]), at([STRIP.x + STRIP.w - 2.2, STRIP.y + 4, 0.8])], { size: 0.45 }));

const LABEL = { x: DECK.x + DECK.w - 22, y: -86, w: 12, d: 68, r: 1.5 };
back.push(S(k.slabOf(LABEL, 0, 1, P, 3), { tone: "mid" }));
back.push(Ln(k.planOutline(k.insetPlan(LABEL, 1.8), 1, P), { tone: "faint" }));
back.push(k.faceTextSvg(k.topMatrix([LABEL.x + 7.4, LABEL.y + LABEL.d - 5], 1, P, "y"), "GT-400", { size: 4.2, tone: "lo" }));
back.push(Dots([at([LABEL.x + LABEL.w / 2, LABEL.y + 2.6, 1]), at([LABEL.x + LABEL.w / 2, LABEL.y + LABEL.d - 2.6, 1])], { size: 0.45 }));

// Front & Rear Pedestal Trunnions supporting the horizontal turbine at x = -142 and x = +66
for (const px of [-142, 66]) {
  const pad = { x: px - 14, y: -52, w: 28, d: 104, r: 3 };
  back.push(S(k.slabOf(pad, 0, 5, P, 3, 0.8), { tone: "mid" }));
  back.push(Dots(k.corners(pad, 4).map(([x, y]) => at([x, y, 5])), { size: 0.5 }));
  for (const py of [-38, 38]) {
    const leg = { x: px - 7, y: py - 7, w: 14, d: 14, r: 1.5 };
    back.push(S(k.slabOf(leg, 5, Z_AXIS - 28, P, 3, 0.6), { tone: "mid" }));
    const cap = { x: px - 9, y: py - 9, w: 18, d: 18, r: 2 };
    back.push(S(k.slabOf(cap, Z_AXIS - 23, 8, P, 3, 0.6), { tone: "mid" }));
    back.push(Dots(k.corners(cap, 3).map(([x, y]) => at([x, y, Z_AXIS - 15])), { size: 0.45 }));
  }
  const cross = { x: px - 8, y: -46, w: 16, d: 92, r: 2 };
  back.push(S(k.slabOf(cross, 38, 8, P, 3, 0.5), { tone: "mid" }));
}

// Chilled water / oil skid perimeter loop on the deck
const LOOP_PTS = G.fillet([[-188, -86, 4.5], [164, -86, 4.5], [164, 86, 4.5], [-188, 86, 4.5], [-188, -86, 4.5]], 14);
for (const part of tubePieces(LOOP_PTS, 1.8, P, { maxLength: 300, spacing: 2, closed: true })) back.push(tubeSvg(part, { tone: "mid" }));

// ============================================================================
// 1. EPICYCLIC REDUCTION GEARBOX (gearbox: s = -196 .. -138)
// ============================================================================
turned("gearbox", MAIN, [[-196, 16.5], [-191, 16.5]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, -196, 13.5, 12, P, { all: true }), { size: 0.42, tone: "mid" }) + Ln(G.circleOf(MAIN, -196, 9, P), { tone: "faint" }),
});
band("gearbox", MAIN, -191, -177, 10.2, {}, { inner: G.arcOf(MAIN, -184, 10.2, P) });
turned("gearbox", MAIN, [[-177, 15], [-173, 21, 1], [-169, 26.5, 1], [-166, 28.5]], {}, {
  smooth: { rows: 4 },
  extra: Dots(G.dotsOf(MAIN, -173, 19, 16, P, { all: true }), { size: 0.38, tone: "mid" }),
});
band("gearbox", MAIN, -166, -146, 28.5, {}, {
  name: "gearbox.housing",
  inner: [-161, -151].map((s) => G.arcOf(MAIN, s, 28.5, P)).join(""),
  extra: Faded(G.ribsOf(MAIN, -165, -147, 28.5, 22, P, { fade: [0.08, 0.5] }), { tone: "faint" }),
});
turned("gearbox", MAIN, [[-146, 31], [-142, 31]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, -142, 29, 24, P, { all: true }), { size: 0.4, tone: "mid" }),
});
band("gearbox", MAIN, -142, -136, 15.5, {}, { inner: G.arcOf(MAIN, -139, 15.5, P) });
const GBX_TOP_BOSS = boss("gearbox", cylPt(-156, 28.5, 90), cylDir(90), 2.6, 3.5);
const GBX_SIDE_BOSS = boss("gearbox", cylPt(-156, 28.5, 15), cylDir(15), 2.8, 3.2);
const GBX_REAR_BOSS = boss("gearbox", cylPt(-156, 28.5, 165), cylDir(165), 2.2, 3);

// ============================================================================
// 2. RADIAL INTAKE BELLMOUTH & VARIABLE IGVs (intake: s = -136 .. -102)
// ============================================================================
const noseProfile = Array.from({ length: 13 }, (_, i) => {
  const t = i / 12;
  const s = -134 + t * 22;
  const r = 14.5 * Math.sqrt(t);
  return [s, r, i > 0 && i < 12 ? 1 : 0];
});
turned("intake", MAIN, noseProfile, {}, { smooth: { rows: 4 }, inner: G.arcOf(MAIN, -122, 10.5, P) });

const bellInProfile = [
  [-134, 24],
  [-130, 24.5, 1],
  [-122, 28, 1],
  [-112, 33.5, 1],
  [-106, 36.2],
];
turned("intake", MAIN, bellInProfile, {}, {
  smooth: { rows: 5 },
  inner: [-126, -115].map((s) => G.arcOf(MAIN, s, s === -126 ? 26.2 : 32, P)).join(""),
});
// 8 radial intake struts between hub and bellmouth rim at s = -131
for (let i = 0; i < 8; i++) {
  const deg = i * 45 + 22.5;
  const p0 = cylPt(-131, 13.5, deg);
  const p1 = cylPt(-131, 24, deg);
  const F = G.frameAlong(p0, cylDir(deg));
  put("intake", G.lerp3(p0, p1, 0.5), S(G.disc(0, 10.5, 1.2, F, P), { tone: "mid" }), { name: `intake.strut${i}`, shapes: [record(A.disc(F, 0, 10.5, 1.2, { name: `intake.strut${i}` }))] });
}
// IGV actuator unison ring
turned("intake", MAIN, [[-106, 38.2], [-101, 38.2]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, -103.5, 38.2, 24, P, { fade: FADE }), { size: 0.42, tone: "mid" }),
  inner: G.arcOf(MAIN, -103.5, 38.2, P),
});
const IGV_SERVO_BOSS = boss("intake", cylPt(-103.5, 38.2, 115), cylDir(115), 2.4, 4);

// ============================================================================
// 3. 6-STAGE AXIAL COMPRESSOR & 360° BLEED TORUS (compressor: s = -101 .. -26)
// ============================================================================
// Visible front compressor rotor disc & blades when exploded
turned("compressor", MAIN, [[-101, 33.5], [-98, 33.5]], { tone: "mid" }, {
  extra: Dots(G.dotsOf(MAIN, -101, 29, 32, P, { all: true }), { size: 0.38, tone: "hi" }) + Ln(G.circleOf(MAIN, -101, 22, P), { tone: "lo" }),
});
const compProfile = [
  [-98, 35.2],
  [-82, 34, 1],
  [-62, 31.8, 1],
  [-42, 29.8, 1],
  [-26, 28.6],
];
turned("compressor", MAIN, compProfile, {}, {
  smooth: { rows: 5 },
  inner: [-88, -72, -52, -36].map((s) => G.arcOf(MAIN, s, 35.2 - ((s + 98) / 72) * 6.6, P)).join(""),
});
// 5 bolted stage flange rings along the axial compressor
for (const [s, r] of [[-94, 36.8], [-78, 35.6], [-62, 33.8], [-46, 31.8], [-31, 30.6]]) {
  band("compressor", MAIN, s, s + 2.8, r, {}, {
    extra: Dots(G.dotsOf(MAIN, s + 1.4, r, 28, P, { fade: FADE }), { size: 0.36, tone: "mid" }),
  });
}
// 360° Mid-Stage Compressor Bleed Torus Manifold at s = -60
const BLEED_S = -60;
const BLEED_R = 42.5;
const BLEED_TUBE = 3.4;
const BLEED_RING = G.arcPoints(MAIN, BLEED_S, BLEED_R, 0, Math.PI * 2, 96);
tubeItems("compressor", BLEED_RING, BLEED_TUBE, { name: "compressor.bleed-ring", maxLength: 20, spacing: 1.2, closed: true });
for (const deg of [25, 95, 165, 275]) {
  const pIn = cylPt(BLEED_S, 33.5, deg);
  const F = G.frameAlong(pIn, cylDir(deg));
  put("compressor", cylPt(BLEED_S, 37.5, deg), S(G.disc(0, BLEED_R - 33.5, 2, F, P), { tone: "hi" }), { name: `compressor.bleed-stub${deg}`, shapes: [record(A.disc(F, 0, BLEED_R - 33.5, 2, { name: `compressor.bleed-stub${deg}` }))] });
  ballAt("compressor", cylPt(BLEED_S, BLEED_R, deg), 4.8, { tone: "hi", name: `compressor.bleed-tee${deg}` });
}
const COMP_SENSE_BOSS = boss("compressor", cylPt(-36, 30, 65), cylDir(65), 1.8, 2.8);

// ============================================================================
// 4. 10-CAN ANNULAR COMBUSTOR & FUEL RAIL (combustor: s = -26 .. +20)
// ============================================================================
turned("combustor", MAIN, [[-26, 33.5], [-22, 33.5]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, -26, 31.5, 28, P, { all: true }), { size: 0.4, tone: "mid" }),
});
band("combustor", MAIN, -22, 16, 35.8, {}, {
  name: "combustor.liner",
  inner: [-10, 4].map((s) => G.arcOf(MAIN, s, 35.8, P)).join(""),
  extra: Dots(G.dotsOf(MAIN, 8, 35.8, 24, P, { fade: FADE }), { size: 0.4, tone: "mid" }),
});
turned("combustor", MAIN, [[16, 38], [20, 38]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, 20, 36, 32, P, { all: true }), { size: 0.4, tone: "mid" }),
});
// 10 radial combustor cans with bolted fuel injector caps around s = -8
for (let i = 0; i < 10; i++) {
  const deg = i * 36 + 12;
  const base = cylPt(-8, 35.2, deg);
  const F = G.frameAlong(base, cylDir(deg));
  put("combustor", cylPt(-8, 37.5, deg), S(G.disc(0, 4.2, 4.8, F, P, { bevel: 0.4 }), { tone: "hi" }) + Dots(G.dotsOf(F, 4.2, 3.6, 6, P, { all: true }), { size: 0.36, tone: "mid" }), {
    bias: 0.2,
    name: `combustor.can${i}`,
    shapes: [record(A.disc(F, 0, 4.2, 4.8, { name: `combustor.can${i}` }))],
  });
}
// Circular Stainless Fuel Manifold Rail at s = -16, R = 41.5
const FUEL_RAIL_S = -16;
const FUEL_RAIL_R = 41.5;
const FUEL_RAIL = G.arcPoints(MAIN, FUEL_RAIL_S, FUEL_RAIL_R, 0, Math.PI * 2, 84);
tubeItems("combustor", FUEL_RAIL, 1.5, { name: "combustor.fuel-rail", maxLength: 18, spacing: 1, closed: true });
const IGNITER_A = boss("combustor", cylPt(2, 35.8, 125), cylDir(125), 2.2, 4.2);
const IGNITER_B = boss("combustor", cylPt(2, 35.8, 55), cylDir(55), 2.2, 4.2);
const COMB_SENSE_BOSS = boss("combustor", cylPt(11, 35.8, 82), cylDir(82), 1.8, 2.8);

// ============================================================================
// 5. 2-STAGE HP & POWER TURBINE MODULE (turbine: s = +20 .. +68)
// ============================================================================
// Visible HP turbine bladed rotor disc when exploded
turned("turbine", MAIN, [[20, 32], [23.5, 32]], { tone: "mid" }, {
  extra: Dots(G.dotsOf(MAIN, 20, 28, 32, P, { all: true }), { size: 0.38, tone: "hi" }),
});
const turbProfile = [
  [23.5, 33.5],
  [32, 29.5, 1],
  [44, 31.5, 1],
  [56, 35.5, 1],
  [64, 38.2],
];
turned("turbine", MAIN, turbProfile, {}, {
  smooth: { rows: 5 },
  inner: [32, 52].map((s) => G.arcOf(MAIN, s, s === 32 ? 29.5 : 34.2, P)).join(""),
  extra: Faded(G.ribsOf(MAIN, 25, 39, 31.2, 24, P, { fade: [0.08, 0.5] }), { tone: "faint" }),
});
// Interstage & Rear Turbine Bolted Flanges
band("turbine", MAIN, 41, 44.5, 35.5, {}, {
  extra: Dots(G.dotsOf(MAIN, 42.8, 35.5, 28, P, { fade: FADE }), { size: 0.38, tone: "mid" }),
});
turned("turbine", MAIN, [[64, 41], [68, 41]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, 68, 38.8, 32, P, { all: true }), { size: 0.4, tone: "mid" }),
});
// 6 EGT Thermocouple Bosses around s = +54
const EGT_BOSS = {};
for (const deg of [25, 65, 110, 150, 210, 320]) {
  EGT_BOSS[deg] = boss("turbine", cylPt(54, 35, deg), cylDir(deg), 1.7, 3);
}
const TURB_SUMP_BOSS = boss("turbine", cylPt(36, 30.5, 18), cylDir(18), 2.6, 3.4);

// ============================================================================
// 6. EXHAUST DIFFUSER PLENUM & FLUTED UPTAKE STACK (exhaust: s = +68..+138, z = Z_AXIS..STACK_TOP)
// ============================================================================
const exhPlenum = [
  [68, 40.5],
  [84, 41.5, 1],
  [124, 40.5, 1],
  [136, 36.5],
];
turned("exhaust", MAIN, exhPlenum, {}, {
  smooth: { rows: 5 },
  inner: [88, 120].map((s) => G.arcOf(MAIN, s, 41, P)).join(""),
});
turned("exhaust", MAIN, [[136, 38.5], [140, 38.5]], {}, {
  bevel: 0.6,
  extra: Dots(G.dotsOf(MAIN, 140, 35.5, 28, P, { all: true }), { size: 0.4, tone: "mid" }) + Ln(G.circleOf(MAIN, 140, 24, P), { tone: "faint" }),
});
boss("exhaust", [140, 0, Z_AXIS], [1, 0, 0], 11, 4, { ring: true });

// Vertical Conical Fluted Uptake Stack rising from the collector at x = STACK_X
const stackR = (h) => 33 + 11 * Math.pow((h - 28) / 100, 1.35);
const stackSlope = (h) => (11 * 1.35 * Math.pow(Math.max(0.01, (h - 28) / 100), 0.35)) / 100;
const STACK_AT = [28, 42, 56, 72, 88, 104, 118, 128];
const STACK_STEPS = 84;
const STACK_BANDS = G.bandsOf(
  [[STACK_AT[0], stackR(STACK_AT[0])], [STACK_AT[STACK_AT.length - 1], stackR(STACK_AT[STACK_AT.length - 1])]],
  STACK_AT.slice(1, -1),
  STACK,
  P,
  { radius: stackR, slope: stackSlope, steps: STACK_STEPS, rows: 6 },
);
STACK_BANDS.bands.forEach((b, idx) => {
  const seam = idx === 2 || idx === 4 ? Ln(b.seam, { tone: "faint" }) : "";
  put("exhaust", [STACK_X, 0, Z_AXIS + (b.s0 + b.s1) / 2], S(b.paths, { tone: "hi", inner: seam }), {
    name: `exhaust.stack${idx}`,
    shapes: [record(A.solid(STACK, b.profile, { radius: stackR, name: `exhaust.stack${idx}` }))],
  });
});
const STACK_FLUTES = STACK_BANDS.sidesOf(STACK_AT[0], STACK_AT[STACK_AT.length - 2], { ends: "first", count: 56 });
put("exhaust", [STACK_X, 0, Z_AXIS + 80], Ln(STACK_FLUTES.d, { tone: "hi" }), {
  bias: 0.2,
  name: "exhaust.flutes",
  shapes: STACK_FLUTES.points.map((pts) => A.tube(pts, 0.4 / KS)),
});
// Top Exhaust Lip Flange & Eductor Manifold Ring
put(
  "exhaust",
  [STACK_X, 0, Z_AXIS + 130],
  S(G.ringBand(128, 132, 36, 46.5, STACK, P), { tone: "hi" }) +
    Ln(G.arcOf(STACK, 132, 36, P, { inward: true, least: -1 }), { tone: "lo" }) +
    Dots(G.dotsOf(STACK, 132, 43.5, 36, P, { all: true }), { size: 0.4, tone: "mid" }),
  { name: "exhaust.lip", shapes: [record(A.ring(STACK, 128, 132, 36, 46.5, { name: "exhaust.lip" }))] },
);
const EDUCTOR_H = 54;
const EDUCTOR_R = 42.5;
const EDUCTOR_RING = G.arcPoints(STACK, EDUCTOR_H, EDUCTOR_R, 0, Math.PI * 2, 96);
tubeItems("exhaust", EDUCTOR_RING, 3.2, { name: "exhaust.eductor", maxLength: 20, spacing: 1.2, closed: true });
for (const deg of [45, 165, 285]) {
  ballAt("exhaust", stackPt(EDUCTOR_H, EDUCTOR_R, deg), 4.6, { tone: "hi", name: `exhaust.tee${deg}` });
}

// ============================================================================
// 7. SHELL-AND-TUBE OIL COOLER, TWIN FILTERS & SCAVENGE PUMP (lube: y = +68)
// ============================================================================
turned("lube", LUBE, [[-44, 6], [-41, 13, 1], [-37, 16.5]], {}, { smooth: { rows: 3 } });
turned("lube", LUBE, [[-37, 18.5], [-34, 18.5]], {}, {
  bevel: 0.5,
  extra: Dots(G.dotsOf(LUBE, -34, 16.8, 16, P, { all: true }), { size: 0.38, tone: "mid" }),
});
band("lube", LUBE, -34, 34, 16, {}, {
  name: "lube.shell",
  inner: [-12, 12].map((s) => G.arcOf(LUBE, s, 16, P)).join(""),
  extra: Faded(G.ribsOf(LUBE, -28, 28, 16, 20, P, { fade: [0.1, 0.55] }), { tone: "faint" }),
});
turned("lube", LUBE, [[34, 18.5], [37, 18.5]], {}, {
  bevel: 0.5,
  extra: Dots(G.dotsOf(LUBE, 37, 16.8, 16, P, { all: true }), { size: 0.38, tone: "mid" }),
});
turned("lube", LUBE, [[37, 16.5], [41, 13, 1], [44, 6]], {}, { smooth: { rows: 3 } });
// Spiral scavenge volute on the front of the lube cooler
const LVOLUTE = G.spiral(LUBE, -22, 18, 22, -140 * DEG, 50 * DEG, 44);
tubeItems("lube", LVOLUTE, (t) => 1.8 + 2.8 * t, { name: "lube.volute", maxLength: 16, spacing: 1, bias: 0.3, ends: [false, true] });

// Twin Vertical Spin-On Duplex Oil Filter Canisters on filter manifold block
const FILTER_BLOCK = { x: 0, y: 58, w: 38, d: 20, r: 2 };
boxAt("lube", FILTER_BLOCK, 36, 10, {}, {
  name: "lube.filter-head",
  extra: Ln(k.planOutline(k.insetPlan(FILTER_BLOCK, 2), 46, P, 2), { tone: "faint" }) + Dots(k.corners(FILTER_BLOCK, 3).map(([x, y]) => at([x, y, 46])), { size: 0.45 }),
});
for (const fx of [10, 28]) {
  const FF = G.frameOf([fx, 68, 46], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  turned("lube", FF, [[0, 7.8], [3, 8.4], [32, 8.4], [34, 7.2]], {}, {
    bevel: 0.5,
    inner: [10, 24].map((z) => G.arcOf(FF, z, 8.4, P)).join(""),
    extra: Ln(k.knurl(fx, 68, 8.4, 72, 78, 28, P), { tone: "lo" }) + Dots([at([fx, 68, 80])], { size: 0.45, tone: "mid" }),
  });
}

// ============================================================================
// 8. HIGH-PRESSURE FUEL PUMP & METERING SKID (fuel: y = -68)
// ============================================================================
turned("fuel", FUEL, [[-34, 13.5], [-31, 13.5]], {}, {
  bevel: 0.5,
  extra: Dots(G.dotsOf(FUEL, -34, 11.5, 12, P, { all: true }), { size: 0.38, tone: "mid" }),
});
band("fuel", FUEL, -31, 4, 12.2, {}, {
  name: "fuel.motor",
  inner: G.arcOf(FUEL, -14, 12.2, P),
  extra: Faded(G.ribsOf(FUEL, -28, 0, 12.2, 16, P, { fade: [0.1, 0.55] }), { tone: "faint" }),
});
turned("fuel", FUEL, [[4, 15.5], [18, 15.5], [22, 11.5]], {}, {
  bevel: 0.5,
  extra: Dots(G.dotsOf(FUEL, 6, 15.5, 18, P, { fade: FADE }), { size: 0.38, tone: "mid" }),
});
const FVOL = G.spiral(FUEL, 12, 17, 21.5, -120 * DEG, 70 * DEG, 42);
tubeItems("fuel", FVOL, (t) => 1.8 + 2.6 * t, { name: "fuel.volute", maxLength: 16, spacing: 1, bias: 0.3, ends: [false, true] });

// ============================================================================
// 9. ANTI-SURGE BLEED, LUBE & 7-LINE SENSE MANIFOLD (plumbing)
// ============================================================================
// 9a. Anti-surge Compressor Bleed Duct with 5-ring Bellows & Globe Valve (from s=-60 bleed ring to stack eductor)
const BLEED_START = cylPt(BLEED_S, BLEED_R, 72);
const BLEED_END = stackPt(EDUCTOR_H, EDUCTOR_R, 165);
const BLEED_DUCT = pipe(
  "plumbing",
  [
    BLEED_START,
    [-60, 16, Z_AXIS + 56],
    [-20, 22, Z_AXIS + 62],
    [42, 22, Z_AXIS + 62],
    [66, -12, Z_AXIS + EDUCTOR_H],
    BLEED_END,
  ],
  3.6,
  {
    bend: 2,
    flangeR: 1.45,
    bellows: [0.22, 0.34, 5],
    bands: [0.55, 0.72],
    valve: [0.44, 3.2],
    maxLength: 18,
    name: "plumbing.bleed-duct",
    free: [true, true],
  },
);
const BLEED_VALVE = valveOn("plumbing", BLEED_DUCT, 0.44, 3.2, { side: [0, 0, 1] });

// 9b. Lube Oil Supply Pipe (from oil cooler y=+68 to gearbox x=-156) with inline valve
const LUBE_SUPPLY = pipe(
  "plumbing",
  [
    [-82, 68, 52],
    [-82, 68, 68],
    [-124, 52, 68],
    [-156, 36, Z_AXIS + 6],
    GBX_SIDE_BOSS,
  ],
  2.5,
  {
    bend: 2.2,
    flangeR: 1.5,
    bands: [0.35, 0.68],
    valve: [0.28, 2.4],
    maxLength: 16,
    name: "plumbing.lube-supply",
    free: [true, true],
  },
);
const LUBE_VALVE = valveOn("plumbing", LUBE_SUPPLY, 0.28, 2.4, { side: [0, 0, 1] });

// 9c. Lube Scavenge Return Pipe (from turbine sump x=+36 to twin filter head)
pipe(
  "plumbing",
  [
    TURB_SUMP_BOSS,
    [36, 46, Z_AXIS + 10],
    [36, 56, 62],
    [19, 58, 54],
    [19, 58, 46],
  ],
  2.2,
  {
    bend: 2.2,
    flangeR: 1.5,
    bellows: [0.3, 0.48, 4],
    bands: [0.7],
    maxLength: 16,
    name: "plumbing.lube-return",
    free: [true, true],
  },
);

// 9d. High-Pressure Fuel Delivery Line (from fuel pump y=-68 to combustor fuel rail x=-16)
const FUEL_DELIVERY = pipe(
  "plumbing",
  [
    [-42, -68, 53],
    [-42, -68, 82],
    [-42, -46, Z_AXIS + 24],
    [-16, -36, Z_AXIS + 28],
    cylPt(FUEL_RAIL_S, FUEL_RAIL_R, 145),
  ],
  2.2,
  {
    bend: 2.2,
    flangeR: 1.5,
    bands: [0.5],
    valve: [0.32, 2.2],
    maxLength: 16,
    name: "plumbing.fuel-line",
    free: [true, true],
  },
);
const FMV = valveOn("plumbing", FUEL_DELIVERY, 0.32, 2.2, { side: [0, 0, 1] });

// 9e. 7-Port Instrumentation Manifold Block & 7 Sense Lines
const BLOCK = { x: -8, y: 42, w: 18, d: 9, r: 1.2 };
const BLOCK_Z = Z_AXIS + 28;
boxAt("plumbing", BLOCK, BLOCK_Z, 10, {}, {
  name: "plumbing.block",
  bias: 0.4,
  extra:
    Ln(k.planOutline(k.insetPlan(BLOCK, 1.2), BLOCK_Z + 10, P, 2), { tone: "faint" }) +
    Dots([0, 1, 2, 3, 4].map((i) => at([BLOCK.x + 2.5 + i * 3.2, BLOCK.y + BLOCK.d, BLOCK_Z + 5])), { size: 0.48, tone: "hi" }),
});
const senses = [
  [GBX_TOP_BOSS, [-156, 0, Z_AXIS + 44], [-88, 28, Z_AXIS + 44], [BLOCK.x + 2, BLOCK.y + 4, BLOCK_Z + 16], [BLOCK.x + 2, BLOCK.y + 4, BLOCK_Z + 10]],
  [IGV_SERVO_BOSS, [-103.5, -18, Z_AXIS + 48], [-52, 24, Z_AXIS + 46], [BLOCK.x + 5, BLOCK.y + 4, BLOCK_Z + 16], [BLOCK.x + 5, BLOCK.y + 4, BLOCK_Z + 10]],
  [COMP_SENSE_BOSS, [-36, 20, Z_AXIS + 42], [-18, 34, Z_AXIS + 42], [BLOCK.x + 8, BLOCK.y + 4, BLOCK_Z + 15], [BLOCK.x + 8, BLOCK.y + 4, BLOCK_Z + 10]],
  [COMB_SENSE_BOSS, [11, 14, Z_AXIS + 46], [4, 34, Z_AXIS + 44], [BLOCK.x + 11, BLOCK.y + 4, BLOCK_Z + 15], [BLOCK.x + 11, BLOCK.y + 4, BLOCK_Z + 10]],
  [EGT_BOSS[65], [54, 18, Z_AXIS + 44], [24, 36, Z_AXIS + 42], [BLOCK.x + 14, BLOCK.y + 4, BLOCK_Z + 15], [BLOCK.x + 14, BLOCK.y + 4, BLOCK_Z + 10]],
  [EGT_BOSS[25], [54, 36, Z_AXIS + 22], [22, 46, BLOCK_Z - 6], [BLOCK.x + 13, BLOCK.y + 4, BLOCK_Z - 6], [BLOCK.x + 13, BLOCK.y + 4, BLOCK_Z]],
  [[19, 68, 80], [19, 54, 92], [-4, 46, BLOCK_Z - 6], [BLOCK.x + 4, BLOCK.y + 4, BLOCK_Z - 6], [BLOCK.x + 4, BLOCK.y + 4, BLOCK_Z]],
];
senses.forEach((pts, idx) => {
  pipe("plumbing", pts, 0.75, { name: `plumbing.sense${idx}`, flangeR: 1.8, bend: 3.5, flanges: [true, false], free: [true, false] });
});

// 3 Piezoresistive Transducers on the Compressor & Turbine Casing
for (const [s, deg, r] of [[-78, 42, 35.6], [-46, 38, 31.8], [42.8, 45, 35.5]]) {
  const face = boss("plumbing", cylPt(s, r, deg), cylDir(deg), 1.6, 2.4);
  const F = G.frameAlong(face, cylDir(deg));
  const meridian = [[0, 0], [0, 1.9], [1.2, 2.2], [5.2, 2.2], [6, 1.5], [6, 0]];
  put("plumbing", G.add3(face, G.mul3(cylDir(deg), 3)), S(G.lathe(meridian, F, P, { steps: 20, smooth: { rows: 3 } }), { tone: "hi" }), {
    bias: 0.3,
    name: `plumbing.transducer${s}`,
    shapes: [record(A.body(F, meridian, { name: `plumbing.transducer${s}` }))],
  });
}

// ============================================================================
// 10. FADEC DIGITAL CONTROLLER & CLAMPED HARNESS (controller: y = -74)
// ============================================================================
const BOX = { x: 6, y: -82, w: 38, d: 16, r: 1.8 };
const BOX_Z = 56;
const BOX_H = 32;
const CTRL = PIECES.controller.move;
boxAt("controller", BOX, BOX_Z, BOX_H, { inner: Ln(k.sideSeam(BOX, BOX_Z + BOX_H - 6, P, 3), { tone: "faint" }) }, {
  name: "controller.box",
  bevel: 0.8,
  extra:
    Ln(k.planOutline(k.insetPlan(BOX, 2.2), BOX_Z + BOX_H, P, 3), { tone: "faint" }) +
    Ln([0, 1, 2].map((row) => k.onTop([[BOX.x + 5, BOX.y + 4 + row * 2.6], [BOX.x + (row === 1 ? 22 : 30), BOX.y + 4 + row * 2.6]], BOX_Z + BOX_H, P)).join(""), { tone: "lo", free: true }) +
    Dots(k.corners(BOX, 2.5).map(([x, y]) => at([x, y, BOX_Z + BOX_H])), { size: 0.45 }),
});
const JBOX = { x: -16, y: -80, w: 14, d: 12, r: 1.4 };
boxAt("controller", JBOX, 62, 16, {}, {
  name: "controller.jbox",
  extra: Ln(k.planOutline(k.insetPlan(JBOX, 1.6), 78, P, 2), { tone: "faint" }) + Dots(k.corners(JBOX, 2).map(([x, y]) => at([x, y, 78])), { size: 0.4 }),
});
const CONNECTORS = [
  [BOX.x + 6, BOX_Z + 8],
  [BOX.x + 14, BOX_Z + 8],
  [BOX.x + 22, BOX_Z + 8],
  [BOX.x + 30, BOX_Z + 8],
  [BOX.x + 10, BOX_Z + 20],
  [BOX.x + 26, BOX_Z + 20],
];
const CONN_Y = BOX.y + BOX.d;
for (const [x, z] of CONNECTORS) {
  const F = G.frameOf([x, CONN_Y, z], [0, 1, 0], [1, 0, 0], [0, 0, 1]);
  const id = nameFor("controller.connector");
  put("controller", [x, CONN_Y + 2, z], S(G.disc(0, 4, 2.4, F, P), { tone: "hi" }) + Ln(G.circleOf(F, 4, 1.2, P, 14), { tone: "faint" }), {
    bias: 0.4,
    name: id,
    shapes: [record(A.disc(F, 0, 4, 2.4, { name: id }))],
  });
}
const plug = (index) => [CONNECTORS[index][0], CONN_Y + 4, CONNECTORS[index][1]];
const CLAMPS = [-72, -48, -18, 12].map((sx) => ({
  centre: [sx, -24, Z_AXIS + 34],
  axis: [1, 0, 0],
  radius: 3.6,
}));
for (const { centre, axis, radius } of CLAMPS) clampAt("controller", centre, axis, radius, { move: CTRL, bundle: "harness" });

cable("controller", [plug(0), [plug(0)[0], -48, 84], [12, -24, Z_AXIS + 34], [-72, -24, Z_AXIS + 34], [-120, -22, Z_AXIS + 28], GBX_REAR_BOSS], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-gbx",
  bundle: "harness",
  clamps: CLAMPS,
  shells: [false, true],
  free: [false, true],
});
cable("controller", [plug(1), [plug(1)[0], -46, 86], [12, -23, Z_AXIS + 35], [-48, -23, Z_AXIS + 35], BLEED_VALVE.approach, BLEED_VALVE.port], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-bleed",
  bundle: "harness",
  clamps: CLAMPS,
  shells: [false, true],
  free: [false, true],
});
cable("controller", [plug(2), [plug(2)[0], -44, 88], [12, -25, Z_AXIS + 33], [-18, -25, Z_AXIS + 33], IGNITER_A], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-ignA",
  bundle: "harness",
  clamps: CLAMPS,
  shells: [false, true],
  free: [false, true],
});
cable("controller", [plug(3), [plug(3)[0], -42, 90], [18, -18, Z_AXIS + 36], IGNITER_B], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-ignB",
  shells: [false, true],
  free: [false, true],
});
cable("controller", [plug(4), [plug(4)[0], -56, 92], FMV.approach, FMV.port], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-fmv",
  shells: [false, true],
  free: [false, true],
});
cable("controller", [plug(5), [plug(5)[0], -38, 96], [24, 22, Z_AXIS + 42], LUBE_VALVE.approach, LUBE_VALVE.port], {
  move: CTRL,
  bend: 4,
  name: "controller.harness-lube",
  shells: [false, true],
  free: [false, true],
});
cable("controller", [[-9, -74, 78], [-9, -74, 92], [14, -74, 92], [14, -74, BOX_Z + BOX_H]], {
  move: CTRL,
  bend: 3,
  name: "controller.cable-jbox",
});

// Settle depth order across assembled (0) and exploded (1) states
A.settle(R, P, { states: [0, 1], step: 0.6 });
items.sort((a, b) => a.key - b.key);
const groups = items.map((item, index) => {
  const [mx, my, mz] = item.move;
  return `<g class="it" data-piece="${item.piece}"${item.ride !== item.piece ? ` data-ride="${item.ride}"` : ""} data-k="${item.key.toFixed(2)}" data-m="${mx.toFixed(1)},${my.toFixed(1)},${mz.toFixed(1)}" data-i="${index}">${item.svg}</g>`;
});

const LABEL_TEXT =
  "GT-400 horizontal industrial turboshaft generator skid: a slotted steel bedplate on ten mounts with front and rear pedestal trunnions supporting a horizontal gas turbine along the X-axis. From left to right sit the 19.6:1 epicyclic reduction gearbox, the radial air intake bellmouth with 20 variable inlet guide vanes, the 6-stage axial compressor with its 360-degree mid-stage bleed ring, the 10-can annular combustor and fuel rail, the 2-stage Inconel turbine module, and the upturned exhaust collector with a 64-flute conical vertical stack. Flanking the bedplate sit the shell-and-tube lube oil cooler with duplex spin-on filters on the left and the high-pressure fuel pump and dual-channel FADEC controller with its clamped harness on the right.";

const backSvg = k.figureSvg({ width: W, height: H, label: LABEL_TEXT, body: back, className: "gt-back" });
const frontSvg = `<svg xmlns="http://www.w3.org/2000/svg" class="iso-svg gt-front" viewBox="0 0 ${W} ${H}" aria-hidden="true"><g class="gt-engine">${groups.join("")}</g></svg>`;

const unit = (vector) => {
  const o = at([0, 0, 0]);
  const p = at(vector);
  return [p[0] - o[0], p[1] - o[1]];
};
const DATA = {
  W,
  H,
  V,
  EX: unit([1, 0, 0]),
  EY: unit([0, 1, 0]),
  EZ: unit([0, 0, 1]),
  pieces: Object.fromEntries(Object.entries(PIECES).map(([id, piece]) => [id, { name: piece.name, say: piece.say }])),
  stagger: STAGGER,
  spring: SPRING,
  order: ["gearbox", "intake", "compressor", "combustor", "turbine", "exhaust", "lube", "fuel", "plumbing", "controller"],
};

const PARTS = DATA.order.map((id, index) => `<button type="button" class="gt-part" data-part="${id}"><span class="gt-num">${String(index + 1).padStart(2, "0")}</span>${PIECES[id].name}</button>`).join("");
const corners = `<div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig">Fig 2</span><span class="iso-plate-corner" data-corner="title">GT-400 · horizontal turboshaft skid</span><span class="iso-plate-corner" data-corner="readout" data-readout>1,450 kW · 14.8 : 1 PR · cold</span></div>`;
const controls = `<div class="gt-controls"><button type="button" class="gt-fire" data-fire><span class="gt-lamp" aria-hidden="true"></span><span data-fire-label>Start Turbine</span></button><span class="gt-hint">Hover or press Space to explode into 10 assemblies</span></div>`;
const stage = `<div class="gt-stage" tabindex="0" role="slider" aria-label="GT-400 horizontal industrial turboshaft skid. Hover or press Space and arrow keys to explode the turbine into 10 sub-assemblies; press S or Start Turbine to spool up to 29,400 rpm." aria-valuemin="0" aria-valuemax="${DATA.order.length}" aria-valuenow="0" aria-valuetext="1,450 kW · 14.8 : 1 PR · cold">${backSvg}${frontSvg}</div>`;
const caption =
  "GT-400 is a horizontal twin-spool industrial turboshaft package rated at 1,450 kW shaft power, 14.8 : 1 overall pressure ratio, and 29,400 rpm gas-generator speed reduced to 1,500 rpm by a 19.6 : 1 epicyclic planetary gearbox. Ambient air enters the radial bellmouth past 20 variable inlet guide vanes, is compressed across six axial Ti-6Al-4V stages with a 360° anti-surge bleed manifold, burns with jet fuel in a 10-can annular combustor, expands through a 2-stage Inconel turbine, and exits up a 64-flute conical diffuser stack.";
const body = `<figure class="iso-figure gt"><div class="iso-plate">${existsSync(join(HERE, "gas-turbine-poster-a4.pdf")) ? pdfButton("gas-turbine-poster-a4.pdf") : ""}${corners}${stage}${controls}</div><figcaption class="iso-legend"><span class="gt-parts">${PARTS}</span><span class="iso-caption">${caption}</span></figcaption></figure>`;

const CSS = readFileSync(join(HERE, "gt.css"), "utf8");
const LIVE = readFileSync(join(HERE, "live.js"), "utf8").replace("__DATA__", JSON.stringify(DATA));
const page = k.pageHtml({ title: "GT-400 Horizontal Turboshaft Skid", theme: THEME, body: `<style>${CSS}</style>${body}`, script: LIVE, width: 980 });
const name = THEME === "light" ? "gas-turbine-light.html" : "gas-turbine.html";
writeFileSync(join(HERE, name), page);
console.log("wrote", name, `${(page.length / 1024).toFixed(0)} KB`, `${items.length} items`);
