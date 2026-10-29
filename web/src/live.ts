// Live state fed by the WebSocket: agent status, inbox, session events, workflow runs.
import { useSyncExternalStore } from "react";
import { api, getToken } from "./api";
import type { InboxItem, LiveState, SessionEvent, SessionInfo, WorkflowRun } from "./types";

export type Live = {
  connected: boolean;
  statuses: Record<string, LiveState>;
  inbox: InboxItem[];
  sessions: Record<string, SessionInfo>;
  events: Record<string, SessionEvent[]>;
  deltas: Record<string, string>;
  workflowRuns: Record<string, WorkflowRun>;
  announcement: string;
  dexVersion: number; // bumps when the resource list may have changed
};

let state: Live = {
  connected: false,
  statuses: {},
  inbox: [],
  sessions: {},
  events: {},
  deltas: {},
  workflowRuns: {},
  announcement: "",
  dexVersion: 0,
};

const listeners = new Set<() => void>();

function set(patch: Partial<Live>) {
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
}

export function useLive<T>(selector: (s: Live) => T): T {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => selector(state),
  );
}

export function seedSessionEvents(id: string, events: SessionEvent[], info: SessionInfo) {
  set({ events: { ...state.events, [id]: events }, sessions: { ...state.sessions, [id]: info } });
}

export function refreshInbox() {
  api<InboxItem[]>("/api/inbox")
    .then((inbox) => set({ inbox }))
    .catch(() => undefined);
}

type Msg = {
  topic: string;
  agent?: string;
  state?: LiveState["state"];
  since?: number | null;
  detail?: string | null;
  event?: SessionEvent & { type: string };
  session_id?: string;
  session?: SessionInfo;
  item?: InboxItem;
  run?: WorkflowRun;
};

function handle(msg: Msg) {
  switch (msg.topic) {
    case "status": {
      if (!msg.agent || !msg.state) return;
      const next: LiveState = { state: msg.state, since: msg.since ?? null, detail: msg.detail ?? null };
      const before = state.statuses[msg.agent]?.state;
      set({
        statuses: { ...state.statuses, [msg.agent]: next },
        announcement: before !== msg.state ? `${msg.agent}: ${msg.state}` : state.announcement,
      });
      break;
    }
    case "inbox": {
      if (!msg.item) return;
      const others = state.inbox.filter((i) => i.id !== msg.item?.id);
      set({
        inbox: msg.item.status === "pending" ? [...others, msg.item] : others,
        announcement: msg.item.status === "pending" ? `Nuevo pendiente de ${msg.item.agent}: ${msg.item.title}` : state.announcement,
      });
      break;
    }
    case "session": {
      const id = msg.session_id;
      const ev = msg.event;
      if (!id || !ev) return;
      if (ev.type === "delta") {
        set({ deltas: { ...state.deltas, [id]: (state.deltas[id] ?? "") + (ev.text ?? "") } });
      } else {
        const rest = { ...state.deltas };
        if (ev.type === "assistant" || ev.type === "result") delete rest[id];
        set({ events: { ...state.events, [id]: [...(state.events[id] ?? []), ev] }, deltas: rest });
      }
      break;
    }
    case "session_status":
      if (msg.session) set({ sessions: { ...state.sessions, [msg.session.id]: { ...state.sessions[msg.session.id], ...msg.session } } });
      break;
    case "workflow_run":
      if (msg.run) set({ workflowRuns: { ...state.workflowRuns, [msg.run.id]: msg.run } });
      break;
  }
}

let socket: WebSocket | null = null;
let retry = 0;

export function connectLive(): void {
  const token = getToken();
  if (!token || socket) return;
  const url = `ws://${window.location.host}/ws?t=${encodeURIComponent(token)}`;
  const ws = new WebSocket(url);
  socket = ws;
  ws.onopen = () => {
    retry = 0;
    set({ connected: true, dexVersion: state.dexVersion + 1 });
    api<Record<string, LiveState>>("/api/status")
      .then((statuses) => set({ statuses }))
      .catch(() => undefined);
    refreshInbox();
  };
  ws.onmessage = (e) => {
    try {
      handle(JSON.parse(String(e.data)) as Msg);
    } catch {
      /* ignore malformed frames */
    }
  };
  ws.onclose = () => {
    socket = null;
    set({ connected: false });
    retry = Math.min(retry + 1, 6);
    window.setTimeout(connectLive, 500 * 2 ** retry);
  };
  ws.onerror = () => ws.close();
}
