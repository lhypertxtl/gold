import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { checkSessionApi, logoutApi } from './api/client';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SignalDetailPage } from './pages/SignalDetailPage';

export function App() {
  const [authUser, setAuthUser] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [meta, setMeta] = useState<{ hasDemo: boolean; hasReal: boolean }>({
    hasDemo: false,
    hasReal: false,
  });

  useEffect(() => {
    checkSessionApi()
      .then((res) => {
        if (res.authenticated) {
          setAuthUser(res.username);
        }
      })
      .catch(() => {
        setAuthUser(null);
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);

  const handleLogout = async () => {
    await logoutApi();
    setAuthUser(null);
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center text-sm">
        Cargando Gold Signals...
      </div>
    );
  }

  if (!authUser) {
    return <LoginPage onSuccess={(username) => setAuthUser(username)} />;
  }

  return (
    <BrowserRouter basename="/gold">
      <Layout
        username={authUser}
        onLogout={handleLogout}
        hasDemoData={meta.hasDemo}
        hasRealData={meta.hasReal}
      >
        <Routes>
          <Route path="/" element={<DashboardPage onMetaChange={setMeta} />} />
          <Route path="/signals/:id" element={<SignalDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
export default App;
