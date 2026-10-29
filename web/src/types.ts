export type Kind = "agent" | "skill";

export type LiveState = {
  state: "inactivo" | "trabajando" | "entrenando" | "esperando" | "error";
  since: number | null;
  detail: string | null;
};

export type Resource = {
  id: string;
  kind: Kind;
  name: string;
  description: string;
  source: "user" | "project" | "plugin";
  plugin: string | null;
  path: string;
  model: string | null;
  tools: string[];
  valid: boolean;
  error: string | null;
  archetype: string;
  hobby: string;
  clients: string[];
  status?: LiveState;
  body?: string;
  stats?: { runs: number; done: number; success_rate: number | null; cost_usd: number; last: number | null };
};

export type DexResponse = { resources: Resource[]; counts: { agents: number; skills: number } };

export type InboxItem = {
  id: string;
  kind: "permission" | "approval";
  title: string;
  agent: string;
  detail: Record<string, unknown>;
  created: number;
  status: "pending" | "resolved";
  session_id: string | null;
  workflow_run_id: string | null;
};

export type SessionStatus = "starting" | "running" | "idle" | "done" | "limit" | "error" | "cancelled";

export type SessionInfo = {
  id: string;
  agent: string;
  agent_id: string;
  kind: "chat" | "task";
  policy: "ask" | "readonly";
  status: SessionStatus;
  created: number;
  finished: number | null;
  cost_usd: number;
  turns: number;
  max_turns: number;
  max_budget_usd: number;
  workflow_run_id: string | null;
  events?: SessionEvent[];
};

export type SessionEvent = {
  ts: number;
  type: string;
  text?: string;
  name?: string;
  id?: string;
  tool?: string;
  input?: unknown;
  allow?: boolean;
  is_error?: boolean;
  message?: string;
  limit?: string | null;
  cost_usd?: number;
  turns?: number;
  subtype?: string;
};

export type RunRow = {
  id: string;
  agent: string;
  kind: string;
  status: string;
  created: number;
  finished: number | null;
  cost_usd: number | null;
  turns: number | null;
  prompt: string | null;
  result: string | null;
};

export type GlossaryEntry = {
  slug: string;
  id: string;
  tipo: Kind;
  nombre: string;
  descripcion: string;
  repo: string;
  commit: string;
  ruta: string;
  licencia: string;
  clientes: string[];
  categorias: string[];
  revision: { fecha: string; resultado: "ok" | "aviso" | "bloqueado"; notas: string };
  archivos_total: number;
  instalada: boolean;
  capturada_por_dex: boolean;
};

export type CapturePreview = {
  slug: string;
  nombre: string;
  tipo: Kind;
  repo: string;
  commit: string;
  licencia: string;
  revision: GlossaryEntry["revision"];
  archivos: { origen: string; destino: string; bytes: number; sha: string; requiere_atencion: boolean }[];
  conflictos: string[];
  total_bytes: number;
};

export type WorkflowStep = {
  type: "agent" | "human";
  agent: string | null;
  instruction: string;
  policy: "ask" | "readonly";
  max_turns: number;
  max_budget_usd: number;
};

export type Workflow = {
  id: string;
  name: string;
  goal: string;
  steps: WorkflowStep[];
  max_total_budget_usd: number;
};

export type WorkflowRun = {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: "running" | "waiting_human" | "done" | "failed" | "rejected" | "cancelled" | "interrupted" | "limit";
  created: number;
  finished: number | null;
  cost_usd: number;
  error: string | null;
  steps: {
    index: number;
    type: "agent" | "human";
    agent: string | null;
    instruction: string;
    status: string;
    output: string | null;
    session_id: string | null;
    cost_usd: number;
  }[];
};

export type Settings = {
  version: string;
  claude_home: string;
  claude_home_exists: boolean;
  project_dir: string;
  data_dir: string;
  claude_cli: string | null;
  model_override: string | null;
  features: { id: string; nombre: string; estado: "disponible" | "beta" | "en diseño" }[];
};
