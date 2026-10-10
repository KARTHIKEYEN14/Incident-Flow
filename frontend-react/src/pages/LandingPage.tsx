import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowRight, Zap, CheckCircle2, Lock, Radio, ChevronDown } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50/50 via-white to-slate-50 text-slate-900 flex flex-col selection:bg-indigo-100 selection:text-indigo-900">
      {/* Light Navbar */}
      <header className="px-6 md:px-12 py-5 flex justify-between items-center bg-white/90 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-50 shadow-xs h-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-200">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <span className="text-xl font-extrabold tracking-tight text-slate-900">
            IncidentFlow
          </span>
        </div>
        <nav className="flex items-center gap-4">
          <Link 
            to="/login" 
            className="px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold transition-all border border-slate-200 shadow-xs cursor-pointer"
          >
            Sign In
          </Link>
          <Link 
            to="/login" 
            className="hidden sm:inline-flex px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition-all shadow-md shadow-indigo-200 cursor-pointer"
          >
            Get Started
          </Link>
        </nav>
      </header>

      {/* Hero Section - Full First Screen Fold */}
      <section className="min-h-[calc(100vh-5rem)] flex flex-col justify-center items-center px-6 py-12 text-center max-w-5xl mx-auto w-full">
        <div className="space-y-6 max-w-4xl my-auto">
          <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-200/80 text-indigo-700 text-xs font-bold uppercase tracking-wider shadow-xs">
            <span className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />
            Real-time Outage Response Platform
          </div>
          
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight leading-[1.1] text-slate-900">
            Coordinate, Mitigate &amp; <br className="hidden sm:block" />
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 bg-clip-text text-transparent">
              Resolve Outages Faster
            </span>
          </h1>
          
          <p className="text-base sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed font-normal">
            A high-speed incident command center for engineering teams. Synchronize live updates 
            via WebSockets, protect state with optimistic concurrency, and track full audit timelines.
          </p>

          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 pt-4">
            <Link 
              to="/login"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-base transition-all shadow-xl shadow-indigo-200 hover:-translate-y-0.5 flex items-center justify-center gap-2 group cursor-pointer"
            >
              Open IncidentFlow <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a 
              href="#preview"
              className="w-full sm:w-auto px-7 py-4 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-base transition-all border border-slate-200 shadow-sm cursor-pointer"
            >
              Explore Capabilities
            </a>
          </div>
        </div>

        {/* Scroll indicator pointing to the next container */}
        <a 
          href="#preview" 
          className="pb-4 pt-8 flex flex-col items-center justify-center text-slate-400 hover:text-indigo-600 transition-colors group cursor-pointer"
        >
          <span className="text-xs font-semibold text-slate-400 group-hover:text-indigo-600 mb-1 transition-colors">
            Scroll to preview
          </span>
          <ChevronDown className="w-5 h-5 text-indigo-500 animate-bounce" />
        </a>
      </section>

      {/* Container 2: Live UI Mockup Preview - Visible after scrolling */}
      <section id="preview" className="py-24 px-6 max-w-6xl mx-auto w-full flex flex-col items-center scroll-mt-20">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold uppercase tracking-wider mb-3">
            Live Workspace
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
            IncidentFlow Command Center
          </h2>
          <p className="text-slate-500 mt-2 text-base max-w-xl mx-auto">
            Experience real-time telemetry, responder messaging, and automated audit logs in one streamlined view.
          </p>
        </div>

        <div className="w-full rounded-3xl bg-white p-3 sm:p-5 border border-slate-200 shadow-2xl shadow-indigo-100/70">
          <div className="rounded-2xl bg-slate-50 border border-slate-200 overflow-hidden text-left p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-400 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-amber-400 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-emerald-400 inline-block" />
                </div>
                <span className="text-xs text-slate-500 font-mono font-medium ml-2">incidentflow #inc-9142 • live</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  SEV-1 CRITICAL
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  INVESTIGATING
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-5">
              <div className="md:col-span-2 space-y-3 font-sans">
                <p className="text-sm font-bold text-slate-900">Payment Gateway 504 Gateway Timeouts</p>
                
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span className="font-bold text-indigo-700">Alice (Commander)</span>
                    <span>14:02 UTC</span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    Database connection pool exhausted after upstream auth spike. Scaling read replicas now.
                  </p>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span className="font-bold text-emerald-700">Bob (Responder)</span>
                    <span>14:04 UTC</span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    Replicas scaled. Latency returning to nominal 45ms across all clusters.
                  </p>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Command Roster</p>
                <div className="flex items-center gap-2.5 text-xs text-slate-800 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Alice (Commander)
                </div>
                <div className="flex items-center gap-2.5 text-xs text-slate-800 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Bob (Responder)
                </div>
                <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center gap-1.5 font-mono">
                  <Radio className="w-3 h-3 text-emerald-600 animate-pulse" /> WebSocket: connected (2 peers)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Container 3: Features Grid */}
      <section id="features" className="py-20 px-6 max-w-6xl mx-auto w-full">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Engineered for High-Pressure Outage Response
          </h2>
          <p className="text-slate-500 mt-2 text-sm max-w-lg mx-auto">
            Everything your response team needs to stabilize systems and communicate clearly.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard 
            icon={<Zap className="w-6 h-6 text-amber-600" />}
            title="Real-time WebSockets"
            desc="Sub-millisecond broadcast of incident events, responder chat, and team coordination without polling."
          />
          <FeatureCard 
            icon={<Lock className="w-6 h-6 text-indigo-600" />}
            title="Optimistic Concurrency"
            desc="Robust OCC guarantees prevent conflicting status changes or race conditions during chaos."
          />
          <FeatureCard 
            icon={<CheckCircle2 className="w-6 h-6 text-emerald-600" />}
            title="Full Audit Timeline"
            desc="Immutable event streaming captures every severity switch, participant joining, and resolution note."
          />
        </div>
      </section>

      {/* Light Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 px-6 text-center text-xs text-slate-500 mt-auto">
        <p>&copy; {new Date().getFullYear()} IncidentFlow. Powered by FastAPI &amp; React.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: ReactNode, title: string, desc: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-200 transition-all text-left shadow-xs hover:shadow-lg">
      <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}
