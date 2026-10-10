import { type ReactNode, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { api } from '../lib/api';
import { 
  AlertTriangle, Clock, CheckCircle2, Search, ArrowRight, 
  ShieldAlert, Activity, Plus, Filter, Flame, Globe, Building2, Lock
} from 'lucide-react';

interface Incident {
  id: string;
  title: string;
  description?: string;
  service_name: string;
  severity: string;
  status: string;
  commander_id?: string;
  creator_id: string;
  visibility?: 'ORGANIZATION' | 'DEPARTMENT' | 'RESTRICTED';
  department?: string;
  version: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  creator_name?: string;
  commander_name?: string;
}

export default function Dashboard() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [visibilityFilter, setVisibilityFilter] = useState('ALL');
  const navigate = useNavigate();

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await api.getIncidents();
      setIncidents(res.incidents || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    const colors: Record<string, string> = {
      'SEV-1': 'bg-red-50 text-red-700 border-red-200',
      'SEV-2': 'bg-orange-50 text-orange-700 border-orange-200',
      'SEV-3': 'bg-blue-50 text-blue-700 border-blue-200',
      'SEV-4': 'bg-slate-50 text-slate-700 border-slate-200',
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${colors[sev] || colors['SEV-3']}`}>
        {sev}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const icons: Record<string, ReactNode> = {
      'INVESTIGATING': <Search className="w-3.5 h-3.5 text-amber-600" />,
      'IDENTIFIED': <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />,
      'MONITORING': <Clock className="w-3.5 h-3.5 text-indigo-600" />,
      'RESOLVED': <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />,
    };
    const colors: Record<string, string> = {
      'INVESTIGATING': 'bg-amber-50 text-amber-700 border-amber-200',
      'IDENTIFIED': 'bg-rose-50 text-rose-700 border-rose-200',
      'MONITORING': 'bg-indigo-50 text-indigo-700 border-indigo-200',
      'RESOLVED': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    };
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colors[status] || 'bg-slate-100'}`}>
        {icons[status]} {status}
      </span>
    );
  };

  const getVisibilityBadge = (vis?: string, dept?: string) => {
    if (vis === 'RESTRICTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <Lock className="w-3 h-3 text-rose-600" /> Restricted
        </span>
      );
    }
    if (vis === 'DEPARTMENT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
          <Building2 className="w-3 h-3 text-purple-600" /> Dept: {dept || 'Team'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
        <Globe className="w-3 h-3 text-teal-600" /> Organization
      </span>
    );
  };

  // Metrics
  const totalIncidents = incidents.length;
  const activeIncidents = incidents.filter(i => i.status !== 'RESOLVED').length;
  const criticalSev1 = incidents.filter(i => i.severity === 'SEV-1' && i.status !== 'RESOLVED').length;
  const resolvedIncidents = incidents.filter(i => i.status === 'RESOLVED').length;

  // Filtered List
  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch = 
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (inc.department && inc.department.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesStatus = 
      statusFilter === 'ALL' ||
      (statusFilter === 'ACTIVE' && inc.status !== 'RESOLVED') ||
      inc.status === statusFilter;

    const matchesSeverity = 
      severityFilter === 'ALL' ||
      inc.severity === severityFilter;

    const matchesVisibility =
      visibilityFilter === 'ALL' ||
      inc.visibility === visibilityFilter;

    return matchesSearch && matchesStatus && matchesSeverity && matchesVisibility;
  });

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">IncidentFlow Command Center</h1>
            <p className="text-slate-500 mt-1 text-sm">Monitor, respond, and resolve service outages in real time.</p>
          </div>
          <Link 
            to="/incidents/new"
            className="inline-flex items-center justify-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-100 shrink-0 cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Declare Incident
          </Link>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active</span>
              <div className="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-black text-slate-900 mt-2">{activeIncidents}</p>
            <p className="text-xs text-slate-400 mt-1">Ongoing investigations</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Critical (SEV-1)</span>
              <div className="w-8 h-8 rounded-xl bg-red-50 flex items-center justify-center text-red-600">
                <Flame className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-black text-slate-900 mt-2">{criticalSev1}</p>
            <p className="text-xs text-slate-400 mt-1">Requiring immediate action</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Resolved</span>
              <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-black text-slate-900 mt-2">{resolvedIncidents}</p>
            <p className="text-xs text-slate-400 mt-1">Closed successfully</p>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Visible</span>
              <div className="w-8 h-8 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
                <ShieldAlert className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-black text-slate-900 mt-2">{totalIncidents}</p>
            <p className="text-xs text-slate-400 mt-1">Based on your permissions</p>
          </div>
        </div>

        {/* Controls Bar: Search & Filters */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input 
              type="text"
              placeholder="Search by title, service, department..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500 transition-all text-slate-900"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
            <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-xl p-1 text-xs shrink-0">
              <Filter className="w-3.5 h-3.5 text-slate-400 ml-2 mr-1" />
              <button 
                onClick={() => setStatusFilter('ALL')}
                className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                  statusFilter === 'ALL' ? 'bg-white shadow-xs text-slate-900' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                All
              </button>
              <button 
                onClick={() => setStatusFilter('ACTIVE')}
                className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                  statusFilter === 'ACTIVE' ? 'bg-white shadow-xs text-indigo-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Active
              </button>
              <button 
                onClick={() => setStatusFilter('RESOLVED')}
                className={`px-3 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                  statusFilter === 'RESOLVED' ? 'bg-white shadow-xs text-emerald-600 font-semibold' : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                Resolved
              </button>
            </div>

            <select
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 outline-none cursor-pointer shrink-0"
            >
              <option value="ALL">All Severities</option>
              <option value="SEV-1">SEV-1 Critical</option>
              <option value="SEV-2">SEV-2 Major</option>
              <option value="SEV-3">SEV-3 Minor</option>
              <option value="SEV-4">SEV-4 Low</option>
            </select>

            <select
              value={visibilityFilter}
              onChange={e => setVisibilityFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 outline-none cursor-pointer shrink-0"
            >
              <option value="ALL">All Visibilities</option>
              <option value="ORGANIZATION">Organization</option>
              <option value="DEPARTMENT">Department</option>
              <option value="RESTRICTED">Restricted</option>
            </select>
          </div>
        </div>

        {/* Incidents List */}
        {loading ? (
          <div className="flex justify-center p-16">
            <div className="w-10 h-10 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
            <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-slate-100">
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">No Incidents Found</h3>
            <p className="text-slate-500 text-sm max-w-sm mx-auto">
              {searchQuery || statusFilter !== 'ALL' || severityFilter !== 'ALL' || visibilityFilter !== 'ALL'
                ? 'Try adjusting your filters or search query.'
                : 'All systems are operating normally. No active incident reports.'}
            </p>
          </div>
        ) : (
          <div className="grid gap-3">
            {filteredIncidents.map(inc => (
              <div 
                key={inc.id}
                onClick={() => navigate(`/incidents/${inc.id}`)}
                className="group bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer flex flex-col md:flex-row md:items-center gap-4"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 mb-2 flex-wrap">
                    {getSeverityBadge(inc.severity)}
                    {getStatusBadge(inc.status)}
                    {getVisibilityBadge(inc.visibility, inc.department)}
                    <span className="text-xs font-semibold text-slate-500 bg-slate-50 px-2.5 py-0.5 rounded-full border border-slate-200">
                      {inc.service_name}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors truncate">
                    {inc.title}
                  </h3>
                  {inc.description && (
                    <p className="text-slate-500 text-xs mt-1 line-clamp-1">
                      {inc.description}
                    </p>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                    <span>Opened: {new Date(inc.created_at).toLocaleDateString()}</span>
                    {inc.creator_name && <span>By: {inc.creator_name}</span>}
                    {inc.commander_name && <span>IC: {inc.commander_name}</span>}
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
                  <span className="text-xs font-semibold text-indigo-600 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                    Enter Incident Room <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}