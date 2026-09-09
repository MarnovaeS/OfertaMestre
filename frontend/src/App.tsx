import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Activity,
  Database,
  LayoutDashboard,
  Link2,
  LoaderCircle,
  LogIn,
  LogOut,
  Plug,
  RefreshCw,
  ShieldCheck,
  Unplug,
  UserPlus,
} from "lucide-react";
import {
  ApiError,
  api,
  type DashboardSummary,
  type MercadoLivreStatus,
  type SteamStatus,
  type User,
} from "./api";
import "./styles.css";

const TOKEN_KEY = "ofertamestre_session_token";
const EMPTY: DashboardSummary = {
  deals_today: 0,
  excellent_deals: 0,
  monitored_products: 0,
  alerts_sent: 0,
  online_stores: 0,
};
type View = "dashboard" | "integrations";
type Health = "checking" | "online" | "offline";

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<Health>("checking");
  const [view, setView] = useState<View>("dashboard");
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    api
      .health()
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
  }, []);
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me(token)
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const authenticated = (value: string) => {
    sessionStorage.setItem(TOKEN_KEY, value);
    setLoading(true);
    setToken(value);
  };
  const logout = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setView("dashboard");
  };

  if (loading)
    return (
      <main className="loading">
        <LoaderCircle className="spin" />
        <span>Carregando sessao</span>
      </main>
    );
  if (!token || !user)
    return <Auth health={health} onAuthenticated={authenticated} />;

  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <nav aria-label="Navegacao principal">
          <Nav
            active={view === "dashboard"}
            icon={<LayoutDashboard />}
            onClick={() => setView("dashboard")}
          >
            Visao geral
          </Nav>
          <Nav
            active={view === "integrations"}
            icon={<Plug />}
            onClick={() => setView("integrations")}
          >
            Integracoes
          </Nav>
        </nav>
        <div className="sidebar-footer">
          <span className="avatar">{initials(user.full_name)}</span>
          <div className="user-copy">
            <strong>{user.full_name}</strong>
            <small>{user.email}</small>
          </div>
          <button
            className="icon-button"
            type="button"
            onClick={logout}
            title="Sair"
          >
            <LogOut />
          </button>
        </div>
      </aside>
      <main className="content">
        <header className="page-header">
          <div>
            <p className="eyebrow">
              {view === "dashboard" ? "Operacao" : "Conectores"}
            </p>
            <h1>{view === "dashboard" ? "Visao geral" : "Integracoes"}</h1>
          </div>
          <HealthBadge health={health} />
        </header>
        {view === "dashboard" ? (
          <Dashboard token={token} />
        ) : (
          <Integrations token={token} />
        )}
      </main>
    </div>
  );
}

