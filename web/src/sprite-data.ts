// Original pixel-art creature, drawn for this project. 16x16 grid.
// Legend: o outline, b body, l light, d dark, w eye white, k pupil, m mouth, a accent, g gray, y yellow, r red.

export const GRID = 16;

export const BASE: string[] = [
  "................",
  ".....oooooo.....",
  "....obbbbbbo....",
  "...obbbbbbbbo...",
  "...obwkbbwkbo...",
  "...obbbbbbbbo...",
  "...oblbmmblbo...",
  "...obbbbbbbbo...",
  "....obbbbbbo....",
  "..oobbbbbbbboo..",
  "..obobbbbbbobo..",
  "...o.obbbbo.o...",
  ".....obbbbo.....",
  ".....oo..oo.....",
  "....ooo..ooo....",
  "................",
];

export const EYES_CLOSED = "...oboobboobo...";
export const EYES_OPEN = BASE[4] as string;

// Overlays replace non-"." cells. They give each archetype a silhouette.
export const ARCHETYPE_OVERLAY: Record<string, Record<number, string>> = {
  investigador: { 0: ".......aa.......", 1: ".....ooaaoo....." },
  constructor: { 1: ".....aaaaaa.....", 2: "....aaaaaaaa...." },
  guardian: { 1: "....a......a....", 2: "....aa....aa...." },
  mensajero: { 1: "....aaaaaaaa....", 2: "...aaaaaaaaaaa.." },
  artista: { 0: ".......aaa......", 1: "....aaaaaaaa....", 2: "....aaaaaaaa...." },
};

export type Prop = { rows: string[]; x: number; y: number };

// Small items drawn next to the creature, per state or hobby.
export const PROPS: Record<string, Prop> = {
  laptop: { x: 10, y: 10, rows: ["gggggg", "gyyyyg", "gggggg", "gggggg"] },
  dumbbell: { x: 11, y: 8, rows: ["g...g", "ggggg", "g...g"] },
  book: { x: 11, y: 9, rows: ["rrrrr", "rwwwr", "rwwwr", "rrrrr"] },
  brush: { x: 11, y: 7, rows: ["...ry", "..ry.", ".ry..", "rr..."] },
  wrench: { x: 11, y: 8, rows: ["gg.gg", ".ggg.", "..g..", "..g.."] },
  shield: { x: 11, y: 8, rows: ["ggggg", "gaaag", ".gag.", "..g.."] },
  envelope: { x: 10, y: 9, rows: ["wwwwww", "wgwwgw", "wwggww", "wwwwww"] },
  question: { x: 13, y: 0, rows: ["yyy", "..y", ".y.", "...", ".y."] },
  alert: { x: 13, y: 0, rows: ["rr", "rr", "rr", "..", "rr"] },
  z: { x: 13, y: 0, rows: ["www", "..w", ".w.", "w..", "www"] },
};

export const HOBBY_PROP: Record<string, string> = {
  investigador: "book",
  constructor: "wrench",
  guardian: "shield",
  mensajero: "envelope",
  artista: "brush",
};
