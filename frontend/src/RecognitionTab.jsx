// src/components/RecognitionTab.jsx
import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { UserCheck, UserX } from 'lucide-react';
import CameraFeed from './CameraFeed';
import RecentActivity from './RecentActivity';

const RECOGNITION_COOLDOWN = 10 * 60 * 1000; // 10 minutes in milliseconds

const RecognitionTab = () => {
  const [recognizedPerson, setRecognizedPerson] = useState(null);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [processing, setProcessing] = useState(false);
  const recognitionTimeoutRef = useRef(null);
  const lastRecognitionTime = useRef(0);
  const recognizedUsers = useRef(new Map()); // Track last recognition time for each user

  const handleFaceDetected = useCallback(async (imageDataUrl) => {
    const now = Date.now();
    // Prevent recognition more often than every 2 seconds
    if (processing || now - lastRecognitionTime.current < 2000) return;

    try {
      setProcessing(true);
      lastRecognitionTime.current = now;

      // Clear previous recognition timeout
      if (recognitionTimeoutRef.current) {
        clearTimeout(recognitionTimeoutRef.current);
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/recognize-face`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          image: imageDataUrl.split(',')[1] 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Recognition failed');
      }

      if (data.success) {
        const userId = data.id; // Ensure backend returns user ID
        const lastRecognition = recognizedUsers.current.get(userId) || 0;
        
        if (now - lastRecognition >= RECOGNITION_COOLDOWN) {
          // Update last recognition time
          recognizedUsers.current.set(userId, now);
          
          setRecognizedPerson(data);
          setStatus({
            type: 'success',
            message: `Welcome, ${data.name}!${data.message ? ` ${data.message}` : ''}`
          });

          // Reset after 5 seconds
          recognitionTimeoutRef.current = setTimeout(() => {
            setRecognizedPerson(null);
            setStatus({ type: '', message: '' });
          }, 5000);
        } else {
          // User recognized but within cooldown period
          const minutesRemaining = Math.ceil((RECOGNITION_COOLDOWN - (now - lastRecognition)) / 60000);
          setStatus({
            type: 'info',
            message: `Already logged. Please try again in ${minutesRemaining} minutes.`
          });
        }
      } else {
        setStatus({
          type: 'error',
          message: data.message || 'Face not recognized'
        });
      }
    } catch (error) {
      console.error('Recognition error:', error);
      setStatus({
        type: 'error',
        message: error.message
      });
    } finally {
      setProcessing(false);
    }
  }, [processing]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Face Recognition</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="relative">
          <CameraFeed 
            active={true} 
            onFaceDetected={handleFaceDetected}
            captureMode={false}
          />
          
          {recognizedPerson && (
            <div className="absolute top-4 left-4 right-4 p-4 bg-green-500/20 backdrop-blur-sm rounded-lg border border-green-500">
              <div className="flex items-center gap-2 text-green-600">
                <UserCheck className="h-5 w-5" />
                <span className="font-medium">{recognizedPerson.name}</span>
              </div>
            </div>
          )}
        </div>

        {status.message && (
          <Alert variant={status.type === 'error' ? 'destructive' : 'default'}>
            <AlertDescription>{status.message}</AlertDescription>
          </Alert>
        )}

        <RecentActivity />
      </CardContent>
    </Card>
  );
};

export default RecognitionTab;
