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

        if (err instanceof DOMException) {
          if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            setErrorMessage(
              "Camera permission was denied. Please allow camera access for this site in your browser settings and try again."
            );
          } else if (err.name === "NotFoundError") {
            setErrorMessage("No camera was found. Connect a camera and try again.");
          } else {
            setErrorMessage(`Camera access failed: ${err.message}`);
          }
        } else {
          setErrorMessage("Camera access was denied.");
        }
      }
    }

    startCamera();
  }, []);

  return (
    <div style={{ padding: "40px" }}>
      <h1>Live Camera</h1>

      {errorMessage && (
        <p style={{ color: "#fca5a5", marginBottom: "16px" }}>{errorMessage}</p>
      )}

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