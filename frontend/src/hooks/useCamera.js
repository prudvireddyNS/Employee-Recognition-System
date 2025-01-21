// src/hooks/useCamera.js
import { useRef, useEffect } from 'react';

const useCamera = (videoRef, active) => {
  const streamRef = useRef(null);

  useEffect(() => {
    const startCamera = async () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing the camera:", err);
      }
    };

    const stopCamera = () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    };

    if (active) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => stopCamera();
  }, [active]);
};

export default useCamera;
