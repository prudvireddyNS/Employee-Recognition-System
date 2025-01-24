// src/components/RegistrationTab.jsx
import React, { useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Camera, RefreshCw } from 'lucide-react';
import RegistrationForm from './RegistrationForm';
import EmployeeIdCard from './EmployeeIdCard';
import CameraFeed from './CameraFeed';

const RegistrationTab = () => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isRegistered, setIsRegistered] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    department: '',
    position: '',
    email: '',
    companyEmail: ''
  });
  const [faceLocation, setFaceLocation] = useState(null);
  const previewRef = useRef(null);

  const adjustFaceLocation = (faces, imageElement) => {
    if (!faces || !faces.length || !imageElement) return null;
    
    const face = faces[0];
    const displayWidth = imageElement.clientWidth;
    const displayHeight = imageElement.clientHeight;
    const naturalWidth = imageElement.naturalWidth;
    const naturalHeight = imageElement.naturalHeight;

    // Calculate scaling factors
    const scaleX = displayWidth / naturalWidth;
    const scaleY = displayHeight / naturalHeight;

    return {
      left: face.left * scaleX,
      top: face.top * scaleY,
      width: (face.right - face.left) * scaleX,
      height: (face.bottom - face.top) * scaleY
    };
  };

  const handleCapture = async (imageDataUrl) => {
    try {
      // Detect face in captured image
      const response = await fetch(`${import.meta.env.VITE_API_URL}/detect-faces`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageDataUrl.split(',')[1] }),
      });

      const data = await response.json();
      
      if (data.success && data.faces.length > 0) {
        setCapturedImage(imageDataUrl);
        setFaceLocation(data.faces[0]); // Store the first face location
      }
    } catch (err) {
      console.error('Error detecting face in captured image:', err);
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setIsRegistered(false);
  };

  const handleRegister = async () => {
    setLoading(true);
    setMessage('');

    try {
      if (!capturedImage) {
        throw new Error('Please capture a photo first');
      }

      const payload = {
        image: capturedImage.split(',')[1],
        firstName: formData.firstName,
        lastName: formData.lastName,
        department: formData.department.toLowerCase(),
        position: formData.position,
        email: formData.email
      };

      const response = await fetch(`${import.meta.env.VITE_API_URL}/register-employee`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      setMessage('Employee registered successfully!');
      setIsRegistered(true);
      setFormData(prev => ({
        ...prev,
        companyEmail: data.company_email
      }));
    } catch (error) {
      console.error('Registration error:', error);
      setMessage(error.message);
      setIsRegistered(false);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    console.log('Form data updated:', name, value); // Debug log
  };

  const handleReset = () => {
    setCapturedImage(null);
    setIsRegistered(false);
    setMessage('');
    setFormData({
      firstName: '',
      lastName: '',
      department: '',
      position: '',
      email: '',
      companyEmail: ''
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {isRegistered ? 'Employee ID Card' : 'Register New Employee'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isRegistered ? (
          <div className="space-y-6">
            <EmployeeIdCard employee={formData} photo={capturedImage} />
            <Button onClick={handleReset} className="w-full">
              Register Another Employee
            </Button>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              <div className="relative w-full aspect-video bg-slate-950 rounded-lg overflow-hidden">
                {capturedImage ? (
                  <div className="relative w-full h-full" ref={previewRef}>
                    <img 
                      src={capturedImage} 
                      alt="Captured" 
                      className="w-full h-full object-cover"
                      onLoad={(e) => {
                        if (faceLocation) {
                          const adjusted = adjustFaceLocation(
                            [faceLocation],
                            e.target
                          );
                          if (adjusted) {
                            const box = document.createElement('div');
                            box.className = 'absolute border-4 border-green-500 rounded-sm';
                            box.style.left = `${adjusted.left}px`;
                            box.style.top = `${adjusted.top}px`;
                            box.style.width = `${adjusted.width}px`;
                            box.style.height = `${adjusted.height}px`;
                            
                            // Remove any existing face boxes
                            const existingBox = previewRef.current.querySelector('.face-box');
                            if (existingBox) {
                              existingBox.remove();
                            }
                            
                            box.classList.add('face-box');
                            previewRef.current.appendChild(box);
                          }
                        }
                      }}
                    />
                    <div className="absolute bottom-4 right-4">
                      <Button
                        onClick={handleRetake}
                        variant="secondary"
                        size="sm"
                      >
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Retake Photo
                      </Button>
                    </div>
                  </div>
                ) : (
                  <CameraFeed 
                    active={true} 
                    onFaceDetected={handleCapture}
                    captureMode={true}
                  />
                )}
              </div>
            </div>
            <RegistrationForm
              formData={formData}
              handleChange={handleChange}
              handleRegister={handleRegister}
              capturedImage={capturedImage}
              loading={loading}
              message={message}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default RegistrationTab;