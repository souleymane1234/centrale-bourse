import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Spinner from './Spinner';

const PUBLIC_PREFIX_PATHS = ['/profil', '/bienvenue'];

function isPublicPath(pathname) {
  if (pathname === '/') return true;
  return PUBLIC_PREFIX_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export default function PlatformGate({ children }) {
  const { loading, isAuthenticated, hasPlatformAccess } = useAuth();
  const location = useLocation();
  const isPublic = isPublicPath(location.pathname);

  if (loading) {
    return <Spinner label="Chargement..." />;
  }

  if (!isAuthenticated) {
    if (isPublic) {
      return children;
    }
    return <Navigate to="/bienvenue" replace state={{ from: location.pathname }} />;
  }

  if (!hasPlatformAccess && !isPublic) {
    return <Navigate to="/bienvenue" replace />;
  }

  return children;
}
