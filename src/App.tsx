import { useState } from 'react';
import GrassLibrary from './pages/GrassLibrary';
import Prediction from './pages/Prediction';
import ResearchEvidence from './pages/ResearchEvidence';

type AppPage = 'library' | 'prediction' | 'research';

export default function App() {
  const [activePage, setActivePage] = useState<AppPage>('library');
  const [researchContext, setResearchContext] = useState({ species: '', mechanism: '' });

  const openResearchEvidence = (context: { species?: string; mechanism?: string }) => {
    setResearchContext({
      species: context.species ?? '',
      mechanism: context.mechanism ?? '',
    });
    setActivePage('research');
  };

  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        <div>
          <strong>Halophyte Grass Dictionary</strong>
          <span>Phase 1 Library + Phase 2 Prediction + Phase 4 Research Evidence</span>
        </div>
        <div className="app-navigation-actions">
          <button
            className={activePage === 'library' ? 'nav-button nav-button-active' : 'nav-button'}
            type="button"
            onClick={() => setActivePage('library')}
          >
            Grass Library
          </button>
          <button
            className={activePage === 'prediction' ? 'nav-button nav-button-active' : 'nav-button'}
            type="button"
            onClick={() => setActivePage('prediction')}
          >
            Prediction Model
          </button>
          <button
            className={activePage === 'research' ? 'nav-button nav-button-active' : 'nav-button'}
            type="button"
            onClick={() => setActivePage('research')}
          >
            Research Evidence
          </button>
        </div>
      </nav>
      {activePage === 'library' ? (
        <GrassLibrary onViewResearchEvidence={openResearchEvidence} />
      ) : activePage === 'prediction' ? (
        <Prediction />
      ) : (
        <ResearchEvidence initialSpecies={researchContext.species} initialMechanism={researchContext.mechanism} />
      )}
    </>
  );
}
