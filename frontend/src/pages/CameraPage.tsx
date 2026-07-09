import { useEffect, useRef } from "react";

export default function CameraPage() {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error(err);
        alert("Camera access denied");
      }
    }

    startCamera();
  }, []);

  return (
    <div style={{ padding: "40px" }}>
      <h1>Live Camera</h1>

      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{
          width: "800px",
          borderRadius: "12px",
        }}
      />
    </div>
  );
}