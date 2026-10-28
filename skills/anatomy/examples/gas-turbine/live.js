const D = __DATA__;
const root = document.querySelector(".gt");
const stage = root.querySelector(".gt-stage");
const front = stage.querySelector(".gt-front");
const engine = front.querySelector(".gt-engine");
const readout = root.querySelector("[data-readout]");
const fireButton = root.querySelector("[data-fire]");
const fireLabel = root.querySelector("[data-fire-label]");
const partButtons = [...root.querySelectorAll(".gt-part")];
const still = matchMedia("(prefers-reduced-motion: reduce)");

const nodes = [...engine.querySelectorAll(".it")].map((el) => ({
  el,
  piece: el.dataset.piece,
  ride: el.dataset.ride || el.dataset.piece,
  key: Number(el.dataset.k),
  m: el.dataset.m.split(",").map(Number),
  index: Number(el.dataset.i),
  shown: "",
}));
for (const node of nodes) node.lift = node.m[0] * D.V[0] + node.m[1] * D.V[1] + node.m[2] * D.V[2];
let order = nodes.map((_, index) => index);

const IDS = Object.keys(D.pieces);
const STAGGER = D.stagger;
const SPRING = D.spring;
const piece = Object.fromEntries(IDS.map((id) => [id, { x: 0, v: 0, target: 0, pending: null }]));

let clock = 0;
let apart = false;
let selected = null;
let running = false;
let spool = 0;
let spoolTarget = 0;
let frame = 0;
let last = 0;
let visible = true;

function say(text) {
  if (readout.textContent !== text) readout.textContent = text;
}

function formatRun(s) {
  if (s < 0.02) return "0 rpm · 24 °C EGT · cold";
  const n1 = Math.round(s * 29400).toLocaleString("en-US");
  const egt = Math.round(24 + s * 616);
  const kw = Math.round(s * s * 1450).toLocaleString("en-US");
  return `${n1} rpm · ${egt} °C EGT · ${kw} kW`;
}

function describe() {
  const text = selected
    ? D.pieces[selected].say
    : running
      ? formatRun(spool)
      : apart
        ? `apart · ${D.order.length} assemblies`
        : "1,450 kW · 14.8 : 1 PR · cold";
  say(text);
  if (stage.getAttribute("aria-valuetext") !== text) stage.setAttribute("aria-valuetext", text);
}

function setApart(on) {
  if (apart === on) return;
  apart = on;
  const goal = on ? 1 : 0;
  let index = 0;
  for (const id of on ? STAGGER : [...STAGGER].reverse()) {
    if (!piece[id]) continue;
    if (piece[id].target === goal) piece[id].pending = null;
    else piece[id].pending = { value: goal, at: clock + (still.matches ? 0 : index++ * SPRING.stagger) };
  }
  describe();
  run();
}

function select(id) {
  if (id === "stand") id = null;
  if (selected === id) return;
  selected = id;
  for (const node of nodes) {
    if (id !== null && node.piece === id) node.el.setAttribute("data-on", "");
    else node.el.removeAttribute("data-on");
  }
  if (id) stage.setAttribute("data-focus", "");
  else stage.removeAttribute("data-focus");
  partButtons.forEach((button) => (button.dataset.part === id ? button.setAttribute("data-on", "") : button.removeAttribute("data-on")));
  stage.setAttribute("aria-valuenow", String(id ? D.order.indexOf(id) + 1 : 0));
  describe();
}

function toggleRun() {
  running = !running;
  spoolTarget = running ? 1 : 0;
  if (running) root.setAttribute("data-running", "");
  else root.removeAttribute("data-running");
  fireLabel.textContent = running ? "Shut Down" : "Start Turbine";
  describe();
  run();
}

