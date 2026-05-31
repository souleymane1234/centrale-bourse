import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="pb-[calc(4rem+env(safe-area-inset-bottom,0px))] md:pb-0">
        <Outlet />
      </main>
    </div>
  );
}
