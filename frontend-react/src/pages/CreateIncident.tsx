import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { api } from '../lib/api';
import { 
  AlertCircle, FileText, Server, AlertTriangle, UserCheck, 
  Globe, Building2, Lock
} from 'lucide-react';

interface UserOption {
  id: string;
  name: string;
  email: string;
  department?: string;
}

export default function CreateIncident() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [serviceName, setServiceName] = useState('');
  const [severity, setSeverity] = useState('SEV-3');
  const [commanderId, setCommanderId] = useState('');
  const [visibility, setVisibility] = useState<'ORGANIZATION' | 'DEPARTMENT' | 'RESTRICTED'>('ORGANIZATION');
  const [department, setDepartment] = useState('Engineering');
  
  const [users, setUsers] = useState<UserOption[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.getUsers().catch(() => []),
      api.getMe().catch(() => null),
    ]).then(([usersList, currentUser]) => {
      setUsers(usersList);
      if (currentUser?.department) {
        setDepartment(currentUser.department);
      }
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !serviceName.trim()) {
      setError('Title and Service Name are required.');
      return;
    }
    if (visibility === 'DEPARTMENT' && !department.trim()) {
      setError('Please specify the affected department for department-visible incidents.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const payload: any = {
        title: title.trim(),
        description: description.trim() ? description.trim() : null,
        service_name: serviceName.trim(),
        severity,
        visibility,
        department: visibility === 'DEPARTMENT' ? department.trim() : null,
      };
      if (commanderId) {
        payload.commander_id = commanderId;
      }

      const result = await api.createIncident(payload);
      navigate(`/incidents/${result.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create incident');
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Declare New Incident</h1>
          <p className="text-slate-500 mt-1">
            Initiate response coordination and automatically launch a real-time IncidentFlow room.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-start gap-3 text-sm border border-red-100">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-500" /> Incident Title <span className="text-red-500">*</span>
            </label>
            <input 
              type="text"
              required
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-900 transition-all placeholder:text-slate-400"
              placeholder="e.g. Production Payment Gateway High Latency (504 Gateway Timeout)"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-slate-500" /> Summary & Initial Assessment
            </label>
            <textarea 
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-900 transition-all resize-none placeholder:text-slate-400 text-sm"
              placeholder="Provide context on symptoms, affected customer segment, active alerts, and immediate actions taken..."
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Server className="w-4 h-4 text-indigo-500" /> Affected Service <span className="text-red-500">*</span>
              </label>
              <input 
                type="text"
                required
                value={serviceName}
                onChange={e => setServiceName(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-900 transition-all placeholder:text-slate-400"
                placeholder="e.g., payment-service, auth-api"
              />
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" /> Severity Level <span className="text-red-500">*</span>
              </label>
              <select 
                value={severity}
                onChange={e => setSeverity(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-900 font-medium transition-all"
              >
                <option value="SEV-1">SEV-1: Critical Outage (Customer facing)</option>
                <option value="SEV-2">SEV-2: Major Degradation</option>
                <option value="SEV-3">SEV-3: Minor Impact / Workaround available</option>
                <option value="SEV-4">SEV-4: Low Priority / Internal only</option>
              </select>
            </div>
          </div>

          {/* Visibility and Access Control Selector */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-500" /> Incident Visibility & Access Control <span className="text-red-500">*</span>
            </label>
            <div className="grid sm:grid-cols-3 gap-3">
              <label 
                className={`flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  visibility === 'ORGANIZATION' 
                    ? 'border-indigo-600 bg-indigo-50/40 text-slate-900' 
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 text-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 font-bold text-sm">
                    <Globe className="w-4 h-4 text-teal-600" /> Organization
                  </div>
                  <input 
                    type="radio" 
                    name="visibility" 
                    value="ORGANIZATION"
                    checked={visibility === 'ORGANIZATION'}
                    onChange={() => setVisibility('ORGANIZATION')}
                    className="accent-indigo-600"
                  />
                </div>
                <p className="text-xs text-slate-500">
                  All authenticated employees can discover and view this incident report.
                </p>
              </label>

              <label 
                className={`flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  visibility === 'DEPARTMENT' 
                    ? 'border-indigo-600 bg-indigo-50/40 text-slate-900' 
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 text-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 font-bold text-sm">
                    <Building2 className="w-4 h-4 text-indigo-600" /> Department
                  </div>
                  <input 
                    type="radio" 
                    name="visibility" 
                    value="DEPARTMENT"
                    checked={visibility === 'DEPARTMENT'}
                    onChange={() => setVisibility('DEPARTMENT')}
                    className="accent-indigo-600"
                  />
                </div>
                <p className="text-xs text-slate-500">
                  Only employees matching the affected department can discover and view.
                </p>
              </label>

              <label 
                className={`flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  visibility === 'RESTRICTED' 
                    ? 'border-indigo-600 bg-indigo-50/40 text-slate-900' 
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/50 text-slate-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 font-bold text-sm">
                    <Lock className="w-4 h-4 text-rose-600" /> Restricted
                  </div>
                  <input 
                    type="radio" 
                    name="visibility" 
                    value="RESTRICTED"
                    checked={visibility === 'RESTRICTED'}
                    onChange={() => setVisibility('RESTRICTED')}
                    className="accent-indigo-600"
                  />
                </div>
                <p className="text-xs text-slate-500">
                  Confidential. Only the creator, commander, and explicitly invited users can view.
                </p>
              </label>
            </div>
          </div>

          {/* Department Field (shown when DEPARTMENT visibility is selected) */}
          {visibility === 'DEPARTMENT' && (
            <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-100 space-y-2">
              <label className="block text-xs font-bold text-indigo-950 uppercase tracking-wider flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-indigo-600" /> Affected Department <span className="text-red-500">*</span>
              </label>
              <input 
                type="text"
                required
                value={department}
                onChange={e => setDepartment(e.target.value)}
                placeholder="e.g. Engineering, Operations, Security"
                className="w-full px-4 py-2.5 bg-white border border-indigo-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-slate-900 font-medium text-sm"
              />
              <p className="text-xs text-indigo-700/80">
                Only users whose registered department matches will have access to this incident.
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-500" /> Incident Commander (Optional)
            </label>
            <select
              value={commanderId}
              onChange={e => setCommanderId(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-slate-900 transition-all"
            >
              <option value="">Default (Assign to myself)</option>
              {users.map(u => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email}) — {u.department || 'Engineering'}
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-400 mt-1.5">
              The incident commander oversees response coordination and sets status updates.
            </p>
          </div>

          <div className="pt-6 border-t border-slate-100 flex justify-end gap-3 items-center">
            <button 
              type="button"
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2.5 text-slate-600 font-medium hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="bg-indigo-600 text-white px-8 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200/50 disabled:opacity-70 flex items-center gap-2 cursor-pointer"
            >
              {loading ? 'Declaring Incident...' : 'Declare Incident'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}