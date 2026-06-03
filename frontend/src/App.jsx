import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import LandingLayout from './components/landing/LandingLayout';
import PlatformGate from './components/PlatformGate';
import HomePage from './pages/HomePage';
import CompanyPage from './pages/CompanyPage';
import NewsPage from './pages/NewsPage';
import NewsDetailPage from './pages/NewsDetailPage';
import ComparePage from './pages/ComparePage';
import ProfilePage from './pages/ProfilePage';
import LandingPage from './pages/LandingPage';
import LegalCguPage from './pages/LegalCguPage';
import LegalPrivacyPage from './pages/LegalPrivacyPage';
import FollowPage from './pages/FollowPage';

export default function App() {
  return (
    <Routes>
      <Route element={<LandingLayout />}>
        <Route path="/bienvenue" element={<LandingPage />} />
        <Route path="/cgu" element={<LegalCguPage />} />
        <Route path="/confidentialite" element={<LegalPrivacyPage />} />
      </Route>
      <Route
        element={
          <PlatformGate>
            <Layout />
          </PlatformGate>
        }
      >
        <Route path="/" element={<HomePage />} />
        <Route path="/actualites" element={<NewsPage />} />
        <Route path="/actualites/:slug" element={<NewsDetailPage />} />
        <Route path="/comparer" element={<ComparePage />} />
        <Route path="/profil" element={<ProfilePage />} />
        <Route path="/suivi" element={<FollowPage />} />
        <Route path="/societe/:ticker" element={<CompanyPage />} />
      </Route>
    </Routes>
  );
}
