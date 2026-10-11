import { type ReactNode, useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { api } from '../lib/api';
import { ShieldAlert, LayoutDashboard, PlusCircle, LogOut, User as UserIcon, Building2, Activity } from 'lucide-react';

export default function Layout({ 
  children, 
  fullHeight = false 
}: { 
  children: ReactNode; 
  fullHeight?: boolean; 
}) {
  const [user, setUser] = useState<any>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api.getMe().then(setUser).catch(() => navigate('/login'));
  }, [navigate]);

  const handleLogout = () => {
    api.logout();
    navigate('/');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-900">
      {/* Light Mode Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 text-slate-700 flex flex-col hidden md:flex shrink-0 shadow-xs">
        <div className="p-6">
          <Link to="/dashboard" className="flex items-center gap-3 mb-8 group">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-100 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight block leading-tight">IncidentFlow</span>
              <span className="text-[11px] font-medium text-slate-400 block">Incident Ops Center</span>
            </div>
          </Link>
          
          <nav className="space-y-1.5">
            <Link 
              to="/dashboard"
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                location.pathname === '/dashboard' 
                  ? 'bg-indigo-50 text-indigo-700 shadow-xs border border-indigo-100/80' 
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <LayoutDashboard className={`w-4 h-4 ${location.pathname === '/dashboard' ? 'text-indigo-600' : 'text-slate-400'}`} />
              Dashboard
            </Link>
            <Link 
              to="/incidents/new"
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                location.pathname === '/incidents/new' 
                  ? 'bg-indigo-50 text-indigo-700 shadow-xs border border-indigo-100/80' 
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <PlusCircle className={`w-4 h-4 ${location.pathname === '/incidents/new' ? 'text-indigo-600' : 'text-slate-400'}`} />
              New Incident
            </Link>
            <Link 
              to="/testing"
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                location.pathname === '/testing' 
                  ? 'bg-indigo-50 text-indigo-700 shadow-xs border border-indigo-100/80' 
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Activity className={`w-4 h-4 ${location.pathname === '/testing' ? 'text-indigo-600' : 'text-slate-400'}`} />
              Automated Testing
            </Link>
          </nav>
        </div>
        
        <div className="mt-auto p-5 border-t border-slate-100 bg-slate-50/60">
          {user && (
            <div className="mb-4 p-2.5 bg-white rounded-xl border border-slate-200/60 shadow-xs">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm shrink-0">
                  {user.name?.[0]?.toUpperCase() || <UserIcon className="w-4 h-4" />}
                </div>
                <div className="overflow-hidden min-w-0">
                  <p className="text-slate-900 text-xs font-bold truncate">{user.name}</p>
                  <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] font-semibold text-indigo-700">
                <Building2 className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                <span className="truncate">{user.department || 'Engineering'}</span>
              </div>
            </div>
          )}
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all w-full cursor-pointer"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* Mobile Header (Light Mode) */}
        <header className="md:hidden bg-white border-b border-slate-200 text-slate-900 p-4 flex justify-between items-center shrink-0 shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <span className="font-bold text-slate-900 text-base">IncidentFlow</span>
          </div>
          <button onClick={handleLogout} className="p-2 text-slate-500 hover:text-red-600 rounded-lg">
            <LogOut className="w-5 h-5" />
          </button>
        </header>

        <div className={`flex-1 min-h-0 ${fullHeight ? 'overflow-y-auto lg:overflow-hidden flex flex-col p-3 md:p-5' : 'overflow-y-auto p-4 md:p-8'}`}>
          {children}
        </div>
      </main>
    </div>
  );
}