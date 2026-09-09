const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type User = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
};
export type DashboardSummary = {
  deals_today: number;
  excellent_deals: number;
  monitored_products: number;
  alerts_sent: number;
  online_stores: number;
};
export type MercadoLivreStatus = {
  connected: boolean;
  provider: "mercadolivre";
  expires_at: string | null;
  provider_user_id: string | null;
};
export type SteamStatus = {
  configured: boolean;
  provider: "steam";
  store_exists: boolean;
};
export type SteamSyncResult = {
  catalog_items_seen: number;
  catalog_items_created: number;
  catalog_items_updated: number;
};

export type ProviderIntegrationStatus = {
  provider: string;
  name: string;
  store_slug: string | null;
  channel: string;
  state:
    | "connected"
    | "configured"
    | "credentials_required"
    | "approval_required"
    | "partnership_required";
  configured: boolean;
  connected: boolean;
  store_exists: boolean | null;
  capabilities: string[];
  note: string;
  setup_url: string | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams))
    headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const body = await response.text();
  let payload: ({ detail?: string } & T) | undefined;
  try {
    payload = body ? (JSON.parse(body) as { detail?: string } & T) : undefined;
  } catch {
    payload = undefined;
  }
  if (!response.ok)
    throw new ApiError(
      payload?.detail ?? "Nao foi possivel concluir a operacao.",
      response.status,
    );
  return payload as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  register: (full_name: string, email: string, password: string) =>
    request<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }),
    }),
  me: (token: string) => request<User>("/api/v1/auth/me", {}, token),
  dashboard: (token: string) =>
    request<DashboardSummary>("/api/v1/dashboard/summary", {}, token),
  mercadoLivreStatus: (token: string) =>
    request<MercadoLivreStatus>(
      "/api/v1/integrations/mercadolivre/status",
      {},
      token,
    ),
  mercadoLivreAuthorize: (token: string) =>
    request<{ authorization_url: string }>(
      "/api/v1/integrations/mercadolivre/authorize",
      {},
      token,
    ),
  mercadoLivreDisconnect: (token: string) =>
    request<void>(
      "/api/v1/integrations/mercadolivre",
      { method: "DELETE" },
      token,
    ),
  steamStatus: (token: string) =>
    request<SteamStatus>("/api/v1/integrations/steam/status", {}, token),
  steamSync: (token: string) =>
    request<SteamSyncResult>(
      "/api/v1/integrations/steam/sync?max_results=100",
      { method: "POST" },
      token,
    ),
  providers: (token: string) =>
    request<ProviderIntegrationStatus[]>(
      "/api/v1/integrations/providers",
      {},
      token,
    ),
};
