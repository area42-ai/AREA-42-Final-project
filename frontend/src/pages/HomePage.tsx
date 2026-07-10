import { useEffect, useRef, useState } from "react";

interface LogEntry {
  time: string;
  type: "info" | "success" | "warning" | "danger";
  message: string;
}

interface Incident {
  incident_id: string;
  status: string;
  start_seconds: number | null;
  end_seconds: number | null;
  duration_seconds: number | null;
  violated_items: string[];
  ppe_status: Record<string, string>;
  confidence: number | null;
}

interface IncidentEnvelope {
  schema_version: string;
  video_id: string;
  source_pipeline: string;
  models: string[];
  analysis_scope: string[];
  incident_detected: boolean;
  incidents: Incident[];
  summary: string;
}

function HomePage() {
  // Live Camera states
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const cameraContainerRef = useRef<HTMLDivElement>(null);

  // Tab switching state
  const [activeTab, setActiveTab] = useState<"upload" | "camera" | "rtsp">("upload");

  const toggleFullscreen = () => {
    const container = cameraContainerRef.current;
    if (!container) return;

    if (!document.fullscreenElement) {
      if (container.requestFullscreen) {
        container.requestFullscreen();
      } else if ((container as any).webkitRequestFullscreen) {
        (container as any).webkitRequestFullscreen();
      } else if ((container as any).msRequestFullscreen) {
        (container as any).msRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  // Video list states
  const [availableVideos, setAvailableVideos] = useState<string[]>([]);
  const [selectedVideoName, setSelectedVideoName] = useState<string>("");

  // Video Upload / Playback states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisLogs, setAnalysisLogs] = useState<LogEntry[]>([]);
  const [apiResult, setApiResult] = useState<IncidentEnvelope | null>(null);
  const [apiMode, setApiMode] = useState<"live" | "simulated" | null>(null);
  
  // Dashboard Metrics
  const [complianceRate, setComplianceRate] = useState<number>(100);
  const [violationsCount, setViolationsCount] = useState<number>(0);
  const [ppeStatus, setPpeStatus] = useState<Record<string, string>>({
    hard_hat: "neutral",
    safety_vest: "neutral",
    boots: "neutral",
    goggles: "neutral",
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load available videos on mount
  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await fetch("/api/videos");
      const data = await response.json();
      if (data.videos) {
        setAvailableVideos(data.videos);
        if (data.videos.length > 0 && !selectedVideoName) {
          handleSelectVideoName(data.videos[0]);
        }
      }
    } catch (err) {
      console.error("Failed to fetch videos:", err);
    }
  };

  useEffect(() => {
    if (cameraOn && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current
        .play()
        .then(() => console.log("Video started"))
        .catch((err) => console.error("Play error:", err));
    }
  }, [cameraOn]);

  // Clean up object URLs and stream on unmount
  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [videoUrl]);

  // Automatically stop camera when switching away from the Camera tab
  useEffect(() => {
    if (activeTab !== "camera" && cameraOn) {
      stopCamera();
    }
  }, [activeTab]);

  // Camera Handlers
  const startCamera = async () => {
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError("This browser does not support camera access.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      streamRef.current = stream;
      setCameraOn(true);
    } catch (err) {
      console.error(err);
      if (err instanceof DOMException) {
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
          setCameraError(
            "Camera permission was denied. Please allow camera access in settings."
          );
        } else if (err.name === "NotFoundError") {
          setCameraError("No camera device was found.");
        } else {
          setCameraError(`Camera access failed: ${err.message}`);
        }
      } else {
        setCameraError("Camera access failed for an unknown reason.");
      }
      setCameraOn(false);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraOn(false);
    setCameraError(null);
  };

  // Upload and Select Handlers
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await uploadAndSelectVideo(file);
    }
  };

  const uploadAndSelectVideo = async (file: File) => {
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }
    setSelectedFile(file);
    setVideoUrl(URL.createObjectURL(file));
    setSelectedVideoName(file.name);
    resetAnalysisState();

    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      if (result.error) {
        console.error("Upload error:", result.error);
      } else {
        fetchVideos();
      }
    } catch (err) {
      console.error("Failed to upload file to backend:", err);
    }
  };

  const handleSelectVideoName = (name: string) => {
    setSelectedVideoName(name);
    setSelectedFile(null);
    setVideoUrl(`/api/videos/${name}`);
    resetAnalysisState();
  };

  const resetAnalysisState = () => {
    setIsAnalyzing(false);
    setAnalysisProgress(0);
    setAnalysisLogs([]);
    setApiResult(null);
    setApiMode(null);
    setComplianceRate(100);
    setViolationsCount(0);
    setPpeStatus({
      hard_hat: "neutral",
      safety_vest: "neutral",
      boots: "neutral",
      goggles: "neutral",
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("video/")) {
        await uploadAndSelectVideo(file);
      } else {
        alert("Please drop a valid video file.");
      }
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const startVideoAnalysis = async () => {
    let nameToAnalyze = selectedVideoName;

    if (!nameToAnalyze) return;

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setApiResult(null);
    setApiMode(null);

    setAnalysisLogs([
      { time: "00:00", type: "info", message: "Connecting to Watch Out API pipeline..." },
      { time: "00:01", type: "info", message: `Targeting: ${nameToAnalyze}` },
    ]);

    setPpeStatus({
      hard_hat: "pending",
      safety_vest: "pending",
      boots: "pending",
      goggles: "pending",
    });

    // Mock progress increments
    let currentProgress = 10;
    const progressInterval = setInterval(() => {
      if (currentProgress < 95) {
        currentProgress += 5;
        setAnalysisProgress(currentProgress);
        
        if (currentProgress === 30) {
          setAnalysisLogs((prev) => [
            ...prev,
            { time: "00:05", type: "info", message: "Extracting frames and prepping visual classification payload..." }
          ]);
        } else if (currentProgress === 60) {
          setAnalysisLogs((prev) => [
            ...prev,
            { time: "00:10", type: "info", message: "Evaluating whole-video safety details via NVIDIA Nemotron model..." }
          ]);
        } else if (currentProgress === 85) {
          setAnalysisLogs((prev) => [
            ...prev,
            { time: "00:15", type: "info", message: "Formatting output JSON against incident compliance schemas..." }
          ]);
        }
      }
    }, 300);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          video_name: nameToAnalyze,
          pipeline: "pipeline_a"
        })
      });
      
      const result = await response.json();
      clearInterval(progressInterval);
      setAnalysisProgress(100);
      setIsAnalyzing(false);

      if (result.error) {
        setAnalysisLogs((prev) => [
          ...prev,
          { time: "Error", type: "danger", message: `Analysis failed: ${result.error}` }
        ]);
        setPpeStatus({
          hard_hat: "neutral",
          safety_vest: "neutral",
          boots: "neutral",
          goggles: "neutral",
        });
        return;
      }

      setApiMode(result.mode);
      const envelope: IncidentEnvelope = result.data;
      setApiResult(envelope);

      const incidents = envelope.incidents || [];
      setViolationsCount(incidents.length);
      
      const activeScope = envelope.analysis_scope || ["hard_hat", "safety_vest", "safety_glasses", "gloves"];
      const violatedItems = new Set<string>();
      incidents.forEach(inc => {
        (inc.violated_items || []).forEach(item => violatedItems.add(item));
      });
      
      const safeCount = activeScope.length - violatedItems.size;
      const rate = Math.round((safeCount / activeScope.length) * 100);
      setComplianceRate(rate);

      const nextPpeStatus: Record<string, string> = {
        hard_hat: "valid",
        safety_vest: "valid",
        boots: "valid",
        goggles: "valid",
      };
      
      violatedItems.forEach(item => {
        if (item === "safety_glasses") {
          nextPpeStatus["goggles"] = "invalid";
        } else {
          nextPpeStatus[item] = "invalid";
        }
      });
      
      setPpeStatus(nextPpeStatus);

      const finalLogs: LogEntry[] = [
        { time: "00:00", type: "info", message: `Analysis Mode: ${result.mode.toUpperCase()}` },
        { time: "00:02", type: "info", message: `Models: ${envelope.models?.join(" + ")}` },
      ];

      incidents.forEach(inc => {
        const itemLabel = (inc.violated_items || []).join(", ");
        const durationText = inc.end_seconds 
          ? `from ${inc.start_seconds}s to ${inc.end_seconds}s` 
          : `starting at ${inc.start_seconds}s (Unresolved)`;
          
        finalLogs.push({
          time: `00:${String(Math.floor(inc.start_seconds || 0)).padStart(2, "0")}`,
          type: "danger",
          message: `Incident Detected: Missing ${itemLabel} ${durationText}`
        });
      });

      if (incidents.length === 0) {
        finalLogs.push({
          time: "00:20",
          type: "success",
          message: "All clear! Full PPE compliance verified across the timeline."
        });
      } else {
        finalLogs.push({
          time: "00:22",
          type: "warning",
          message: `Audit complete. Captured ${incidents.length} compliance violation(s).`
        });
      }

      setAnalysisLogs(finalLogs);

    } catch (err) {
      clearInterval(progressInterval);
      setAnalysisProgress(100);
      setIsAnalyzing(false);
      console.error("API error:", err);
      setAnalysisLogs((prev) => [
        ...prev,
        { time: "Error", type: "danger", message: "API connection failed. Please ensure backend is running." }
      ]);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }
    setVideoUrl(null);
    setSelectedVideoName("");
    resetAnalysisState();
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-orange-500 border-b-4 border-orange-600 px-6 py-4 sticky top-0 z-50 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img
              src="/watch-out-logo.svg"
              alt="Watch Out Logo"
              className="h-10 w-auto brightness-0 invert"
              onError={(e) => {
                e.currentTarget.src = "/watch-out-logo.png";
              }}
            />
            <div className="h-6 w-[1px] bg-orange-300 hidden sm:block"></div>
            <span className="text-orange-100 text-sm font-semibold tracking-wide hidden sm:inline">
              Workplace Safety Monitor
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white rounded-full px-4 py-1 text-xs font-bold text-orange-600 shadow-xs">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              {apiMode === "live" ? "Live NVIDIA Pipeline" : "Interactive Simulation Mode"}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        
        {/* Stats Row */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-2xl border-l-4 border-orange-500 border-y border-r border-slate-150 p-6 shadow-sm flex items-center justify-between hover:shadow-md transition">
            <div>
              <p className="text-slate-400 text-xs font-bold tracking-wider uppercase">Compliance Score</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1">{complianceRate}%</h3>
              <p className={`text-xs font-bold mt-1 ${complianceRate === 100 ? "text-emerald-600" : "text-rose-600"}`}>
                {complianceRate === 100 ? "Perfect compliance" : "Immediate review required"}
              </p>
            </div>
            <div className="bg-orange-100 p-4 rounded-2xl text-orange-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>

          <div className="bg-white rounded-2xl border-l-4 border-orange-500 border-y border-r border-slate-150 p-6 shadow-sm flex items-center justify-between hover:shadow-md transition">
            <div>
              <p className="text-slate-400 text-xs font-bold tracking-wider uppercase">Active Feeds</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1">
                {cameraOn ? "1 Camera" : selectedVideoName ? "1 Video" : "None"}
              </h3>
              <p className="text-slate-500 text-xs mt-1">Source: {cameraOn ? "Webcam" : selectedVideoName ? "File" : "Idle"}</p>
            </div>
            <div className="bg-orange-100 p-4 rounded-2xl text-orange-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
          </div>

          <div className="bg-white rounded-2xl border-l-4 border-orange-500 border-y border-r border-slate-150 p-6 shadow-sm flex items-center justify-between hover:shadow-md transition">
            <div>
              <p className="text-slate-400 text-xs font-bold tracking-wider uppercase">Violations Found</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1">{violationsCount}</h3>
              <p className={`text-xs font-bold mt-1 ${violationsCount > 0 ? "text-rose-600 animate-pulse" : "text-slate-500"}`}>
                {violationsCount > 0 ? "Pipeline warnings active" : "No safety hazards detected"}
              </p>
            </div>
            <div className="bg-orange-100 p-4 rounded-2xl text-orange-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>

          <div className="bg-white rounded-2xl border-l-4 border-orange-500 border-y border-r border-slate-150 p-6 shadow-sm flex items-center justify-between hover:shadow-md transition">
            <div>
              <p className="text-slate-400 text-xs font-bold tracking-wider uppercase">API Connection</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1">Connected</h3>
              <p className="text-slate-500 text-xs mt-1">Backend: http://localhost:8000</p>
            </div>
            <div className="bg-orange-100 p-4 rounded-2xl text-orange-600">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </section>

        {/* Dashboard Tabs & Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Video Workspace (Webcam, Upload, RTSP) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Tab selector */}
            <div className="bg-white rounded-2xl border border-slate-100 p-1.5 shadow-xs flex gap-1">
              <button
                id="tab-upload"
                onClick={() => setActiveTab("upload")}
                className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer ${
                  activeTab === "upload"
                    ? "bg-orange-500 text-white shadow-xs"
                    : "text-slate-600 hover:bg-orange-50"
                }`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Video
              </button>

              <button
                id="tab-camera"
                onClick={() => setActiveTab("camera")}
                className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer ${
                  activeTab === "camera"
                    ? "bg-orange-500 text-white shadow-xs"
                    : "text-slate-600 hover:bg-orange-50"
                }`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Live Camera
              </button>

              <button
                id="tab-rtsp"
                onClick={() => setActiveTab("rtsp")}
                className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer ${
                  activeTab === "rtsp"
                    ? "bg-orange-500 text-white shadow-xs"
                    : "text-slate-600 hover:bg-orange-50"
                }`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
                </svg>
                RTSP IP Stream
              </button>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-3xl border border-slate-150 p-6 sm:p-8 shadow-sm">
              
              {/* UPLOAD TAB */}
              {activeTab === "upload" && (
                <div className="space-y-6">
                  
                  {availableVideos.length > 0 && (
                    <div className="bg-orange-50/20 border border-orange-100 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                      <div className="text-sm font-semibold text-slate-700">
                        Select video from available test files:
                      </div>
                      <select
                        id="video-select-dropdown"
                        value={selectedVideoName}
                        onChange={(e) => handleSelectVideoName(e.target.value)}
                        className="bg-white border border-slate-250 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-orange-500 w-full sm:w-64"
                      >
                        <option value="">-- Choose video file --</option>
                        {availableVideos.map((video) => (
                          <option key={video} value={video}>
                            {video}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {!selectedVideoName ? (
                    // Drag and Drop Zone
                    <div
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-orange-350 hover:border-orange-500 rounded-2xl bg-orange-50/5 hover:bg-orange-50/15 p-12 text-center transition cursor-pointer flex flex-col items-center justify-center group"
                    >
                      <input
                        ref={fileInputRef}
                        id="file-input-upload"
                        type="file"
                        accept="video/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <div className="bg-orange-50 text-orange-500 p-5 rounded-2xl mb-4 group-hover:scale-110 transition duration-300">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <h4 className="text-lg font-extrabold text-slate-800">
                        Upload Video Footage for safety auditing
                      </h4>
                      <p className="text-slate-400 text-sm mt-2 max-w-sm mx-auto">
                        Drag and drop your MP4, WebM or other video clip here, or click to browse local folders.
                      </p>
                    </div>
                  ) : (
                    // File Preview & Controller
                    <div className="space-y-6">
                      <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <div className="bg-orange-100 text-orange-600 p-3 rounded-xl">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                            </svg>
                          </div>
                          <div>
                            <h5 className="font-semibold text-slate-800 text-sm truncate max-w-[250px] sm:max-w-[400px]">
                              {selectedVideoName}
                            </h5>
                            {selectedFile && (
                              <p className="text-xs text-slate-400 mt-0.5">
                                {formatBytes(selectedFile.size)}
                              </p>
                            )}
                          </div>
                        </div>

                        <button
                          id="btn-reset-upload"
                          onClick={resetUpload}
                          className="text-slate-400 hover:text-rose-500 p-2 rounded-lg hover:bg-rose-50 transition cursor-pointer"
                          title="Remove video file"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>

                      {/* Video Player */}
                      {videoUrl && selectedFile && (
                        <div className="relative rounded-2xl overflow-hidden border border-slate-100 shadow-sm bg-black aspect-video flex items-center justify-center">
                          <video
                            src={videoUrl}
                            controls
                            className="w-full h-full object-contain"
                          />
                        </div>
                      )}

                      {/* Analysis Controls */}
                      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                        {!isAnalyzing && analysisProgress === 0 ? (
                          <button
                            id="btn-trigger-analysis"
                            onClick={startVideoAnalysis}
                            className="w-full sm:w-auto bg-orange-500 hover:bg-orange-600 text-white font-bold px-8 py-3.5 rounded-xl shadow-xs hover:shadow-orange-500/20 transition flex items-center justify-center gap-2 cursor-pointer"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Run AI safety audit
                          </button>
                        ) : (
                          <div className="w-full space-y-2">
                            <div className="flex justify-between items-center text-sm font-semibold text-slate-700">
                              <span>Analyzing frames & tracking personnel...</span>
                              <span>{analysisProgress}%</span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-orange-500 h-full transition-all duration-300 rounded-full"
                                style={{ width: `${Math.min(analysisProgress, 100)}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* LIVE CAMERA TAB */}
              {activeTab === "camera" && (
                <div className="space-y-6">
                  <div className="flex flex-col items-center justify-center">
                    {!cameraOn ? (
                      <div className="text-center py-8">
                        <div className="bg-orange-50 text-orange-500 p-6 rounded-3xl inline-block mb-4">
                          <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <h4 className="text-lg font-extrabold text-slate-800">Direct Camera Audit</h4>
                        <p className="text-slate-400 text-sm mt-2 max-w-sm mx-auto mb-6">
                          Allow local camera feeds to record video and test NVIDIA inference parameters in real-time.
                        </p>
                        <button
                          id="btn-start-camera"
                          onClick={startCamera}
                          className="bg-orange-500 hover:bg-orange-600 text-white font-bold px-8 py-3.5 rounded-xl shadow-xs transition cursor-pointer"
                        >
                          Start Live Camera
                        </button>
                      </div>
                    ) : (
                      <div className="w-full space-y-6">
                        <div
                          ref={cameraContainerRef}
                          className="relative rounded-2xl overflow-hidden border border-slate-100 bg-black aspect-video flex items-center justify-center"
                        >
                          <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover"
                          />
                          
                          {/* Live Badge Overlay */}
                          <div className="absolute top-4 left-4 flex gap-2">
                            <div className="bg-emerald-500/90 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5 backdrop-blur-xs">
                              <span className="h-2.5 w-2.5 bg-white rounded-full animate-ping"></span>
                              Live Stream
                            </div>
                          </div>

                          {/* Fullscreen Button */}
                          <button
                            id="btn-fullscreen-camera"
                            onClick={toggleFullscreen}
                            className="absolute top-4 right-4 bg-black/60 hover:bg-black/80 text-white p-2.5 rounded-xl backdrop-blur-xs transition cursor-pointer"
                            title="Toggle Fullscreen"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {cameraError && (
                    <div className="rounded-xl border border-rose-100 bg-rose-50 p-4 text-sm text-rose-800">
                      {cameraError}
                    </div>
                  )}
                </div>
              )}

              {/* RTSP STREAM TAB */}
              {activeTab === "rtsp" && (
                <div className="text-center py-12 space-y-4">
                  <div className="bg-orange-50 text-orange-500 p-6 rounded-3xl inline-block">
                    <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 100-6 3 3 0 000 6z" />
                    </svg>
                  </div>
                  <h4 className="text-xl font-extrabold text-slate-800">RTSP Stream Integration</h4>
                  <p className="text-slate-400 text-sm max-w-md mx-auto">
                    Direct RTSP network streaming from IP cameras. This pipeline is currently planned for MVP stage 2.
                  </p>
                  <div className="pt-4">
                    <span className="bg-orange-50 text-orange-600 text-xs font-semibold px-4 py-2 rounded-full border border-orange-100">
                      Coming Soon - Pipeline TBD
                    </span>
                  </div>
                </div>
              )}

            </div>

            {/* Model Summary Text (only visible after analysis) */}
            {apiResult && apiResult.summary && (
              <div className="bg-white rounded-3xl border border-slate-150 p-6 shadow-sm space-y-3">
                <h4 className="font-bold text-slate-800 text-lg flex items-center gap-2">
                  <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  AI Executive Summary
                </h4>
                <p className="text-sm text-slate-600 leading-relaxed font-sans bg-slate-50 p-4 rounded-xl border border-slate-100">
                  {apiResult.summary}
                </p>
              </div>
            )}
          </div>

          {/* Right Column: AI Console & Incident Feed */}
          <div className="space-y-6">
            
            {/* Real-time Status Card */}
            <div className="bg-white rounded-3xl border border-slate-150 p-6 shadow-sm">
              <h4 className="font-bold text-slate-800 text-lg mb-4 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-orange-500"></span>
                PPE Compliance Matrix
              </h4>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
                  <span className="text-2xl">🪖</span>
                  <p className="text-xs text-slate-400 font-semibold mt-2 uppercase tracking-wide">Helmet</p>
                  <div className="mt-2 flex justify-center">
                    {ppeStatus.hard_hat === "neutral" && (
                      <span className="text-xs text-slate-400 font-medium">Not Tested</span>
                    )}
                    {ppeStatus.hard_hat === "pending" && (
                      <span className="text-xs text-amber-500 font-medium animate-pulse">Checking...</span>
                    )}
                    {ppeStatus.hard_hat === "valid" && (
                      <span className="text-xs text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">Safe</span>
                    )}
                    {ppeStatus.hard_hat === "invalid" && (
                      <span className="text-xs text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded-full">Missing!</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
                  <span className="text-2xl">🦺</span>
                  <p className="text-xs text-slate-400 font-semibold mt-2 uppercase tracking-wide">Safety Vest</p>
                  <div className="mt-2 flex justify-center">
                    {ppeStatus.safety_vest === "neutral" && (
                      <span className="text-xs text-slate-400 font-medium">Not Tested</span>
                    )}
                    {ppeStatus.safety_vest === "pending" && (
                      <span className="text-xs text-amber-500 font-medium animate-pulse">Checking...</span>
                    )}
                    {ppeStatus.safety_vest === "valid" && (
                      <span className="text-xs text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">Safe</span>
                    )}
                    {ppeStatus.safety_vest === "invalid" && (
                      <span className="text-xs text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded-full">Missing!</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
                  <span className="text-2xl">🥾</span>
                  <p className="text-xs text-slate-400 font-semibold mt-2 uppercase tracking-wide">Work Boots</p>
                  <div className="mt-2 flex justify-center">
                    {ppeStatus.boots === "neutral" && (
                      <span className="text-xs text-slate-400 font-medium">Not Tested</span>
                    )}
                    {ppeStatus.boots === "pending" && (
                      <span className="text-xs text-amber-500 font-medium animate-pulse">Checking...</span>
                    )}
                    {ppeStatus.boots === "valid" && (
                      <span className="text-xs text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">Safe</span>
                    )}
                    {ppeStatus.boots === "invalid" && (
                      <span className="text-xs text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded-full">Missing!</span>
                    )}
                  </div>
                </div>

                <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
                  <span className="text-2xl">🥽</span>
                  <p className="text-xs text-slate-400 font-semibold mt-2 uppercase tracking-wide">Goggles</p>
                  <div className="mt-2 flex justify-center">
                    {ppeStatus.goggles === "neutral" && (
                      <span className="text-xs text-slate-400 font-medium">Not Tested</span>
                    )}
                    {ppeStatus.goggles === "pending" && (
                      <span className="text-xs text-amber-500 font-medium animate-pulse">Checking...</span>
                    )}
                    {ppeStatus.goggles === "valid" && (
                      <span className="text-xs text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full">Safe</span>
                    )}
                    {ppeStatus.goggles === "invalid" && (
                      <span className="text-xs text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded-full">Missing!</span>
                    )}
                  </div>
                </div>
              </div>

              {apiResult && (
                <div className="mt-6 border-t border-slate-100 pt-6 text-center">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Audit Result Score</p>
                  <div className="text-4xl font-extrabold text-slate-900 mt-2">{complianceRate}%</div>
                  <p className={`text-xs font-semibold mt-1.5 ${complianceRate === 100 ? "text-emerald-600" : "text-rose-600"}`}>
                    {complianceRate === 100 ? "No violations detected" : `${violationsCount} violations captured`}
                  </p>
                </div>
              )}
            </div>

            {/* AI Console Feed */}
            <div className="bg-white rounded-3xl border border-slate-150 p-6 shadow-sm flex flex-col h-[380px]">
              <div className="flex items-center justify-between border-b border-slate-50 pb-4 mb-4">
                <h4 className="font-bold text-slate-800 text-lg flex items-center gap-2">
                  <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Real-time Detections
                </h4>
                {isAnalyzing && (
                  <span className="flex h-2.5 w-2.5 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-orange-500"></span>
                  </span>
                )}
              </div>

              <div className="flex-1 overflow-y-auto space-y-3 pr-2 text-xs font-mono">
                {analysisLogs.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center space-y-2">
                    <svg className="w-8 h-8 opacity-40 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="max-w-[200px]">No active feed. Load a video file and start the safety audit.</p>
                  </div>
                ) : (
                  analysisLogs.map((log, index) => (
                    <div
                      key={index}
                      className={`p-2.5 rounded-lg border flex items-start gap-2.5 leading-relaxed transition-all duration-200 ${
                        log.type === "success"
                          ? "bg-emerald-50/50 border-emerald-100 text-emerald-800"
                          : log.type === "warning"
                          ? "bg-amber-50/50 border-amber-100 text-amber-800"
                          : log.type === "danger"
                          ? "bg-rose-50/50 border-rose-100 text-rose-800"
                          : "bg-slate-50/50 border-slate-100 text-slate-600"
                      }`}
                    >
                      <span className="opacity-60 select-none">[{log.time}]</span>
                      <span className="flex-1 truncate-2-lines">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>

        </div>

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-100 py-6 text-center text-xs text-slate-400 mt-auto">
        <p>© 2026 Watch Out - Developed by AREA-42. Powered by NVIDIA vision models (TBD).</p>
      </footer>
    </div>
  );
}

export default HomePage;