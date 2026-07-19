import { useEffect, useState } from 'react';
import GrassLibrary from './pages/GrassLibrary';
import Prediction from './pages/Prediction';
import SoilSalinityMapper from './pages/SoilSalinityMapper';

type AppPage = 'library' | 'prediction' | 'knowledgeGraph' | 'fieldMatch' | 'miniProjects';

const ROUTES: Record<AppPage, string> = {
  library: '/',
  prediction: '/prediction',
  knowledgeGraph: '/knowledge-graph',
  fieldMatch: '/field-match',
  miniProjects: '/soil-salinity-mapping',
};

function pageFromPath(pathname: string): AppPage {
  if (pathname === '/prediction') {
    return 'prediction';
  }
  if (pathname === '/knowledge-graph') {
    return 'knowledgeGraph';
  }
  if (pathname === '/field-match' || pathname === '/halophyte-field-match') {
    return 'fieldMatch';
  }
  if (pathname === '/mini-projects' || pathname === '/soil-salinity-mapping' || pathname === '/salinity-map') {
    return 'miniProjects';
  }
  return 'library';
}

function StaticModulePage({ title, src }: { title: string; src: string }) {
  return (
    <main className="module-page">
      <iframe className="module-frame" title={title} src={src} />
    </main>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState<AppPage>(() => pageFromPath(window.location.pathname));

  useEffect(() => {
    if (window.location.pathname === '/mini-projects' || window.location.pathname === '/salinity-map') {
      window.history.replaceState({}, '', ROUTES.miniProjects);
    }
    const handlePopState = () => setActivePage(pageFromPath(window.location.pathname));
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (page: AppPage) => {
    const path = ROUTES[page];
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
    setActivePage(page);
  };

  const renderNavButton = (page: AppPage, label: string) => (
    <button
      className={activePage === page ? 'nav-button nav-button-active' : 'nav-button'}
      type="button"
      onClick={() => navigate(page)}
    >
      {label}
    </button>
  );

  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        <div>
          <strong>Halophyte Grass Dictionary</strong>
          <span>Library, prediction, field match, and mini-project modules</span>
        </div>
        <div className="app-navigation-actions">
          {renderNavButton('library', 'Grass Library')}
          {renderNavButton('prediction', 'Prediction Model')}
          {renderNavButton('knowledgeGraph', 'Knowledge Graph')}
          {renderNavButton('fieldMatch', 'Field Match')}
          {renderNavButton('miniProjects', 'Soil Salinity Mapper')}
        </div>
      </nav>
      {activePage === 'library' ? (
        <GrassLibrary />
      ) : activePage === 'prediction' ? (
        <Prediction />
      ) : activePage === 'knowledgeGraph' ? (
        <StaticModulePage title="Halophyte Knowledge Graph" src="/modules/knowledge-graph/index.html" />
      ) : activePage === 'fieldMatch' ? (
        <StaticModulePage title="Halophyte Field Match" src="/modules/field-match/index.html" />
      ) : (
        <SoilSalinityMapper />
      )}
    </>
  );
}
