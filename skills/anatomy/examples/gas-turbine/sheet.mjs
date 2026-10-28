const piece = (id) => `.it[data-piece="${id}"]`;
const engine = { view: "apart", layers: [1] };

export default {
  page: "gas-turbine-light.html",
  out: "gas-turbine",
  layers: ".gt-stage > svg.gt-back, .gt-stage > svg.gt-front",
  views: {
    rest: {},
    apart: { actions: [["key", " "], ["wait", 1800]], reset: [["key", " "], ["wait", 1800]] },
  },

  name: "GT-400",
  title: "GT-400: how a horizontal turboshaft generator works",
  number: "AN-009",
  tagline: "Twin-spool axial turboshaft skid",
  question: "How does a gas turbine turn fuel into 1,450 kW of shaft torque?",
  lead: "Air drawn through a radial bellmouth is squeezed to 14.8 bar by six axial compressor stages, mixed with atomized fuel in a ten-can annular combustor, and expanded through a two-stage Inconel turbine that spins a 19.6 : 1 planetary reduction gearbox.",
  quote: "Continuous Brayton-cycle compression, combustion and expansion on one horizontal axis",
  numbers: [
    ["1,450", "kW", "continuous shaft power"],
    ["14.8", ": 1", "axial pressure ratio"],
    ["29,400", "rpm", "gas-generator spool"],
    ["1,500", "rpm", "gearbox output shaft"],
    ["640", "°C", "exhaust gas temp (EGT)"],
  ],
  spec: [
    ["Configuration", "Horizontal twin-spool turboshaft"],
    ["Compressor", "6-stage axial + IGVs, 14.8 : 1"],
    ["Combustor", "10-can annular, dual igniters"],
    ["Turbine", "2-stage Inconel 718 (HP + PT)"],
    ["Gearbox", "Epicyclic planetary, 19.6 : 1"],
    ["Lubrication", "Shell-and-tube cooler + duplex filters"],
    ["Control", "Dual-channel FADEC + 7 sense lines"],
  ],
  why: {
    title: "Why bleed air from the middle of the compressor?",
    text: "During start-up the rear compressor stages choke before the front stages reach design speed. Opening the 360° mid-stage bleed ring through the hydroformed bellows duct vents excess air into the exhaust eductor, preventing compressor surge.",
  },

  parts: [
    { id: "gearbox", name: "Epicyclic reduction gearbox", say: "19.6 : 1 planetary gear train reducing 29,400 rpm to 1,500 rpm.", select: piece("gearbox") },
    { id: "intake", name: "Radial intake bellmouth & IGVs", say: "Aerodynamic inlet cone and 20 variable guide vanes.", select: piece("intake") },
    { id: "compressor", name: "6-stage axial compressor & bleed ring", say: "Six Ti-6Al-4V axial stages and 360° mid-stage bleed torus.", select: piece("compressor") },
    { id: "combustor", name: "10-can annular combustor & fuel rail", say: "Ten combustor cans fed by a stainless fuel ring and dual igniters.", select: piece("combustor") },
    { id: "turbine", name: "2-stage HP & power turbine module", say: "Inconel 718 gas-generator and power turbine with 6 EGT probes.", select: piece("turbine") },
    { id: "exhaust", name: "Exhaust collector & fluted uptake stack", say: "Horizontal plenum and 64-flute conical vertical exhaust diffuser.", select: piece("exhaust") },
    { id: "lube", name: "Shell-and-tube oil cooler & twin filters", say: "Finned heat exchanger, scavenge volute and duplex spin-on filters.", select: piece("lube") },
    { id: "fuel", name: "High-pressure fuel pump & metering skid", say: "Finned brushless motor, spiral fuel pump and metering globe valve.", select: piece("fuel") },
    { id: "plumbing", name: "Anti-surge bleed, lube & sense manifold", say: "Bellows bleed duct, oil loop and 7 sense lines into a gauge block.", select: piece("plumbing") },
    { id: "controller", name: "FADEC controller & clamped harness", say: "Digital turbine controller, junction box and 4-clamp braided harness.", select: piece("controller") },
  ],

  main: { ...engine },
  inset: { label: "Assembled", view: "rest" },
  steps: [
    { ...engine, title: "Induction & variable IGVs", text: "Filtered air enters the flared bellmouth past the nose cone while 20 variable inlet guide vanes set the swirl angle into Stage 1.", focus: ["intake", "compressor"] },
    { ...engine, title: "6-stage axial compression", text: "Six Ti-6Al-4V rotor/stator stages raise pressure to 14.8 bar; the 360° bleed ring and bellows valve prevent low-speed surge.", focus: ["compressor", "plumbing"] },
    { ...engine, title: "Annular 10-can combustion", text: "High-pressure fuel from the metering skid sprays through the circular rail into ten combustor cans and lights off on dual igniters.", focus: ["combustor", "fuel"] },
    { ...engine, title: "2-stage turbine expansion", text: "Hot gas expands through the HP stage to drive the compressor and through the power turbine to spin the 19.6 : 1 planetary gearbox.", focus: ["turbine", "gearbox"] },
    { ...engine, title: "Exhaust & closed-loop cooling", text: "Spent gas exits the 64-flute vertical stack while the shell-and-tube cooler and FADEC controller regulate oil temp and EGT.", focus: ["exhaust", "lube", "controller"] },
  ],
  assemblies: [
    { ...engine, title: "Cold section & drive train", text: "The 19.6 : 1 epicyclic reduction gearbox, radial intake bellmouth, 20 variable IGVs and 6-stage axial compressor sit on the front half of the horizontal shaft.", parts: ["gearbox", "intake", "compressor"] },
    { ...engine, title: "Hot section & exhaust stack", text: "The 10-can annular combustor, 2-stage Inconel turbine module and upturned 64-flute conical exhaust stack convert thermal energy into shaft torque.", parts: ["combustor", "turbine", "exhaust"] },
    { ...engine, title: "Lubrication & fuel skids", text: "Flanking the main bedplate sit the finned shell-and-tube oil cooler with duplex spin-on filters and the high-pressure fuel pump.", parts: ["lube", "fuel"] },
    { ...engine, title: "FADEC controls & process piping", text: "The anti-surge bellows duct, lube lines and seven sense lines join the 4-clamp FADEC harness across the top of the casing.", parts: ["plumbing", "controller"] },
  ],
  details: [
    { ...engine, title: "Epicyclic gearbox & intake", text: "Finned planetary housing coupled to the radial bellmouth and IGV actuator ring.", around: ["gearbox", "intake"], focus: ["gearbox", "intake"] },
    { ...engine, title: "10-can combustor & turbine", text: "Circular fuel rail, bolted injector caps, Inconel turbine barrel and EGT bosses.", around: ["combustor", "turbine"], focus: ["combustor", "turbine"] },
    { ...engine, title: "Oil cooler & duplex filters", text: "Horizontal finned heat exchanger, spiral scavenge volute and twin spin-on canisters.", around: ["lube"], focus: ["lube"] },
  ],
};
