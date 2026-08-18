/**
 * Analysis lifecycle for a single-response /api/pipeline call.
 * Progress stages are UI-only; prediction values come only from the API.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { askRag, fetchLiveNews, fetchSampleNews, isAuthError, runPipeline } from "../api";
import { USE_MOCK, MOCK_RESULT } from "../mock";
import {
  buildAnalysisDashboard,
  clearSessionHistory,
  loadSessionHistory,
  saveSessionHistory,
} from "../utils/dashboardMapper";

export const ANALYSIS_STATES = [
  "idle",
  "starting",
  "demand_running",
  "demand_complete",
  "price_running",
  "price_complete",
  "logistics_running",
  "logistics_complete",
  "container_running",
  "container_complete",
  "supervisor_running",
  "completed",
  "failed",
];

const RUNNING_SEQUENCE = [
  { status: "starting", progress: 5, agent: "Preparing pipeline", stage: null },
  { status: "demand_running", progress: 12, agent: "Demand Agent", stage: "demand" },
  { status: "price_running", progress: 28, agent: "Price Agent", stage: "price" },
  { status: "logistics_running", progress: 44, agent: "Logistics Agent", stage: "logistics" },
  { status: "container_running", progress: 60, agent: "Container Agent", stage: "container" },
  { status: "supervisor_running", progress: 76, agent: "Supervisor Agent", stage: "supervisor" },
];

const REVEAL_SEQUENCE = [
  { status: "demand_complete", progress: 20, agent: "Demand Agent", reveal: "demand", stage: "demand" },
  { status: "price_complete", progress: 40, agent: "Price Agent", reveal: "price", stage: "price" },
  {
    status: "logistics_complete",
    progress: 60,
    agent: "Logistics Agent",
    reveal: "logistics",
    stage: "logistics",
  },
  {
    status: "container_complete",
    progress: 80,
    agent: "Container Agent",
    reveal: "container",
    stage: "container",
  },
  {
    status: "completed",
    progress: 100,
    agent: "Supervisor Agent",
    reveal: "supervisor",
    stage: "supervisor",
  },
];

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export function useAnalysis({ onAuthExpired } = {}) {
  const [analysisStatus, setAnalysisStatus] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [activeAgent, setActiveAgent] = useState(null);
  const [activeStage, setActiveStage] = useState(null);
  const [revealed, setRevealed] = useState({
    demand: false,
    price: false,
    logistics: false,
    container: false,
    supervisor: false,
  });
  const [activity, setActivity] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [rawResult, setRawResult] = useState(null);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);
  const [sessionMeta, setSessionMeta] = useState(null);

  const [demandNews, setDemandNews] = useState("");
  const [priceNews, setPriceNews] = useState("");
  const [containers, setContainers] = useState(6);
  const [containerType, setContainerType] = useState("20FT");

  const [question, setQuestion] = useState("What documents are needed to export onions from India?");
  const [rag, setRag] = useState(null);
  const [ragMessages, setRagMessages] = useState([]);
  const [lastAsked, setLastAsked] = useState("");
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState("");

  const [newsLoading, setNewsLoading] = useState(false);

  const cancelRef = useRef(0);
  const runningPulseRef = useRef(null);

  const pushActivity = useCallback((item) => {
    setActivity((prev) => [
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        at: new Date().toISOString(),
        ...item,
      },
      ...prev,
    ].slice(0, 40));
  }, []);

  const restoreSession = useCallback(() => {
    const hist = loadSessionHistory();
    if (!hist?.dashboard) return false;
    setDashboard(hist.dashboard);
    setRawResult(hist.dashboard.raw || null);
    setSessionMeta({ savedAt: hist.savedAt, label: "Recent browser session" });
    setAnalysisStatus("completed");
    setProgress(100);
    setRevealed({
      demand: true,
      price: true,
      logistics: true,
      container: true,
      supervisor: true,
    });
    setActiveAgent(null);
    setActiveStage(null);
    return true;
  }, []);

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  const clearDashboard = useCallback(() => {
    clearSessionHistory();
    setDashboard(null);
    setRawResult(null);
    setSessionMeta(null);
    setActivity([]);
    setAnalysisStatus("idle");
    setProgress(0);
    setRevealed({
      demand: false,
      price: false,
      logistics: false,
      container: false,
      supervisor: false,
    });
    setActiveAgent(null);
    setActiveStage(null);
    setError("");
  }, []);

  const loadSamples = useCallback(async () => {
    setError("");
    if (USE_MOCK) {
      setDemandNews(
        "Saudi Arabia onion shortage after delayed shipments; traders seek Indian supply.\n\nUAE rice importers increase basmati enquiry.\n\nJapan maize feed mills raise import tenders."
      );
      setPriceNews(
        "Nashik onion mandi firming on lower stocks. Punjab rice auctions steady. Karnataka maize arrivals soft."
      );
      return;
    }
    try {
      const data = await fetchSampleNews();
      setDemandNews(data.demand_news || "");
      setPriceNews(data.price_news || "");
    } catch (e) {
      setError(e.message || "Failed to load samples");
    }
  }, []);

  /** News Agent — pull live headlines from GDELT / Google News / NewsAPI */
  const loadLiveNews = useCallback(async () => {
    setError("");
    setToast(null);
    if (USE_MOCK) {
      await loadSamples();
      return;
    }
    setNewsLoading(true);
    try {
      const data = await fetchLiveNews();
      setDemandNews(data.demand_news || "");
      setPriceNews(data.price_news || "");
      setToast({
        type: "success",
        message: `Live news updated — Demand: ${data.demand_count || 0} · India price: ${data.price_count || 0}`,
      });
    } catch (e) {
      const msg = e.message || "Failed to fetch live news";
      setError(msg);
      setToast({ type: "error", message: msg });
      if (isAuthError(e) && typeof onAuthExpired === "function") {
        onAuthExpired(msg);
      }
    } finally {
      setNewsLoading(false);
    }
  }, [loadSamples, onAuthExpired]);

  const runAnalysis = useCallback(async () => {
    const token = ++cancelRef.current;
    setError("");
    setToast(null);
    setAnalysisStatus("starting");
    setProgress(5);
    setActiveAgent("News Agent — fetching live headlines");
    setActiveStage(null);
    setRevealed({
      demand: false,
      price: false,
      logistics: false,
      container: false,
      supervisor: false,
    });
    pushActivity({
      title: "Analysis started",
      description: "News Agent → Demand → Price → Logistics → Containers → Groq Explain",
      status: "running",
      icon: "play",
    });

    let pulseIdx = 0;
    runningPulseRef.current = setInterval(() => {
      if (token !== cancelRef.current) return;
      pulseIdx = (pulseIdx + 1) % RUNNING_SEQUENCE.length;
      const step = RUNNING_SEQUENCE[pulseIdx];
      setAnalysisStatus(step.status);
      setProgress(step.progress);
      setActiveAgent(step.agent);
      setActiveStage(step.stage);
    }, 1400);

    try {
      let data;
      if (USE_MOCK) {
        await sleep(1800);
        data = {
          ...MOCK_RESULT,
          generated_at: new Date().toISOString(),
          inputs: {
            available_containers: Number(containers),
            container_type: containerType,
            top_n: 3,
          },
        };
      } else {
        // auto_news=true → backend News Agent fetches verified live news
        data = await runPipeline({
          demand_news: demandNews,
          price_news: priceNews,
          available_containers: Number(containers),
          container_type: containerType,
          top_n: 3,
          auto_news: true,
        });
        if (data.error) throw new Error(data.error);
        // Show the live news the agents actually used
        if (data.news_fetch?.demand_news) setDemandNews(data.news_fetch.demand_news);
        if (data.news_fetch?.price_news) setPriceNews(data.news_fetch.price_news);
      }

      if (token !== cancelRef.current) return;

      if (runningPulseRef.current) {
        clearInterval(runningPulseRef.current);
        runningPulseRef.current = null;
      }

      const mapped = buildAnalysisDashboard(data);
      setRawResult(data);
      setDashboard(mapped);
      saveSessionHistory(mapped);
      setSessionMeta({
        savedAt: new Date().toISOString(),
        label: "Recent browser session",
      });

      // Staged visual reveal after real response — no invented values
      for (const step of REVEAL_SEQUENCE) {
        if (token !== cancelRef.current) return;
        setAnalysisStatus(step.status);
        setProgress(step.progress);
        setActiveAgent(step.agent);
        setActiveStage(step.stage);
        setRevealed((prev) => ({ ...prev, [step.reveal]: true }));
        pushActivity({
          title: `${step.agent} completed`,
          description:
            step.reveal === "supervisor"
              ? mapped?.supervisorRecommendation?.summary || "Final recommendation ready"
              : `Stage results available for ${step.reveal}`,
          status: "complete",
          icon: step.reveal,
        });
        await sleep(420);
      }

      setToast({ type: "success", message: "Export analysis complete" });
      setActiveAgent(null);
      setActiveStage(null);
    } catch (e) {
      if (runningPulseRef.current) {
        clearInterval(runningPulseRef.current);
        runningPulseRef.current = null;
      }
      if (token !== cancelRef.current) return;
      setAnalysisStatus("failed");
      setError(e.message || "Analysis failed");
      setToast({ type: "error", message: e.message || "Analysis failed" });
      pushActivity({
        title: "Analysis failed",
        description: e.message || "Pipeline error",
        status: "error",
        icon: "error",
      });
      if (isAuthError(e) && typeof onAuthExpired === "function") {
        onAuthExpired(e.message || "Please login first");
      }
    }
  }, [containers, containerType, demandNews, priceNews, pushActivity, onAuthExpired]);

  const onAsk = useCallback(async () => {
    const q = question.trim();
    if (!q) return;
    setRagLoading(true);
    setRagError("");
    setLastAsked(q);
    setRagMessages((messages) => [
      ...messages,
      { id: `${Date.now()}-user`, role: "user", content: q },
    ]);
    try {
      if (USE_MOCK) {
        await sleep(500);
        const response = {
          answer:
            "To export onions from India you typically need an IEC, APEDA registration where applicable, a phytosanitary certificate, commercial invoice, packing list, bill of lading, and destination-specific import permits.",
          sources: [{ title: "IEC basics", score: 0.91 }],
          used_llm: true,
        };
        setRag(response);
        setRagMessages((messages) => [
          ...messages,
          { id: `${Date.now()}-assistant`, role: "assistant", content: response.answer, sources: response.sources },
        ]);
      } else {
        const response = await askRag(q);
        setRag(response);
        setRagMessages((messages) => [
          ...messages,
          {
            id: `${Date.now()}-assistant`,
            role: "assistant",
            content: response.answer || "Not available",
            sources: response.sources || [],
          },
        ]);
      }
      pushActivity({
        title: "RAG query answered",
        description: q.slice(0, 80),
        status: "complete",
        icon: "rag",
      });
    } catch (e) {
      setRagError(e.message || "RAG request failed");
      if (isAuthError(e) && typeof onAuthExpired === "function") {
        onAuthExpired(e.message || "Please login first");
      }
    } finally {
      setRagLoading(false);
    }
  }, [question, pushActivity, onAuthExpired]);

  const clearRag = useCallback(() => {
    setRag(null);
    setLastAsked("");
    setRagError("");
    setRagMessages([]);
  }, []);

  const isRunning =
    analysisStatus !== "idle" &&
    analysisStatus !== "completed" &&
    analysisStatus !== "failed";

  return {
    analysisStatus,
    progress,
    activeAgent,
    activeStage,
    revealed,
    activity,
    dashboard,
    rawResult,
    error,
    toast,
    setToast,
    sessionMeta,
    demandNews,
    setDemandNews,
    priceNews,
    setPriceNews,
    containers,
    setContainers,
    containerType,
    setContainerType,
    question,
    setQuestion,
    rag,
    ragMessages,
    lastAsked,
    ragLoading,
    ragError,
    isRunning,
    runAnalysis,
    loadSamples,
    loadLiveNews,
    newsLoading,
    onAsk,
    clearRag,
    restoreSession,
    clearDashboard,
  };
}
