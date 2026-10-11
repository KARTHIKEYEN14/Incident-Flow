import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Play,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowLeft,
} from 'lucide-react';
import { api } from '../lib/api';

interface TestCase {
  id: string;
  test_key: string;
  feature_name: string;
  category: string;
  title: string;
  description?: string;
}

interface TestResult {
  id: string;
  test_case_id: string;
  feature_name: string;
  category: string;
  title: string;
  status: 'PASSED' | 'FAILED' | 'BLOCKED' | 'SKIPPED';
  duration_ms: number;
  error_message?: string;
  description?: string;
}

interface TestRunSummary {
  id: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  duration_ms: number;
}

export default function TestingDashboard() {
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [results, setResults] = useState<TestResult[]>([]);
  const [currentRun, setCurrentRun] = useState<TestRunSummary | null>(null);

  // Batch & Cycle states
  const [batchNumber, setBatchNumber] = useState<number | null>(null);
  const [roundNumber, setRoundNumber] = useState<number | null>(null);
  const [cycleRestarted, setCycleRestarted] = useState<boolean>(false);

  // Loading states
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Helper to ensure an authenticated session for running or generating tests
  const ensureAuthenticated = async (): Promise<boolean> => {
    if (api.getToken()) {
      return true;
    }
    // Seamless fallback to pre-seeded staff account so anyone can test without friction
    try {
      const res = await api.login({ email: 'alice@warroom.dev', password: 'password123' });
      if (res?.access_token) {
        api.setToken(res.access_token);
        return true;
      }
    } catch {
      // User can manually log in via /login if needed
    }
    return false;
  };

  const loadData = async () => {
    setLoadingInitial(true);
    setErrorMessage(null);
    try {

      // Load current active batch of 5 test cases
      try {
        const batchInfo = await api.getCurrentBatch();
        if (batchInfo?.batch_tests && batchInfo.batch_tests.length > 0) {
          setTestCases(batchInfo.batch_tests);
          setBatchNumber(batchInfo.batch_number || 1);
          setRoundNumber(batchInfo.round_number || 1);
          setCycleRestarted(!!batchInfo.cycle_restarted);
        } else {
          const cases = await api.getTestCases();
          setTestCases(cases || []);
          setBatchNumber(1);
          setRoundNumber(1);
        }
      } catch {
        const cases = await api.getTestCases();
        setTestCases(cases || []);
        setBatchNumber(1);
        setRoundNumber(1);
      }

      // Fresh batch begins in ready state; do not show stale runs as current batch results
      setResults([]);
      setCurrentRun(null);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load test cases.');
    } finally {
      setLoadingInitial(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateTests = async () => {
    setIsGenerating(true);
    setFeedback(null);
    setErrorMessage(null);
    try {
      const authed = await ensureAuthenticated();
      if (!authed) {
        setErrorMessage('Authentication required. Please sign in to generate test cases.');
        return;
      }
      const resp = await api.generateTestCases();
      const newBatch = resp.batch_tests || [];
      setTestCases(newBatch);
      setBatchNumber(resp.batch_number || 1);
      setRoundNumber(resp.round_number || 1);
      setCycleRestarted(!!resp.cycle_restarted);
      // Reset run results for fresh generated batch
      setResults([]);
      setCurrentRun(null);
      setFeedback(resp.message || `Generated Batch ${resp.batch_number || 1} · ${newBatch.length} test cases.`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to generate test cases.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunTests = async () => {
    setIsRunning(true);
    setFeedback(null);
    setErrorMessage(null);
    try {
      const authed = await ensureAuthenticated();
      if (!authed) {
        setErrorMessage('Authentication required. Please sign in to run automated tests.');
        return;
      }
      // Execute ONLY the currently displayed batch of test cases
      const targetIds = testCases.map((t) => t.id);
      const runDetail = await api.runTests({ test_case_ids: targetIds });
      if (runDetail?.run) {
        setCurrentRun({
          id: runDetail.run.id,
          total_tests: runDetail.run.total_tests,
          passed_tests: runDetail.run.passed_tests,
          failed_tests: runDetail.run.failed_tests,
          duration_ms: runDetail.run.duration_ms,
        });
      }
      // Map descriptions onto results for clear rendering
      const caseMap = new Map(testCases.map((c) => [c.id, c.description]));
      const enrichedResults = (runDetail.results || []).map((r: TestResult) => ({
        ...r,
        description: caseMap.get(r.test_case_id) || r.description,
      }));
      setResults(enrichedResults);
      setFeedback(`Batch execution completed (${runDetail.run?.passed_tests || 0} passed).`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Test execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  // Determine tests to display: actual run results if available, else generated test cases
  const displayedItems = results.length > 0 ? results : testCases;

  return (
    <div className="min-h-screen bg-[#F3F6FC] text-[#111827] flex flex-col font-sans selection:bg-[#365CF5]/10 selection:text-[#365CF5]">
      {/* 1. TOP HEADER */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-[#DCE4F0]">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-2 text-slate-500 hover:text-[#111827] transition-colors pr-3 border-r border-slate-200 text-xs font-semibold"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>IncidentFlow Home</span>
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#365CF5] flex items-center justify-center text-white shadow-sm">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-[#111827]">IncidentFlow</span>
                <span className="ml-2 px-2 py-0.5 text-[10px] font-mono font-bold tracking-wide uppercase bg-[#365CF5]/10 text-[#365CF5] rounded">
                  Automated Testing
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 2. MAIN SECTION */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-8 flex-1">
        {/* Title & Action Buttons */}
        <div className="bg-white rounded-2xl border border-[#DCE4F0] p-6 shadow-xs mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-black text-[#111827] tracking-tight">
                Automated Testing
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Verify implemented IncidentFlow features against the isolated test environment.
              </p>
            </div>

            {/* Action Buttons: 1. Generate New Test Cases, 2. Run Tests */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                id="btn-generate-tests"
                onClick={handleGenerateTests}
                disabled={isGenerating || isRunning}
                className="px-4 py-2.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-xl transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Sparkles className={`w-3.5 h-3.5 text-[#365CF5] ${isGenerating ? 'animate-spin' : ''}`} />
                {isGenerating ? 'Generating Tests...' : 'Generate New Test Cases'}
              </button>

              <button
                id="btn-run-tests"
                onClick={handleRunTests}
                disabled={isRunning || isGenerating || testCases.length === 0}
                className="px-5 py-2.5 text-xs font-bold text-white bg-[#365CF5] hover:bg-[#2849D6] shadow-sm rounded-xl transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
                {isRunning ? 'Running Tests...' : 'Run Tests'}
              </button>
            </div>
          </div>
        </div>

        {/* Feedback / Notifications */}
        {cycleRestarted && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 text-xs flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
            <span className="font-medium">
              Full scenario catalogue completed (30/30 tests). Restarting cycle: Round {roundNumber || 2} · Batch {batchNumber || 1}
            </span>
          </div>
        )}

        {feedback && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{feedback}</span>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2 mb-4">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* 3. TEST RESULTS */}
        <div className="space-y-4">
          {/* Top Compact Result with Batch Badge */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="text-xs font-mono font-bold text-slate-700 bg-white px-3.5 py-1.5 rounded-lg border border-slate-200 shadow-2xs">
                {currentRun ? (
                  <span>
                    Total: {currentRun.total_tests} | Passed: {currentRun.passed_tests} | Failed: {currentRun.failed_tests}
                  </span>
                ) : (
                  <span>
                    Total: {testCases.length} | Ready to Run
                  </span>
                )}
              </div>

              {batchNumber && (
                <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-md">
                  {roundNumber && roundNumber > 1 ? `Round ${roundNumber} · ` : ''}Batch {batchNumber} · {testCases.length} test cases
                </span>
              )}
            </div>

            {currentRun && (
              <span className="text-xs font-mono text-slate-400">
                Execution time: {currentRun.duration_ms} ms
              </span>
            )}
          </div>

          {/* Test List Cards */}
          {loadingInitial ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-xs text-slate-500">
              Loading test suite...
            </div>
          ) : displayedItems.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-xs text-slate-500">
              No test cases generated yet. Click "Generate New Test Cases" to generate a batch of 5 test cases.
            </div>
          ) : (
            <div className="space-y-2.5">
              {displayedItems.map((item: any) => {
                const isResult = 'status' in item;
                const isPassed = item.status === 'PASSED';

                return (
                  <div
                    key={item.id}
                    className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs hover:border-slate-300 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      {/* Left: Test Name, Feature, Description */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h2 className="text-sm font-bold text-slate-900">
                            {item.title}
                          </h2>
                          <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                            {item.feature_name}
                          </span>
                        </div>

                        {item.description && (
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {item.description}
                          </p>
                        )}

                        {/* Short Failure Explanation when applicable */}
                        {isResult && !isPassed && item.error_message && (
                          <div className="mt-2.5 p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 font-mono">
                            <span className="font-bold">Failure: </span>
                            {item.error_message}
                          </div>
                        )}
                      </div>

                      {/* Right: Pass or Fail Status */}
                      <div className="shrink-0 pt-0.5">
                        {isResult ? (
                          isPassed ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              Passed
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
                              <XCircle className="w-3.5 h-3.5 text-rose-600" />
                              Failed
                            </span>
                          )
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                            Ready
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
