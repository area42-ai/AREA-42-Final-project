import { useEffect, useRef, useState } from "react";

function HomePage() {
  const [cameraOn, setCameraOn] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (cameraOn && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;

      videoRef.current
        .play()
        .then(() => console.log("Video started"))
        .catch((err) => console.error("Play error:", err));
    }
  }, [cameraOn]);

  const startCamera = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(
        (device) => device.kind === "videoinput"
      );

      console.log("Available cameras:");
      console.table(videoDevices);

      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });

      console.log("Stream:", stream);
      console.log("Video tracks:", stream.getVideoTracks());

      streamRef.current = stream;

      // Video useEffect-də qoşulacaq
      setCameraOn(true);
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        alert(`${err.name}: ${err.message}`);
      } else {
        alert("Unknown error");
      }
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());

    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOn(false);
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    ctx.drawImage(video, 0, 0);

    console.log("Frame captured");
  };

  const analyzeFrame = () => {
    if (!canvasRef.current) return;

    const image = canvasRef.current.toDataURL("image/jpeg");

    console.log(image);

    alert("Frame ready to send to backend.");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
      <div className="w-full max-w-5xl p-10">

        <h1 className="text-5xl font-bold text-center">
          Watch Out
        </h1>

        <p className="text-center text-slate-400 mt-4 text-xl">
          AI Workplace Safety Monitoring
        </p>

        <div className="grid md:grid-cols-3 gap-6 mt-14">

          {/* Camera Card */}
          <div className="bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-800">
            <div className="text-5xl">📹</div>

            <h2 className="text-2xl font-semibold mt-6">
              Live Camera
            </h2>

            <p className="text-slate-400 mt-3">
              Connect your webcam or USB camera for live monitoring.
            </p>

            {!cameraOn ? (
              <button
                onClick={startCamera}
                className="mt-8 w-full rounded-xl bg-blue-600 hover:bg-blue-700 py-3"
              >
                Start Camera
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="mt-8 w-full rounded-xl bg-red-600 hover:bg-red-700 py-3"
              >
                Stop Camera
              </button>
            )}
          </div>

          {/* Upload Card */}
          <div className="bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-800">
            <div className="text-5xl">🎥</div>

            <h2 className="text-2xl font-semibold mt-6">
              Upload Video
            </h2>

            <p className="text-slate-400 mt-3">
              Upload recorded workplace footage for analysis.
            </p>

            <button className="mt-8 w-full rounded-xl bg-green-600 hover:bg-green-700 py-3">
              Upload
            </button>
          </div>

          {/* RTSP Card */}
          <div className="bg-slate-900 rounded-2xl p-8 shadow-lg border border-slate-800 opacity-70">
            <div className="text-5xl">📡</div>

            <h2 className="text-2xl font-semibold mt-6">
              RTSP Camera
            </h2>

            <p className="text-slate-400 mt-3">
              Future IP camera integration.
            </p>

            <button
              disabled
              className="mt-8 w-full rounded-xl bg-gray-700 py-3"
            >
              Coming Soon
            </button>
          </div>

        </div>

        {cameraOn && (
          <div className="mt-12 bg-slate-900 rounded-2xl p-6 border border-slate-800">
            <h2 className="text-2xl font-semibold mb-6">
              Live Camera
            </h2>

            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full rounded-xl"
            />

            <div className="flex gap-4 mt-6">
              <button
                onClick={captureFrame}
                className="bg-yellow-500 hover:bg-yellow-600 px-6 py-3 rounded-xl"
              >
                📸 Capture Frame
              </button>

              <button
                onClick={analyzeFrame}
                className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-xl"
              >
                🤖 Analyze
              </button>
            </div>

            <canvas
              ref={canvasRef}
              className="mt-6 w-full rounded-xl border border-slate-700"
            />
          </div>
        )}

      </div>
    </div>
  );
}

export default HomePage;