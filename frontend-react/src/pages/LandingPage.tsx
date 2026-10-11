import { Link } from 'react-router-dom';
import {
  ShieldAlert, ArrowRight, ChevronRight, Radio, Activity,
  CheckCircle2, Lock, Users, Terminal, Cpu, Clock,
  GitCommit
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F3F6FC] text-[#111827] flex flex-col font-sans selection:bg-[#365CF5]/10 selection:text-[#365CF5]">

      {/* 1. SLIM REFINED NAVIGATION */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-[#DCE4F0]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Left: Brand */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[#365CF5] flex items-center justify-center text-white shadow-sm">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-[#111827]">
                IncidentFlow
              </span>
            </div>
          </Link>

          {/* Center: Nav Anchors */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#workflow" className="hover:text-[#111827] transition-colors">
              Workflow
            </a>
            <a href="#features" className="hover:text-[#111827] transition-colors">
              Features
            </a>
            <a href="#reliability" className="hover:text-[#111827] transition-colors">
              Reliability
            </a>
          </nav>

          {/* Right: Auth Actions */}
          <div className="flex items-center gap-3">
            <Link
              to="/testing"
              className="hidden sm:flex px-3 py-1.5 text-xs font-semibold text-[#365CF5] bg-[#365CF5]/10 hover:bg-[#365CF5]/20 border border-[#365CF5]/25 rounded-md transition-colors items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5" />
              Testing
            </Link>
            <Link
              to="/login"
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:text-[#111827] rounded-md transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="px-3.5 py-1.5 rounded-md bg-[#365CF5] hover:bg-[#2849D6] text-white text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* 2. DISTINCTIVE ASYMMETRIC HERO SECTION */}
      <section className="min-h-[calc(100vh-4rem)] flex flex-col justify-center border-b border-[#DCE4F0] py-8 lg:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full my-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center">

            {/* Left Column: Editorial & Technical Copy */}
            <div className="lg:col-span-5 space-y-6">
              {/* Eyebrow */}
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-[#365CF5]/10 border border-[#365CF5]/20 text-[#365CF5] text-[11px] font-mono font-bold tracking-wider uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-[#365CF5] animate-pulse" />
                INCIDENT RESPONSE PLATFORM
              </div>

              {/* Headline */}
              <h1 className="text-3xl sm:text-4xl lg:text-[44px] font-black text-[#111827] tracking-tight leading-[1.12]">
                When systems fail, your team moves as one.
              </h1>

              {/* Supporting Copy */}
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
                Coordinate high-stakes incidents with real-time WebSocket chatter, OCC concurrency guards that prevent state clobbering, role-based command rosters, and persistent audit histories that record every mitigation decision from triage to resolution.
              </p>

              {/* CTAs */}
              <div className="pt-2 flex flex-wrap items-center gap-3">
                <Link
                  to="/login"
                  className="px-5 py-2.5 rounded-lg bg-[#365CF5] hover:bg-[#2849D6] text-white text-sm font-semibold shadow-xs transition-colors flex items-center gap-2 cursor-pointer"
                >
                  Launch IncidentFlow <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  to="/testing"
                  className="px-4 py-2.5 rounded-lg border border-slate-300 hover:border-[#365CF5] text-slate-700 hover:text-[#365CF5] text-sm font-semibold transition-colors flex items-center gap-2 cursor-pointer bg-white shadow-2xs"
                >
                  <Activity className="w-4 h-4 text-[#365CF5]" /> Automated Testing
                </Link>
                <a
                  href="#workflow"
                  className="text-sm font-semibold text-slate-700 hover:text-[#365CF5] transition-colors inline-flex items-center gap-1.5"
                >
                  Explore the workflow <ChevronRight className="w-4 h-4 text-slate-400" />
                </a>
              </div>

              {/* Credibility Strip */}
              <div className="pt-6 border-t border-[#DCE4F0]">
                <p className="text-xs font-mono text-slate-500 flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-slate-700">Real-time collaboration</span>
                  <span>·</span>
                  <span className="font-semibold text-slate-700">Version-safe updates</span>
                  <span>·</span>
                  <span className="font-semibold text-slate-700">Persistent audit trails</span>
                </p>
              </div>
            </div>

            {/* Right Column: Realistic Engineering Operations Console Preview */}
            <div className="lg:col-span-7">
              <div className="rounded-xl border border-[#DCE4F0] bg-white shadow-xl shadow-slate-200/50 overflow-hidden">

                {/* Dark Navy Incident Console Top Bar */}
                <div className="bg-[#0F172A] p-4 text-white border-b border-slate-800">
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                    <div className="flex items-center gap-2.5">
                      <div className="flex gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
                      </div>
                      <span className="font-mono text-xs text-slate-400 font-medium tracking-tight">
                        CONSOLE // warroom-east-01
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        WS: CONNECTED (3 ACTIVE)
                      </span>
                    </div>
                  </div>

                  {/* Incident Header in Console */}
                  <div className="pt-3 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-red-500 text-white tracking-wider">
                        SEV-1 CRITICAL
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        INVESTIGATING
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        SERVICE: AUTH-JWT
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 ml-auto">
                        OCC v4 · STATE LOCKED
                      </span>
                    </div>
                    <p className="text-sm sm:text-base font-bold text-white tracking-tight">
                      Authentication Token Validation Gateway — 504 Gateway Timeouts
                    </p>
                  </div>
                </div>

                {/* Service Status Strip */}
                <div className="bg-[#F8FAFC] border-b border-[#DCE4F0] px-4 py-2.5 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                  <div className="flex items-center justify-between pr-2 border-r border-[#DCE4F0]">
                    <span className="text-slate-500">JWT Gateway</span>
                    <span className="text-rose-600 font-bold">1,820ms</span>
                  </div>
                  <div className="flex items-center justify-between px-2 sm:border-r border-[#DCE4F0]">
                    <span className="text-slate-500">Read Replica</span>
                    <span className="text-amber-600 font-bold">REBUILD</span>
                  </div>
                  <div className="flex items-center justify-between px-2 border-r border-[#DCE4F0]">
                    <span className="text-slate-500">Auth DB Primary</span>
                    <span className="text-emerald-600 font-bold">HEALTHY</span>
                  </div>
                  <div className="flex items-center justify-between pl-2">
                    <span className="text-slate-500">Edge Ingress</span>
                    <span className="text-emerald-600 font-bold">99.98%</span>
                  </div>
                </div>

                {/* Console Main Body: Collaboration Feed + Roster */}
                <div className="grid grid-cols-1 md:grid-cols-12 divide-y md:divide-y-0 md:divide-x divide-[#DCE4F0] text-xs">

                  {/* Left: Real-time Incident Stream */}
                  <div className="md:col-span-8 p-4 space-y-3 bg-white">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pb-1 border-b border-slate-100 font-mono">
                      <span>STREAM // ACTIVE CHATTER</span>
                      <span>SYNC INTERVAL: 0ms</span>
                    </div>

                    {/* Chat Item 1 */}
                    <div className="p-2.5 rounded-lg bg-[#F3F6FC] border border-[#DCE4F0] space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-[#111827] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#365CF5]" />
                          Alice Chen <span className="font-mono text-[10px] text-[#365CF5] font-normal">[COMMANDER]</span>
                        </span>
                        <span className="font-mono text-slate-400 text-[10px]">19:02:14 UTC</span>
                      </div>
                      <p className="text-slate-700 text-[11px] leading-relaxed">
                        Read replica connection pool saturated after upstream token surge. Shifting validation cache to local Redis fallback now.
                      </p>
                    </div>

                    {/* Chat Item 2 */}
                    <div className="p-2.5 rounded-lg bg-[#F3F6FC] border border-[#DCE4F0] space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-[#111827] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          David Kim <span className="font-mono text-[10px] text-emerald-700 font-normal">[RESPONDER]</span>
                        </span>
                        <span className="font-mono text-slate-400 text-[10px]">19:03:45 UTC</span>
                      </div>
                      <p className="text-slate-700 text-[11px] leading-relaxed">
                        Redis fallback active. p99 response latency dropped from 1,820ms to 42ms. Zero token validation errors reported in last 90s.
                      </p>
                    </div>

                    {/* System Audit Action Pill */}
                    <div className="p-2 rounded bg-amber-50 border border-amber-200/80 text-[10px] font-mono text-amber-900 flex items-center justify-between">
                      <span className="flex items-center gap-1.5 font-bold">
                        <GitCommit className="w-3 h-3 text-amber-600" />
                        STATUS ADVANCED → IDENTIFIED
                      </span>
                      <span className="text-slate-500">By Alice Chen · v4</span>
                    </div>
                  </div>

                  {/* Right: Roster & Controls Panel */}
                  <div className="md:col-span-4 p-4 space-y-4 bg-[#F8FAFC]">
                    <div>
                      <p className="text-[11px] font-mono font-bold text-slate-500 uppercase tracking-wider mb-2">
                        ROSTER (3 ACTIVE)
                      </p>
                      <div className="space-y-1.5">
                        <div className="p-1.5 rounded bg-white border border-[#DCE4F0] flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-slate-800 truncate">Alice Chen</span>
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-amber-100 text-amber-800">
                            CMD
                          </span>
                        </div>
                        <div className="p-1.5 rounded bg-white border border-[#DCE4F0] flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-slate-800 truncate">David Kim</span>
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-[#365CF5]/10 text-[#365CF5]">
                            RESP
                          </span>
                        </div>
                        <div className="p-1.5 rounded bg-white border border-[#DCE4F0] flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-slate-800 truncate">Carol Singh</span>
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-slate-100 text-slate-600">
                            OBS
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-[#DCE4F0]">
                      <p className="text-[10px] font-mono text-slate-500 mb-1.5">LIFECYCLE CONTROL</p>
                      <div className="w-full py-1.5 px-2 bg-[#365CF5] text-white rounded text-center font-bold text-[11px] cursor-default shadow-2xs">
                        Advance to MONITORING
                      </div>
                      <p className="text-[9px] font-mono text-slate-400 mt-1 text-center">
                        Guarded by OCC Version 4
                      </p>
                    </div>
                  </div>
                </div>

                {/* Console Footer Status */}
                <div className="px-4 py-2 bg-slate-900 text-slate-400 border-t border-slate-800 text-[10px] font-mono flex items-center justify-between">
                  <span>TELEMETRY: FASTAPI + POSTGRESQL + WEBSOCKET</span>
                  <span className="text-emerald-400 font-bold">STABLE 0 ERRORS</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 3. WORKFLOW STRIP: REPORT → COORDINATE → RESOLVE */}
      <section id="workflow" className="min-h-[calc(100vh-4rem)] flex flex-col justify-center bg-white border-b border-[#DCE4F0] py-12 px-4 sm:px-6 lg:px-8 scroll-mt-16">
        <div className="max-w-7xl mx-auto w-full my-auto">
          <div className="mb-8">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#365CF5]">
              LIFECYCLE EXECUTION
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#111827] tracking-tight mt-1">
              From initial telemetry alert to verified resolution
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Step 1 */}
            <div className="p-6 rounded-xl bg-[#F3F6FC] border border-[#DCE4F0] space-y-3 relative group">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-black text-[#365CF5] bg-[#365CF5]/10 px-2 py-0.5 rounded">
                  STAGE 01
                </span>
                <span className="text-xs font-mono text-slate-400">INGRESS</span>
              </div>
              <h3 className="text-base font-bold text-[#111827]">
                Report &amp; Department Triage
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Declare incidents with explicit severity tags (SEV-1 to SEV-4) and scoped visibility. Targeted departments immediately receive filtered alerts while restricted rooms maintain strict authorization boundaries.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-xl bg-[#F3F6FC] border border-[#DCE4F0] space-y-3 relative group">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-black text-[#365CF5] bg-[#365CF5]/10 px-2 py-0.5 rounded">
                  STAGE 02
                </span>
                <span className="text-xs font-mono text-slate-400">EXECUTION</span>
              </div>
              <h3 className="text-base font-bold text-[#111827]">
                Live Coordination &amp; OCC Guard
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Incident commanders and responders collaborate in dedicated WebSocket rooms. Optimistic Concurrency Control checks guarantee that simultaneous state changes never overwrite concurrent responder actions.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-xl bg-[#F3F6FC] border border-[#DCE4F0] space-y-3 relative group">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-black text-[#365CF5] bg-[#365CF5]/10 px-2 py-0.5 rounded">
                  STAGE 03
                </span>
                <span className="text-xs font-mono text-slate-400">COMPLETION</span>
              </div>
              <h3 className="text-base font-bold text-[#111827]">
                Resolution &amp; Audit Trace
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Transition smoothly through Investigating, Identified, Monitoring, and Resolved. All diagnostic notes, participants, and severity shifts persist to an immutable PostgreSQL event log ready for post-mortem analysis.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. DIFFERENTIATED FEATURES SECTION */}
      <section id="features" className="min-h-[calc(100vh-4rem)] flex flex-col justify-center border-b border-[#DCE4F0] py-12 px-4 sm:px-6 lg:px-8 scroll-mt-16">
        <div className="max-w-7xl mx-auto w-full my-auto">
          <div className="max-w-3xl mb-10">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#365CF5]">
              SYSTEM CAPABILITIES
            </span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-[#111827] tracking-tight mt-1">
              Engineered for reliability under operational pressure
            </h2>
            <p className="text-sm text-slate-600 mt-2">
              Every feature in IncidentFlow is built to eliminate race conditions, coordination friction, and communication lag during live outages.
            </p>
          </div>

          {/* Feature 1: Live Collaboration (Split Layout) */}
          <div className="mb-8 rounded-2xl bg-white border border-[#DCE4F0] p-6 lg:p-8 shadow-xs">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-6 space-y-4">
                <div className="w-10 h-10 rounded-lg bg-[#365CF5]/10 text-[#365CF5] flex items-center justify-center">
                  <Radio className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold text-[#111827] tracking-tight">
                  Live Sub-Millisecond Collaboration
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Bidirectional WebSocket streaming broadcasts hypotheses, mitigation steps, and command directives instantaneously to every connected peer. No polling cycles, no stale caches, and no page refreshes needed during fast-moving diagnostics.
                </p>
                <ul className="space-y-2 text-xs text-slate-700 font-medium">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    Real-time participant presence and connection telemetry
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    Instant synchronization across commanders, responders, and observers
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    Zero message drops with automated reconnection recovery
                  </li>
                </ul>
              </div>

              <div className="lg:col-span-6 bg-[#0F172A] rounded-xl p-4 text-slate-300 font-mono text-xs border border-slate-800">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-[11px] text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-[#365CF5]" />
                    SOCKET STREAM // WS_INCOMING_EVENT
                  </span>
                  <span className="text-emerald-400">STREAMING</span>
                </div>
                <div className="pt-3 space-y-2 text-[11px]">
                  <p className="text-slate-400">&#47;&#47; Client dispatched atomic message payload</p>
                  <p className="text-emerald-400">{`{"type": "new_message", "incident_id": "4092-jwt"}`}</p>
                  <p className="text-slate-300">
                    <span className="text-sky-400">author:</span> &quot;David Kim&quot; · <span className="text-sky-400">role:</span> &quot;RESPONDER&quot;
                  </p>
                  <p className="text-amber-300">
                    <span className="text-sky-400">body:</span> &quot;Fallback cache primed. Latency nominal.&quot;
                  </p>
                  <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
                    <span>DISPATCH LATENCY: 2.4ms</span>
                    <span>PEERS NOTIFIED: 3</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2 & 3: OCC and Persistent Audit (2 Column Distinct Layouts) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

            {/* Feature 2: Optimistic Concurrency Control */}
            <div className="rounded-2xl bg-white border border-[#DCE4F0] p-6 lg:p-8 shadow-xs space-y-5 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[#111827]">
                  Optimistic Concurrency Protection (OCC)
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  When multiple engineers advance lifecycle status or change severity levels simultaneously, traditional systems produce silent race condition overwrites. IncidentFlow enforces strict OCC version tokens.
                </p>
              </div>

              {/* Visual OCC Version Guard Box */}
              <div className="rounded-xl bg-[#F8FAFC] border border-[#DCE4F0] p-4 text-xs font-mono space-y-2.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-slate-700">VERSION STATE CHECK</span>
                  <span className="text-emerald-600 font-bold">MATCH (COMMITTED)</span>
                </div>
                <div className="p-2 rounded bg-white border border-slate-200 space-y-1">
                  <div className="flex justify-between text-slate-600">
                    <span>Incident Version:</span>
                    <span className="font-bold text-[#111827]">v4</span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Expected Version:</span>
                    <span className="font-bold text-[#111827]">v4</span>
                  </div>
                </div>
                <div className="p-2 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px]">
                  <span className="font-bold">Collision Prevention:</span> Version mismatch instantly rejects stale requests with HTTP 409 Conflict, safeguarding database integrity.
                </div>
              </div>
            </div>

            {/* Feature 3: Persistent Audit Timeline */}
            <div className="rounded-2xl bg-white border border-[#DCE4F0] p-6 lg:p-8 shadow-xs space-y-5 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                  <Clock className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-[#111827]">
                  Immutable Forensic Audit Trail
                </h3>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  Every participant invite, severity downgrade, lifecycle transition, and mitigation resolution note is logged chronologically to PostgreSQL as an immutable event with actor attribution.
                </p>
              </div>

              {/* Visual Audit Log Sample */}
              <div className="rounded-xl bg-[#F8FAFC] border border-[#DCE4F0] p-4 text-xs space-y-2.5">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pb-1 border-b border-slate-200">
                  <span>AUDIT RECORD</span>
                  <span>EVENT LOG</span>
                </div>

                <div className="space-y-2 text-[11px]">
                  <div className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <div className="flex-1">
                      <div className="flex justify-between">
                        <span className="font-bold text-slate-900">Incident Created (SEV-1)</span>
                        <span className="font-mono text-slate-400 text-[10px]">19:00:12</span>
                      </div>
                      <span className="text-slate-500 text-[10px]">By Alice Chen · Org-wide</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#365CF5] mt-1.5 shrink-0" />
                    <div className="flex-1">
                      <div className="flex justify-between">
                        <span className="font-bold text-slate-900">Participant Joined [RESPONDER]</span>
                        <span className="font-mono text-slate-400 text-[10px]">19:01:45</span>
                      </div>
                      <span className="text-slate-500 text-[10px]">David Kim invited</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <div className="flex-1">
                      <div className="flex justify-between">
                        <span className="font-bold text-slate-900">Status Advanced → IDENTIFIED</span>
                        <span className="font-mono text-slate-400 text-[10px]">19:03:02</span>
                      </div>
                      <span className="text-slate-500 text-[10px]">By Alice Chen · OCC v4</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 5. LIGHT THEME FEATURE SECTION: SYNCHRONIZED RESPONDERS */}
      <section id="reliability" className="min-h-[calc(100vh-4rem)] flex flex-col justify-center bg-white text-[#111827] border-b border-[#DCE4F0] py-12 px-4 sm:px-6 lg:px-8 scroll-mt-16">
        <div className="max-w-7xl mx-auto w-full my-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">

            {/* Left: Synchronized Responder Narrative */}
            <div className="lg:col-span-6 space-y-6">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#365CF5]">
                COMMAND SYNCHRONIZATION
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#111827] tracking-tight leading-tight">
                How distributed engineering responders maintain absolute alignment.
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                In high-pressure outages, split-second decisions cannot depend on disconnected Slack channels or uncoordinated wiki pages. IncidentFlow establishes a single source of truth that aligns technical response teams in seconds.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#DCE4F0] space-y-1.5">
                  <div className="flex items-center gap-2 text-[#111827] font-bold text-sm">
                    <Users className="w-4 h-4 text-[#365CF5]" />
                    Role Hierarchy
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Clear delineation between Commanders who own lifecycle decisions, Responders who deploy fixes, and Observers.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#DCE4F0] space-y-1.5">
                  <div className="flex items-center gap-2 text-[#111827] font-bold text-sm">
                    <Cpu className="w-4 h-4 text-emerald-600" />
                    Department Scoping
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Targeted isolation for Engineering, Security, Finance, and Operations rooms with database-level access control.
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Architectural Reliability Metrics */}
            <div className="lg:col-span-6">
              <div className="rounded-2xl bg-[#F8FAFC] border border-[#DCE4F0] p-6 sm:p-8 space-y-6 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-[#DCE4F0] font-mono text-xs text-slate-500">
                  <span>ENGINEERING SPECS</span>
                  <span className="text-[#365CF5] font-bold">ENTERPRISE ARCHITECTURE</span>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-1">
                    <p className="text-3xl sm:text-4xl font-black text-[#111827] font-mono">0ms</p>
                    <p className="text-xs font-semibold text-slate-700">Polling Lag</p>
                    <p className="text-[11px] text-slate-500">Instant WebSocket broadcast</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-3xl sm:text-4xl font-black text-[#111827] font-mono">100%</p>
                    <p className="text-xs font-semibold text-slate-700">OCC Protection</p>
                    <p className="text-[11px] text-slate-500">Atomic version checking</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-3xl sm:text-4xl font-black text-[#111827] font-mono">4-Tier</p>
                    <p className="text-xs font-semibold text-slate-700">Severity Triage</p>
                    <p className="text-[11px] text-slate-500">SEV-1 Critical to SEV-4</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-3xl sm:text-4xl font-black text-[#111827] font-mono">Full</p>
                    <p className="text-xs font-semibold text-slate-700">Audit Immutability</p>
                    <p className="text-[11px] text-slate-500">Actor &amp; timestamped logs</p>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-white border border-[#DCE4F0] text-xs font-mono text-slate-700 flex items-center justify-between shadow-2xs">
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-600" />
                    Stack: FastAPI · PostgreSQL · React · WebSockets
                  </span>
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    ACTIVE
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 6. CALL TO ACTION & FOOTER SECTION */}
      <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-between scroll-mt-16">
        <section className="my-auto py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
          <div className="rounded-2xl bg-[#365CF5] text-white p-8 sm:p-12 shadow-xl shadow-[#365CF5]/20 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="space-y-2 max-w-xl">
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                Ready to elevate your incident response?
              </h2>
              <p className="text-sm text-blue-100 leading-relaxed">
                Launch an incident command room in seconds. Experience real-time collaboration, OCC concurrency guards, and compliance-grade audit logging.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <Link
                to="/login"
                className="px-6 py-3 rounded-lg bg-white text-[#365CF5] font-bold text-sm hover:bg-blue-50 transition-colors shadow-sm flex items-center gap-2 cursor-pointer"
              >
                Launch IncidentFlow <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="px-5 py-3 rounded-lg border border-white/30 text-white font-semibold text-sm hover:bg-white/10 transition-colors cursor-pointer"
              >
                Sign In
              </Link>
            </div>
          </div>
        </section>

        {/* 7. CLEAN ENGINEERING FOOTER */}
        <footer className="bg-white border-t border-[#DCE4F0] py-10 px-4 sm:px-6 lg:px-8 mt-auto">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-slate-500">

            <div className="flex items-center gap-3">
              <div className="w-6 h-6 rounded bg-[#365CF5] flex items-center justify-center text-white">
                <ShieldAlert className="w-3.5 h-3.5" />
              </div>
              <span className="font-bold text-slate-800 text-sm">IncidentFlow</span>
              <span className="text-slate-300">|</span>
              <span>Collaborative Incident &amp; Outage Management</span>
            </div>

            <div className="flex items-center gap-6 font-medium">
              <a href="#workflow" className="hover:text-slate-900 transition-colors">
                Workflow
              </a>
              <a href="#features" className="hover:text-slate-900 transition-colors">
                Features
              </a>
              <a href="#reliability" className="hover:text-slate-900 transition-colors">
                Reliability
              </a>
              <Link to="/login" className="hover:text-slate-900 transition-colors">
                Login
              </Link>
            </div>

            <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              <span>ALL SYSTEMS OPERATIONAL</span>
            </div>

          </div>

          <div className="max-w-7xl mx-auto mt-6 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-400">
            <p>&copy; {new Date().getFullYear()} IncidentFlow. Built for high-stakes engineering operations.</p>
            <p className="font-mono">FastAPI · PostgreSQL · React · WebSockets</p>
          </div>
        </footer>
      </div>

    </div>
  );
}
