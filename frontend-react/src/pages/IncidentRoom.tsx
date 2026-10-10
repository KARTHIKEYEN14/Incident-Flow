import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { api } from '../lib/api';
import { 
  Send, Users, Activity, ShieldAlert, ArrowLeft, 
  CheckCircle2, Radio, UserPlus, 
  X, AlertCircle, Globe, Building2, Lock, Eye
} from 'lucide-react';

interface Participant {
  user_id: string;
  role: string;
  user_name?: string;
  user_email?: string;
}

interface Message {
  id: string;
  author_id: string;
  author_name?: string;
  body: string;
  created_at: string;
}

interface EventItem {
  id: number;
  actor_id?: string;
  actor_name?: string;
  event_type: string;
  payload: any;
  created_at: string;
}

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

export default function IncidentRoom() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [allUsers, setAllUsers] = useState<any[]>([]);
  
  const [messageInput, setMessageInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [accessDenied, setAccessDenied] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [activeUsersCount, setActiveUsersCount] = useState(1);
  const [errorMessage, setErrorMessage] = useState('');

  // Modals & Panels
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolutionNote, setResolutionNote] = useState('');
  const [showAddParticipant, setShowAddParticipant] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState<'RESPONDER' | 'OBSERVER'>('RESPONDER');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!id) return;
    loadData();
    api.getMe().then(setCurrentUser).catch(console.error);
    api.getUsers().then(setAllUsers).catch(console.error);

    const wsUrl = api.getWebSocketUrl(id);
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'new_message') {
          setMessages(prev => {
            if (prev.some(m => m.id === payload.data.id)) return prev;
            return [...prev, payload.data];
          });
        } else if (['status_change', 'severity_change', 'incident_resolved'].includes(payload.type)) {
          setIncident(prev => prev ? ({ ...prev, ...payload.data }) : payload.data);
          api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
        } else if (payload.type === 'participant_joined') {
          setParticipants(prev => {
            if (prev.some(p => p.user_id === payload.data.user_id)) return prev;
            return [...prev, payload.data];
          });
          api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
        } else if (payload.type === 'user_connected' || payload.type === 'user_disconnected') {
          if (payload.data?.connected_count) {
            setActiveUsersCount(payload.data.connected_count);
          }
        }
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    socket.onerror = () => {
      setWsConnected(false);
    };

    socket.onclose = () => {
      setWsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadData = async () => {
    if (!id) return;
    try {
      const [incRes, msgRes, evtRes, partRes] = await Promise.all([
        api.getIncident(id),
        api.getMessages(id),
        api.getEvents(id),
        api.getParticipants(id)
      ]);
      setIncident(incRes);
      setMessages(msgRes.messages || []);
      setEvents(evtRes.events || []);
      setParticipants(partRes || []);
    } catch (e: any) {
      console.error(e);
      if (e.message?.includes('denied') || e.message?.includes('permission') || e.message?.includes('403')) {
        setAccessDenied(true);
      } else {
        navigate('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  // Determine viewing vs responder permissions
  const canModify = Boolean(
    currentUser &&
    incident && (
      incident.creator_id === currentUser.id ||
      incident.commander_id === currentUser.id ||
      participants.some(
        p => p.user_id === currentUser.id && (p.role === 'COMMANDER' || p.role === 'RESPONDER')
      )
    )
  );

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !id) return;
    
    const body = messageInput.trim();
    setMessageInput('');
    try {
      const posted = await api.postMessage(id, { body });
      setMessages(prev => {
        if (prev.some(m => m.id === posted.id)) return prev;
        return [...prev, posted];
      });
    } catch (e: any) {
      console.error('Failed to send message', e);
      setErrorMessage(e.message || 'Failed to send message');
    }
  };

  const updateStatus = async (newStatus: string) => {
    if (!incident || !id || !canModify) return;
    setErrorMessage('');
    try {
      const updated = await api.updateStatus(id, { status: newStatus, version: incident.version });
      setIncident(updated);
      api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
    } catch (e: any) {
      if (e.message?.includes('Conflict') || e.message?.includes('version')) {
        setErrorMessage('Version conflict detected. Fetching latest state...');
        loadData();
      } else {
        setErrorMessage(e.message || 'Failed to update status');
      }
    }
  };

  const updateSeverity = async (newSeverity: string) => {
    if (!incident || !id || !canModify) return;
    setErrorMessage('');
    try {
      const updated = await api.updateSeverity(id, { severity: newSeverity, version: incident.version });
      setIncident(updated);
      api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
    } catch (e: any) {
      if (e.message?.includes('Conflict') || e.message?.includes('version')) {
        setErrorMessage('Version conflict detected. Fetching latest state...');
        loadData();
      } else {
        setErrorMessage(e.message || 'Failed to update severity');
      }
    }
  };

  const handleResolve = async () => {
    if (!incident || !id || !canModify) return;
    setErrorMessage('');
    try {
      const updated = await api.resolveIncident(id, { 
        version: incident.version,
        resolution_note: resolutionNote.trim() || null 
      });
      setIncident(updated);
      setShowResolveModal(false);
      setResolutionNote('');
      api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
    } catch (e: any) {
      setErrorMessage(e.message || 'Failed to resolve incident');
    }
  };

  const handleAddParticipant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId || !id || !canModify) return;
    setErrorMessage('');
    try {
      const newPart = await api.addParticipant(id, {
        user_id: selectedUserId,
        role: selectedRole
      });
      setParticipants(prev => {
        if (prev.some(p => p.user_id === newPart.user_id)) return prev;
        return [...prev, newPart];
      });
      setShowAddParticipant(false);
      setSelectedUserId('');
      api.getEvents(id).then(res => setEvents(res.events || [])).catch(console.error);
    } catch (e: any) {
      setErrorMessage(e.message || 'Failed to add participant');
    }
  };

  const getVisibilityBadge = (vis?: string, dept?: string) => {
    if (vis === 'RESTRICTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <Lock className="w-3.5 h-3.5 text-rose-600" /> Restricted Access
        </span>
      );
    }
    if (vis === 'DEPARTMENT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200">
          <Building2 className="w-3.5 h-3.5 text-purple-600" /> Dept: {dept || 'Team'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200">
        <Globe className="w-3.5 h-3.5 text-teal-600" /> Organization-wide
      </span>
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex h-[80vh] items-center justify-center">
          <div className="w-10 h-10 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin" />
        </div>
      </Layout>
    );
  }

  if (accessDenied) {
    return (
      <Layout>
        <div className="max-w-md mx-auto my-20 p-8 bg-white border border-rose-200 rounded-2xl shadow-sm text-center">
          <div className="w-14 h-14 bg-rose-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-rose-100">
            <Lock className="w-7 h-7 text-rose-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600 text-sm mb-6 leading-relaxed">
            You do not have permission to view this incident. This report is restricted or designated for a different department.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full py-2.5 bg-slate-900 text-white rounded-xl font-medium text-sm hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Return to Dashboard
          </button>
        </div>
      </Layout>
    );
  }

  if (!incident) return null;

  const validTransitions: Record<string, string[]> = {
    'INVESTIGATING': ['IDENTIFIED'],
    'IDENTIFIED': ['MONITORING'],
    'MONITORING': ['RESOLVED'],
    'RESOLVED': []
  };

  const nextStatus = validTransitions[incident.status]?.[0];

  return (
    <Layout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Navigation & Status alert */}
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-slate-900 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </button>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 bg-white border border-slate-200 rounded-full shadow-xs">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500' : 'bg-red-500 animate-pulse'}`} />
              <span className="text-slate-600">{wsConnected ? 'Real-time Connected' : 'Connecting...'}</span>
              <span className="text-slate-300">|</span>
              <Users className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-600">{activeUsersCount} Online</span>
            </div>
          </div>
        </div>

        {errorMessage && (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl flex items-center justify-between text-sm border border-red-200 shadow-xs">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage('')} className="p-1 hover:bg-red-100 rounded-lg">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* View-Only Banner for non-responders */}
        {!canModify && (
          <div className="p-4 bg-amber-50 border border-amber-200/80 rounded-2xl flex items-start sm:items-center gap-3 text-amber-900 text-xs shadow-xs">
            <Eye className="w-5 h-5 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />
            <div className="flex-1">
              <span className="font-bold">View-Only Access: </span>
              You have access to inspect this incident room and view real-time chatter. Modifying incident lifecycle, severity, or resolution requires responder or commander authorization.
            </div>
          </div>
        )}

        {/* Incident Header Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-3 flex-1 min-w-0">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-xs font-black tracking-wide border ${
                  incident.severity === 'SEV-1' ? 'bg-red-50 text-red-700 border-red-200' :
                  incident.severity === 'SEV-2' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                  incident.severity === 'SEV-3' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                  'bg-slate-50 text-slate-700 border-slate-200'
                }`}>
                  {incident.severity}
                </span>

                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  incident.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                  incident.status === 'MONITORING' ? 'bg-indigo-50 text-indigo-700 border-indigo-200' :
                  incident.status === 'IDENTIFIED' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                  'bg-amber-50 text-amber-700 border-amber-200'
                }`}>
                  {incident.status}
                </span>

                {getVisibilityBadge(incident.visibility, incident.department)}

                <span className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-full border border-slate-200/60">
                  {incident.service_name}
                </span>

                <span className="text-xs text-slate-400 font-mono">
                  v{incident.version} (OCC)
                </span>
              </div>

              <h1 className="text-2xl font-black text-slate-900 tracking-tight leading-snug">
                {incident.title}
              </h1>

              {incident.description && (
                <p className="text-slate-600 text-sm leading-relaxed max-w-4xl">
                  {incident.description}
                </p>
              )}

              <div className="flex items-center gap-6 text-xs text-slate-400 pt-1 flex-wrap">
                <span>Opened: {new Date(incident.created_at).toLocaleString()}</span>
                {incident.creator_name && <span>Reported by: <b className="text-slate-700">{incident.creator_name}</b></span>}
                {incident.commander_name && <span>Commander: <b className="text-slate-700">{incident.commander_name}</b></span>}
              </div>
            </div>

            {/* Action Buttons for Responders */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              {incident.status !== 'RESOLVED' && nextStatus && (
                <button
                  onClick={() => updateStatus(nextStatus)}
                  disabled={!canModify}
                  title={!canModify ? 'Only commanders and responders can update status' : undefined}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-indigo-100 transition-all flex items-center gap-2 cursor-pointer"
                >
                  Advance to {nextStatus}
                </button>
              )}

              {incident.status !== 'RESOLVED' && (
                <button
                  onClick={() => setShowResolveModal(true)}
                  disabled={!canModify}
                  title={!canModify ? 'Only commanders and responders can resolve' : undefined}
                  className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-md shadow-emerald-100 transition-all flex items-center gap-2 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" /> Resolve Incident
                </button>
              )}

              {/* Severity Quick Dropdown */}
              <select
                value={incident.severity}
                disabled={!canModify || incident.status === 'RESOLVED'}
                onChange={e => updateSeverity(e.target.value)}
                title={!canModify ? 'Only responders can change severity' : undefined}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="SEV-1">SEV-1 Critical</option>
                <option value="SEV-2">SEV-2 Major</option>
                <option value="SEV-3">SEV-3 Minor</option>
                <option value="SEV-4">SEV-4 Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Main 2-Column Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Live Chatter (2 spans) */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-xs flex flex-col h-[650px] overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-sm text-slate-900">Incident Stream & Collaboration</h3>
              </div>
              <span className="text-xs text-slate-400 font-medium">Real-time room</span>
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-8">
                  <ShieldAlert className="w-12 h-12 text-slate-200 mb-3" />
                  <p className="text-sm font-semibold text-slate-600">Incident room open</p>
                  <p className="text-xs text-slate-400 mt-1">Post updates, command decisions, diagnostics, and hypotheses.</p>
                </div>
              ) : (
                messages.map((m) => (
                  <div key={m.id} className="flex gap-3 text-xs leading-relaxed">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0">
                      {m.author_name?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div className="flex-1 bg-slate-50/70 border border-slate-100 p-3.5 rounded-xl space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-slate-900">{m.author_name || 'Responder'}</span>
                        <span className="text-slate-400">{new Date(m.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-slate-700 text-xs whitespace-pre-wrap">{m.body}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Box */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 bg-slate-50/50 flex gap-2">
              <input
                type="text"
                value={messageInput}
                onChange={e => setMessageInput(e.target.value)}
                placeholder="Share diagnosis, mitigation plan, or query responders..."
                className="flex-1 px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500 outline-none text-slate-900"
              />
              <button 
                type="submit"
                disabled={!messageInput.trim()}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl font-bold text-xs shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" /> Send
              </button>
            </form>
          </div>

          {/* Right Column: Responders & Audit Timeline (1 span) */}
          <div className="space-y-6">
            {/* Participants Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">Incident Team ({participants.length})</h3>
                </div>
                {canModify && (
                  <button
                    onClick={() => setShowAddParticipant(true)}
                    className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg text-xs font-bold transition-colors flex items-center gap-1 cursor-pointer"
                    title="Invite employee to this incident"
                  >
                    <UserPlus className="w-3.5 h-3.5" /> Invite
                  </button>
                )}
              </div>

              <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
                {participants.map((p) => (
                  <div key={p.user_id} className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-6 h-6 rounded-md bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-[10px] shrink-0">
                        {p.user_name?.[0]?.toUpperCase() || 'U'}
                      </div>
                      <div className="overflow-hidden">
                        <p className="font-bold text-slate-800 truncate">{p.user_name || 'Employee'}</p>
                        <p className="text-[10px] text-slate-400 truncate">{p.user_email}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full shrink-0 ${
                      p.role === 'COMMANDER' ? 'bg-amber-100 text-amber-800' :
                      p.role === 'RESPONDER' ? 'bg-indigo-100 text-indigo-800' :
                      'bg-slate-200 text-slate-700'
                    }`}>
                      {p.role}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Audit History Timeline */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-sm text-slate-900">Audit History Log</h3>
              </div>

              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {events.length === 0 ? (
                  <p className="text-xs text-slate-400">No events logged yet.</p>
                ) : (
                  events.slice().reverse().map((e) => (
                    <div key={e.id} className="text-xs border-l-2 border-indigo-200 pl-3 py-0.5 space-y-0.5">
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span className="font-bold text-indigo-600 uppercase tracking-wider">{e.event_type.replace(/_/g, ' ')}</span>
                        <span>{new Date(e.created_at).toLocaleTimeString()}</span>
                      </div>
                      {e.actor_name && (
                        <p className="text-[11px] text-slate-500">By: <span className="font-semibold text-slate-700">{e.actor_name}</span></p>
                      )}
                      {e.payload && (
                        <p className="text-[11px] text-slate-600 font-mono bg-slate-50 p-1.5 rounded border border-slate-100 overflow-x-auto">
                          {JSON.stringify(e.payload)}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Modal: Add/Invite Participant */}
        {showAddParticipant && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <UserPlus className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-bold text-base text-slate-900">Invite Employee to Incident</h3>
                </div>
                <button onClick={() => setShowAddParticipant(false)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <p className="text-xs text-slate-500">
                Grant explicit access to this incident. Responders can participate and modify status, while observers have view-only access.
              </p>

              <form onSubmit={handleAddParticipant} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Select Employee</label>
                  <select
                    required
                    value={selectedUserId}
                    onChange={e => setSelectedUserId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 outline-none"
                  >
                    <option value="">Choose an employee...</option>
                    {allUsers
                      .filter(u => !participants.some(p => p.user_id === u.id))
                      .map(u => (
                        <option key={u.id} value={u.id}>
                          {u.name} ({u.email}) — {u.department || 'General'}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Assigned Role</label>
                  <div className="grid grid-cols-2 gap-2">
                    <label className={`p-3 rounded-xl border text-xs cursor-pointer ${
                      selectedRole === 'RESPONDER' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'
                    }`}>
                      <input 
                        type="radio" 
                        name="role" 
                        value="RESPONDER"
                        checked={selectedRole === 'RESPONDER'}
                        onChange={() => setSelectedRole('RESPONDER')}
                        className="mr-2 accent-indigo-600"
                      />
                      RESPONDER
                      <span className="block text-[10px] font-normal text-slate-400 mt-0.5">Can edit status & resolve</span>
                    </label>

                    <label className={`p-3 rounded-xl border text-xs cursor-pointer ${
                      selectedRole === 'OBSERVER' ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 font-bold' : 'border-slate-200 text-slate-600'
                    }`}>
                      <input 
                        type="radio" 
                        name="role" 
                        value="OBSERVER"
                        checked={selectedRole === 'OBSERVER'}
                        onChange={() => setSelectedRole('OBSERVER')}
                        className="mr-2 accent-indigo-600"
                      />
                      OBSERVER
                      <span className="block text-[10px] font-normal text-slate-400 mt-0.5">View & monitor only</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddParticipant(false)}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!selectedUserId}
                    className="px-5 py-2 text-xs font-bold bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
                  >
                    Confirm Invite
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Resolve Incident */}
        {showResolveModal && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-bold text-base text-slate-900">Resolve Incident</h3>
                </div>
                <button onClick={() => setShowResolveModal(false)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <p className="text-xs text-slate-500">
                Marking this incident as resolved will close active response and archive the war room.
              </p>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Resolution Summary Note</label>
                <textarea
                  value={resolutionNote}
                  onChange={e => setResolutionNote(e.target.value)}
                  placeholder="Root cause identified, patch deployed to production, traffic restored..."
                  rows={4}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 outline-none text-slate-900"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowResolveModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  onClick={handleResolve}
                  className="px-5 py-2 text-xs font-bold bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 cursor-pointer shadow-sm shadow-emerald-200"
                >
                  Mark as Resolved
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