function Auth({
  health,
  onAuthenticated,
}: {
  health: Health;
  onAuthenticated: (token: string) => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") await api.register(fullName, email, password);
      const result = await api.login(email, password);
      onAuthenticated(result.access_token);
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : "Nao foi possivel acessar sua conta.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="auth-layout">
      <section className="auth-intro">
        <Brand large />
        <div>
          <p className="eyebrow">Inteligencia de ofertas</p>
          <h1>Centralize catalogos, precos e integracoes.</h1>
        </div>
        <HealthBadge health={health} />
      </section>
      <section className="auth-panel">
        <div className="auth-heading">
          <h2>{mode === "login" ? "Acessar conta" : "Criar conta"}</h2>
          <div className="segmented">
            <button
              type="button"
              className={mode === "login" ? "active" : ""}
              onClick={() => setMode("login")}
            >
              Entrar
            </button>
            <button
              type="button"
              className={mode === "register" ? "active" : ""}
              onClick={() => setMode("register")}
            >
              Cadastrar
            </button>
          </div>
        </div>
        <form onSubmit={submit}>
          {mode === "register" && (
            <label>
              Nome
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                minLength={2}
                required
              />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? (
              <LoaderCircle className="spin" />
            ) : mode === "login" ? (
              <LogIn />
            ) : (
              <UserPlus />
            )}
            {busy ? "Aguarde" : mode === "login" ? "Entrar" : "Criar e entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Dashboard({ token }: { token: string }) {
  const [summary, setSummary] = useState(EMPTY);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .dashboard(token)
      .then(setSummary)
      .catch(() => setError("Resumo temporariamente indisponivel."));
  }, [token]);
  return (
    <>
      {error && <Notice>{error}</Notice>}
      <section className="metrics">
        <Metric label="Promocoes hoje" value={summary.deals_today} />
        <Metric label="Ofertas excelentes" value={summary.excellent_deals} />
        <Metric
          label="Produtos monitorados"
          value={summary.monitored_products}
        />
        <Metric label="Alertas enviados" value={summary.alerts_sent} />
        <Metric label="Lojas online" value={summary.online_stores} />
      </section>
      <section className="readiness">
        <div>
          <p className="eyebrow">Estado da fundacao</p>
          <h2>Servicos preparados para operacao</h2>
        </div>
        <div className="readiness-list">
          <Ready icon={<ShieldCheck />} label="Autenticacao" status="Ativa" />
          <Ready
            icon={<Database />}
            label="Dominio e historico"
            status="Ativos"
          />
          <Ready icon={<Plug />} label="Providers" status="Configuraveis" />
        </div>
      </section>
    </>
  );
}

function Integrations({ token }: { token: string }) {
  const [ml, setMl] = useState<MercadoLivreStatus | null>(null);
  const [steam, setSteam] = useState<SteamStatus | null>(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const refresh = useCallback(async () => {
    setNotice("");
    const [a, b] = await Promise.allSettled([
      api.mercadoLivreStatus(token),
      api.steamStatus(token),
    ]);
    if (a.status === "fulfilled") setMl(a.value);
    if (b.status === "fulfilled") setSteam(b.value);
    if (a.status === "rejected" || b.status === "rejected")
      setNotice("Uma integracao nao respondeu.");
  }, [token]);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  const connect = async () => {
    setBusy("connect");
    try {
      const result = await api.mercadoLivreAuthorize(token);
      location.assign(result.authorization_url);
    } catch (e) {
      setNotice(
        e instanceof ApiError ? e.message : "Falha ao iniciar conexao.",
      );
      setBusy("");
    }
  };
  const disconnect = async () => {
    setBusy("disconnect");
    try {
      await api.mercadoLivreDisconnect(token);
      await refresh();
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : "Falha ao desconectar.");
    } finally {
      setBusy("");
    }
  };
  const sync = async () => {
    setBusy("sync");
    setNotice("");
    try {
      const result = await api.steamSync(token);
      setNotice(
        `Steam sincronizada: ${result.catalog_items_seen} itens vistos, ${result.catalog_items_created} novos.`,
      );
    } catch (e) {
      setNotice(e instanceof ApiError ? e.message : "Falha ao sincronizar.");
    } finally {
      setBusy("");
    }
  };
  return (
    <section className="integrations">
      <div className="section-toolbar">
        <p>Conexoes e fontes de catalogo</p>
        <button
          className="icon-button"
          onClick={() => void refresh()}
          title="Atualizar status"
        >
          <RefreshCw />
        </button>
      </div>
      {notice && <Notice>{notice}</Notice>}
      <Integration
        name="Mercado Livre"
        status={ml?.connected ? "Conectado" : "Desconectado"}
        active={Boolean(ml?.connected)}
        detail={
          ml?.connected
            ? `Usuario ${ml.provider_user_id ?? "nao informado"}`
            : "Nenhuma conta vinculada"
        }
        action={
          ml?.connected ? (
            <button
              className="secondary-button danger"
              onClick={disconnect}
              disabled={Boolean(busy)}
            >
              <Unplug />
              Desconectar
            </button>
          ) : (
            <button
              className="primary-button compact"
              onClick={connect}
              disabled={Boolean(busy)}
            >
              <Link2 />
              Conectar
            </button>
          )
        }
      />
      <Integration
        name="Steam"
        status={steam?.configured ? "Configurada" : "Sem chave"}
        active={Boolean(steam?.configured && steam?.store_exists)}
        detail={
          steam?.store_exists
            ? "Loja registrada no dominio"
            : "Loja Steam ausente"
        }
        action={
          <button
            className="secondary-button"
            onClick={sync}
            disabled={!steam?.configured || Boolean(busy)}
          >
            {busy === "sync" ? (
              <LoaderCircle className="spin" />
            ) : (
              <RefreshCw />
            )}
            Sincronizar
          </button>
        }
      />
    </section>
  );
}

function Integration({
  name,
  status,
  active,
  detail,
  action,
}: {
  name: string;
  status: string;
  active: boolean;
  detail: string;
  action: ReactNode;
}) {
  return (
    <article className="integration-row">
      <span className="integration-icon">
        <Plug />
      </span>
      <div>
        <div className="integration-title">
          <h2>{name}</h2>
          <span className={active ? "state active" : "state"}>{status}</span>
        </div>
        <small>{detail}</small>
      </div>
      <div className="integration-action">{action}</div>
    </article>
  );
}
function Brand({ large = false }: { large?: boolean }) {
  return (
    <div className={large ? "brand large" : "brand"}>
      <span>OM</span>
      <div>
        <strong>OfertaMestre</strong>
        {!large && <small>Operacoes</small>}
      </div>
    </div>
  );
}
function Nav({
  active,
  icon,
  children,
  onClick,
}: {
  active: boolean;
  icon: ReactNode;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      className={active ? "nav-button active" : "nav-button"}
      onClick={onClick}
    >
      {icon}
      {children}
    </button>
  );
}
function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </article>
  );
}
function Ready({
  icon,
  label,
  status,
}: {
  icon: ReactNode;
  label: string;
  status: string;
}) {
  return (
    <div className="ready">
      <span>{icon}</span>
      <strong>{label}</strong>
      <small>{status}</small>
    </div>
  );
}
function HealthBadge({ health }: { health: Health }) {
  return (
    <span className={`health ${health}`}>
      <Activity />
      {health === "checking"
        ? "Verificando"
        : health === "online"
          ? "API online"
          : "API offline"}
    </span>
  );
}
function Notice({ children }: { children: ReactNode }) {
  return (
    <div className="notice" role="status">
      {children}
    </div>
  );
}
function initials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}
