import { useEffect, useState, type ReactNode } from "react";
import "./styles.css";

type DashboardSummary = {
  deals_today: number;
  excellent_deals: number;
  monitored_products: number;
  alerts_sent: number;
  online_stores: number;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_STORAGE_KEY = "ofertamestre_access_token";

const emptySummary: DashboardSummary = {
  deals_today: 0,
  excellent_deals: 0,
  monitored_products: 0,
  alerts_sent: 0,
  online_stores: 0,
};

function App() {
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [health, setHealth] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("API unavailable");
        }
        setHealth("online");
      })
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      return;
    }

    fetch(`${API_URL}/api/v1/dashboard/summary`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Dashboard unavailable");
        }
        return response.json() as Promise<DashboardSummary>;
      })
      .then(setSummary)
      .catch(() => setSummary(emptySummary));
  }, []);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Sprint 0</p>
          <h1>OfertaMestre</h1>
        </div>
        <span className={`status status-${health}`}>
          <Icon name="activity" />
          {health === "checking" ? "Verificando API" : health === "online" ? "API online" : "API offline"}
        </span>
      </section>

      <section className="hero">
        <div>
          <p className="eyebrow">Dashboard inicial</p>
          <h2>Fundacao pronta para inteligencia de ofertas.</h2>
          <p>
            A base do produto esta preparada para autenticacao, evolucao do modelo de dados e integracao dos
            coletores nas proximas sprints.
          </p>
        </div>
      </section>

      <section className="metrics" aria-label="Indicadores iniciais">
        <Metric icon={<Icon name="tag" />} label="Promocoes hoje" value={summary.deals_today} />
        <Metric icon={<Icon name="check" />} label="Ofertas excelentes" value={summary.excellent_deals} />
        <Metric icon={<Icon name="eye" />} label="Produtos monitorados" value={summary.monitored_products} />
        <Metric icon={<Icon name="bell" />} label="Alertas enviados" value={summary.alerts_sent} />
        <Metric icon={<Icon name="store" />} label="Lojas online" value={summary.online_stores} />
      </section>

      <section className="panel">
        <h2>Escopo desta entrega</h2>
        <ul>
          <li>Monorepo estruturado com backend, frontend e documentacao.</li>
          <li>API FastAPI com OpenAPI automatico, JWT e PostgreSQL.</li>
          <li>Interface React preparada para consumir dados reais.</li>
          <li>Docker Compose para subir tudo com um comando.</li>
        </ul>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return (
    <article className="metric">
      <div className="metric-icon">{icon}</div>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </article>
  );
}

function Icon({ name }: { name: "activity" | "tag" | "check" | "eye" | "bell" | "store" }) {
  return <span aria-hidden="true" className={`icon icon-${name}`} />;
}

export default App;
