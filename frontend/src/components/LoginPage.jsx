/**
 * Login gate — required before the command centre opens.
 * Uses existing POST /api/login only.
 */
import { useEffect, useState } from "react";
import { ArrowLeft, Eye, EyeOff, Lock, Ship, User } from "lucide-react";
import { Link } from "react-router-dom";
import { fetchHealth } from "../api";

const DEMO_ACCOUNTS = [
  { user: "exporter", pass: "india@11", label: "Exporter" },
  { user: "demo", pass: "demo@123", label: "Demo" },
  { user: "admin", pass: "admin@123", label: "Admin" },
];

export default function LoginPage({ onLogin, error, loading }) {
  const [username, setUsername] = useState("exporter");
  const [password, setPassword] = useState("india@11");
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(false);
  const [backend, setBackend] = useState({ state: "checking", message: "Checking API…" });

  useEffect(() => {
    let alive = true;
    fetchHealth()
      .then((h) => {
        if (!alive) return;
        setBackend({
          state: "ok",
          message: h.groq_enabled ? `API online · ${h.groq_model || "Groq"}` : "API online · LLM optional",
        });
      })
      .catch(() => {
        if (!alive) return;
        setBackend({
          state: "down",
          message: "Backend offline — start Flask on port 5001",
        });
      });
    return () => {
      alive = false;
    };
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    onLogin(username.trim(), password, remember);
  }

  function fillDemo(account) {
    setUsername(account.user);
    setPassword(account.pass);
  }

  return (
    <div className="xi-login">
      <div className="xi-login__shell">
        <section className="xi-login__panel">
          <div className="xi-brand xi-brand--login">
            <div className="xi-brand__mark" aria-hidden="true">
              <Ship size={17} />
            </div>
            <div className="xi-brand__text">
              <strong>EXPORTINTEL AI</strong>
              <span className={`xi-brand__status ${backend.state === "ok" ? "" : "is-warn"}`}>
                <i className={`xi-dot ${backend.state === "ok" ? "xi-dot--live" : ""}`} />
                {backend.message}
              </span>
            </div>
          </div>

          <h2>Welcome Back!</h2>
          <p className="xi-login__sub">Login to your export intelligence workspace</p>

          <form className="xi-login__form" onSubmit={handleSubmit}>
            <label htmlFor="login-username">
              Username
              <div className="xi-login__input">
                <User size={16} aria-hidden="true" />
                <input
                  id="login-username"
                  name="username"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>
            </label>

            <div className="xi-login__options">
              <label className="xi-login__remember">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(event) => setRemember(event.target.checked)}
                />
                Remember me
              </label>
              <button type="button" className="xi-login__forgot">
                Forgot password?
              </button>
            </div>

            <label htmlFor="login-password">
              Password
              <div className="xi-login__input">
                <Lock size={16} aria-hidden="true" />
                <input
                  id="login-password"
                  name="password"
                  type={showPass ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  className="xi-login__eye"
                  onClick={() => setShowPass((v) => !v)}
                  aria-label={showPass ? "Hide password" : "Show password"}
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>

            {error ? (
              <p className="xi-login__error" role="alert">
                {error}
              </p>
            ) : null}

            {backend.state === "down" ? (
              <p className="xi-login__warn" role="status">
                Start the backend first: <code>cd backend && python app.py</code>
              </p>
            ) : null}

            <button
              className="xi-btn xi-btn--primary xi-btn--block"
              type="submit"
              disabled={loading || backend.state === "down"}
            >
              {loading ? (
                <>
                  <span className="xi-spinner" /> Signing in…
                </>
              ) : (
                "Enter command centre"
              )}
            </button>
          </form>

          <div className="xi-login__demos">
            <span>Quick demo accounts</span>
            <div>
              {DEMO_ACCOUNTS.map((a) => (
                <button key={a.user} type="button" className="xi-chip" onClick={() => fillDemo(a)} disabled={loading}>
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          <Link className="xi-login__back" to="/">
            <ArrowLeft size={14} /> Return to landing page
          </Link>
        </section>

        <section className="xi-login__visual" aria-label="Container terminal and international logistics">
          <div className="xi-login__visual-overlay" />
          <div className="xi-login__visual-copy">
            <p>PREDICTIVE EXPORT INTELLIGENCE</p>
            <h1>Predict. Plan. Export.</h1>
            <span>Connected decisions for global trade.</span>
          </div>
        </section>
      </div>
    </div>
  );
}