function steerSpring(state, dt, calm) {
  if (state.pending && clock >= state.pending.at) {
    state.target = state.pending.value;
    state.pending = null;
  }
  if (calm) {
    state.x = state.target;
    state.v = 0;
    return false;
  }
  for (let index = 0; index < SPRING.substeps; index++) {
    const h = dt / SPRING.substeps;
    state.v += ((state.target - state.x) * SPRING.stiffness - state.v * SPRING.damping) * h;
    state.x += state.v * h;
  }
  if (Math.abs(state.target - state.x) < 2e-4 && Math.abs(state.v) < 2e-4) {
    state.x = state.target;
    state.v = 0;
    return state.pending !== null;
  }
  return true;
}

function place() {
  for (const node of nodes) {
    const share = piece[node.ride].x;
    const tx = (D.EX[0] * node.m[0] + D.EY[0] * node.m[1] + D.EZ[0] * node.m[2]) * share;
    const ty = (D.EX[1] * node.m[0] + D.EY[1] * node.m[1] + D.EZ[1] * node.m[2]) * share;
    const text = share === 0 ? "" : `translate(${tx.toFixed(2)} ${ty.toFixed(2)})`;
    if (text !== node.shown) {
      node.shown = text;
      if (text) node.el.setAttribute("transform", text);
      else node.el.removeAttribute("transform");
    }
  }
  const next = nodes.map((_, index) => index).sort((a, b) => nodes[a].key + nodes[a].lift * piece[nodes[a].ride].x - (nodes[b].key + nodes[b].lift * piece[nodes[b].ride].x));
  if (next.some((index, at) => index !== order[at])) {
    const fragment = document.createDocumentFragment();
    for (const index of next) fragment.appendChild(nodes[index].el);
    engine.appendChild(fragment);
    order = next;
  }
}

function tick(now) {
  const dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60;
  last = now;
  clock += dt;
  const calm = still.matches;
  let moving = false;
  for (const id of IDS) {
    if (steerSpring(piece[id], dt, calm)) moving = true;
  }
  if (Math.abs(spoolTarget - spool) > 1e-3) {
    spool += (spoolTarget - spool) * Math.min(1, dt * 2.2);
    moving = true;
    describe();
  } else {
    spool = spoolTarget;
  }
  place();
  frame = visible && moving ? requestAnimationFrame(tick) : 0;
}

function run() {
  if (!frame && visible) {
    last = 0;
    frame = requestAnimationFrame(tick);
  }
}

stage.addEventListener("pointerenter", () => setApart(true));
stage.addEventListener("pointerleave", () => {
  select(null);
  setApart(false);
});
stage.addEventListener("pointermove", (e) => {
  const hit = e.target.closest(".it");
  if (!apart) setApart(true);
  select(hit ? hit.dataset.piece : null);
});
stage.addEventListener("click", (e) => {
  const hit = e.target.closest(".it");
  if (hit && hit.dataset.piece !== "stand") {
    setApart(true);
    select(selected === hit.dataset.piece ? null : hit.dataset.piece);
  } else {
    setApart(!apart);
    if (!apart) select(null);
  }
});

partButtons.forEach((button) => {
  button.addEventListener("pointerenter", () => {
    setApart(true);
    select(button.dataset.part);
  });
  button.addEventListener("click", () => {
    setApart(true);
    select(selected === button.dataset.part ? null : button.dataset.part);
  });
});

fireButton.addEventListener("click", () => toggleRun());

stage.addEventListener("keydown", (e) => {
  if (e.key === " ") {
    e.preventDefault();
    setApart(!apart);
    if (!apart) select(null);
  } else if (e.key === "s" || e.key === "S" || e.key === "i" || e.key === "I") {
    e.preventDefault();
    toggleRun();
  } else if (e.key === "Escape") {
    e.preventDefault();
    select(null);
    setApart(false);
    if (running) toggleRun();
  } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
    e.preventDefault();
    setApart(true);
    const idx = selected ? (D.order.indexOf(selected) + 1) % D.order.length : 0;
    select(D.order[idx]);
  } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
    e.preventDefault();
    setApart(true);
    const idx = selected ? (D.order.indexOf(selected) - 1 + D.order.length) % D.order.length : D.order.length - 1;
    select(D.order[idx]);
  }
});

place();
describe();
