import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Camera, RefreshCw } from 'lucide-react';

const CameraFeed = ({ active, onFaceDetected, captureMode = false }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectFrameRef = useRef(null);
  const [error, setError] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const startCamera = useCallback(async () => {
    try {
      setIsLoading(true);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      const constraints = {
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        
        await new Promise((resolve) => {
          videoRef.current.onloadeddata = resolve;
        });
        
        if (canvasRef.current) {
          canvasRef.current.width = videoRef.current.videoWidth;
          canvasRef.current.height = videoRef.current.videoHeight;
        }
      }
      
      setError(null);
      return true;
    } catch (err) {
      setError(err.message || 'Failed to access camera');
      console.error('Camera error:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const detectFaces = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || !active) return;

    try {
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      const imageData = canvas.toDataURL('image/jpeg', 0.8);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/detect-faces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData.split(',')[1] }),
      });

      const data = await response.json();

      if (data.success) {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        
        if (data.faces.length > 0) {
          context.strokeStyle = '#00ff00';
          context.lineWidth = 2;

          data.faces.forEach(face => {
            context.strokeRect(face.left, face.top, face.right - face.left, face.bottom - face.top);
          });

          setFaceDetected(true);
          
          // If not in capture mode, trigger face recognition
          if (!captureMode) {
            onFaceDetected(imageData);
          }
        } else {
          setFaceDetected(false);
        }
      }

      // Continue detection if active
      if (active) {
        detectFrameRef.current = requestAnimationFrame(detectFaces);
      }
    } catch (err) {
      console.error('Face detection error:', err);
      setFaceDetected(false);
      if (active) {
        detectFrameRef.current = requestAnimationFrame(detectFaces);
      }
    }
  }, [active, captureMode, onFaceDetected]);

  const handleCapture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !faceDetected) return;

    try {
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      const imageData = canvas.toDataURL('image/jpeg', 1.0);
      onFaceDetected(imageData);
    } catch (err) {
      console.error('Capture error:', err);
    }
  }, [onFaceDetected, faceDetected]);

  useEffect(() => {
    if (active) {
      startCamera().then(success => {
        if (success) detectFaces();
      });
    }
    return () => {
      if (detectFrameRef.current) {
        cancelAnimationFrame(detectFrameRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [active, startCamera, detectFaces]);

  return (
    <div className="relative w-full aspect-video bg-slate-950 rounded-lg overflow-hidden">
      {(isLoading || error) && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 text-white z-10">
          <p className="text-center">
            {isLoading ? 'Initializing camera...' : error}
          </p>
        </div>
      )}
      
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover"
        style={{ transform: 'scaleX(-1)' }}
      />
      
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full object-cover"
        style={{ transform: 'scaleX(-1)' }}
      />

      <div className="absolute bottom-4 right-4 flex gap-2">
        {captureMode && faceDetected && (
          <button
            onClick={handleCapture}
            className="p-2 bg-green-600 hover:bg-green-700 text-white rounded-full transition-colors"
            title="Capture photo"
          >
            <Camera className="h-5 w-5" />
          </button>
        )}
        <button
          onClick={() => startCamera()}
          className="p-2 bg-slate-800/80 hover:bg-slate-700/80 text-white rounded-full transition-colors"
          title="Restart camera"
          disabled={isLoading}
        >
          <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {faceDetected && (
        <div className="absolute top-4 left-4 px-3 py-1.5 bg-green-500/20 backdrop-blur-sm rounded-lg border border-green-500 text-green-600 text-sm">
          {captureMode ? 'Face Detected - Ready to Capture' : 'Face Detected'}
        </div>
      )}
    </div>
  );
};

export default CameraFeed;
