import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { ShieldAlert, LogIn, KeyRound, Mail, AlertCircle, UserPlus, UserCheck, Building2 } from 'lucide-react';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [departments, setDepartments] = useState<{ id: string; name: string }[]>([]);
  const [departmentId, setDepartmentId] = useState('');
  const [deptLoading, setDeptLoading] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      setDeptLoading(true);
      const data = await api.getDepartments();
      setDepartments(data || []);
    } catch (e: any) {
      console.error('Failed to load departments', e);
    } finally {
      setDeptLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (isRegister && !departmentId) {
      setError('Please select your department.');
      return;
    }

    setLoading(true);
    
    try {
      if (isRegister) {
        await api.register({ 
          name, 
          email, 
          password, 
          department_id: departmentId 
        });
        // Automatically login after register
        const result = await api.login({ email, password });
        api.setToken(result.access_token);
      } else {
        const result = await api.login({ email, password });
        api.setToken(result.access_token);
      }
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || (isRegister ? 'Registration failed' : 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4 hover:opacity-80 transition-opacity">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-200">
              <ShieldAlert className="w-7 h-7 text-white" />
            </div>
          </Link>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {isRegister ? 'Create Account' : 'Welcome Back'}
          </h2>
          <p className="text-slate-500 mt-2 text-sm">
            {isRegister 
              ? 'Join the IncidentFlow response team' 
              : 'Sign in to access your active IncidentFlow workspaces'}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/60 p-8 border border-slate-100">
          <form onSubmit={handleSubmit} className="space-y-5">
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <UserCheck className="absolute left-3.5 top-3 w-5 h-5 text-slate-400" />
                    <input 
                      type="text"
                      required
                      value={name}
                      onChange={e => setName(e.target.value)}
                      className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all"
                      placeholder="Jane Doe"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Department <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Building2 className="absolute left-3.5 top-3 w-5 h-5 text-slate-400 pointer-events-none" />
                    <select
                      required
                      value={departmentId}
                      onChange={e => {
                        setDepartmentId(e.target.value);
                        if (error) setError('');
                      }}
                      className={`w-full pl-11 pr-8 py-2.5 bg-slate-50 border rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all cursor-pointer ${
                        !departmentId && error ? 'border-rose-300 ring-1 ring-rose-300 bg-rose-50/20' : 'border-slate-200 text-slate-800'
                      }`}
                    >
                      <option value="">
                        {deptLoading ? 'Loading departments...' : '-- Select your department --'}
                      </option>
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {!departmentId && (
                    <p className="text-[11px] text-slate-400 mt-1">
                      Choose your department (e.g. IT, HR, Finance, Operations, Security, Marketing).
                    </p>
                  )}
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-5 h-5 text-slate-400" />
                <input 
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all"
                  placeholder="engineer@company.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">Password</label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-3 w-5 h-5 text-slate-400" />
                <input 
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="p-3.5 bg-red-50 text-red-700 rounded-xl flex items-start gap-2.5 text-xs font-medium border border-red-100">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-500 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-100 disabled:opacity-70 cursor-pointer"
            >
              {loading 
                ? (isRegister ? 'Creating Account...' : 'Signing in...') 
                : (isRegister ? 'Create Account' : 'Sign In')} 
              {isRegister ? <UserPlus className="w-4 h-4" /> : <LogIn className="w-4 h-4" />}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister);
                setError('');
                setDepartmentId('');
              }}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold transition-colors cursor-pointer"
            >
              {isRegister 
                ? 'Already have an account? Sign In' 
                : "Don't have an account? Register here"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
