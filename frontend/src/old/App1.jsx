import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Camera, Loader2, UserCheck, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

const EmployeePortal = () => {
  // ... (previous state declarations remain the same)
  const [activeTab, setActiveTab] = useState('recognition');
  const [cameraActive, setCameraActive] = useState(true);
  const [recognizedPerson, setRecognizedPerson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    department: '',
    position: '',
    email: ''
  });
  const recognitionVideoRef = useRef(null);
  const registrationVideoRef = useRef(null);
  const streamRef = useRef(null);

  // Dummy data for recognized employees
  const dummyEmployees = [
    { id: 1, name: 'John Doe', department: 'Engineering', lastAttendance: '2025-01-15 09:01 AM' },
    { id: 2, name: 'Jane Smith', department: 'Design', lastAttendance: '2025-01-15 09:05 AM' },
  ];

  const startCamera = async (videoRef) => {
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

  useEffect(() => {
    if (activeTab === 'recognition' && cameraActive) {
      startCamera(recognitionVideoRef);
      const interval = setInterval(() => {
        const randomEmployee = dummyEmployees[Math.floor(Math.random() * dummyEmployees.length)];
        setRecognizedPerson(randomEmployee);
        setMessage(`✓ Attendance marked for ${randomEmployee.name}`);
      }, 5000);

      return () => {
        clearInterval(interval);
        if (activeTab !== 'register') {
          stopCamera();
        }
      };
    }
  }, [activeTab, cameraActive]);

  useEffect(() => {
    if (activeTab === 'register' && !capturedImage) {
      startCamera(registrationVideoRef);
    }

    return () => {
      if (activeTab !== 'recognition') {
        stopCamera();
      }
    };
  }, [activeTab, capturedImage]);

  const handleCapture = () => {
    setLoading(true);
    
    // Create a canvas element to capture the video frame
    const canvas = document.createElement('canvas');
    const video = registrationVideoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw the current video frame on the canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert the canvas to a data URL
    const imageDataUrl = canvas.toDataURL('image/jpeg');
    
    // Update state with the captured image
    setCapturedImage(imageDataUrl);
    stopCamera();
    setLoading(false);
  };

  const handleRegister = () => {
    setLoading(true);
    // Simulate registration delay
    setTimeout(() => {
      setMessage(`Employee registered successfully! Company email: ${formData.firstName.toLowerCase()}.${formData.lastName.toLowerCase()}@company.com`);
      setLoading(false);
    }, 2000);
  };

  const handleRetake = () => {
    setCapturedImage(null);
    startCamera(registrationVideoRef);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // ... (rest of the component remains the same until the render section)

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="recognition">Recognition</TabsTrigger>
          <TabsTrigger value="register">New Employee</TabsTrigger>
        </TabsList>

        <TabsContent value="recognition">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Face Recognition
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setCameraActive(!cameraActive)}
                >
                  {cameraActive ? <Camera className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Camera Feed */}
              <div className="relative w-full aspect-video bg-slate-950 mb-4 rounded-lg overflow-hidden">
                <video ref={recognitionVideoRef} autoPlay playsInline className="w-full h-full object-cover" />
                {recognizedPerson && (
                  <div className="absolute top-4 left-4 right-4 p-4 bg-green-500/20 backdrop-blur-sm rounded-lg border border-green-500">
                    <div className="flex items-center gap-2 text-green-600">
                      <UserCheck className="h-5 w-5" />
                      <span className="font-medium">{recognizedPerson.name}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Status and Recent Activity */}
              <div className="space-y-4">
                {message && (
                  <Alert>
                    <AlertDescription>{message}</AlertDescription>
                  </Alert>
                )}
                <div className="border rounded-lg p-4">
                  <h3 className="font-medium mb-2">Recent Activity</h3>
                  {dummyEmployees.map(emp => (
                    <div key={emp.id} className="flex justify-between items-center py-2">
                      <div>
                        <p className="font-medium">{emp.name}</p>
                        <p className="text-sm text-gray-500">{emp.department}</p>
                      </div>
                      <p className="text-sm">{emp.lastAttendance}</p>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="register">
          <Card>
            <CardHeader>
              <CardTitle>Register New Employee</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Camera Capture Section */}
              <div className="space-y-4 mb-6">
                <div className="relative w-full aspect-video bg-slate-950 rounded-lg overflow-hidden">
                  {capturedImage ? (
                    <img src={capturedImage} alt="captured" className="w-full h-full object-cover" />
                  ) : (
                    <video ref={registrationVideoRef} autoPlay playsInline className="w-full h-full object-cover" />
                  )}
                </div>
                {!capturedImage ? (
                  <Button
                    onClick={handleCapture}
                    className="w-full"
                    disabled={loading}
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Camera className="h-4 w-4 mr-2" />
                        Capture Photo
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    onClick={handleRetake}
                    className="w-full"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retake Photo
                  </Button>
                )}
              </div>

              {/* Registration Form */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input id="firstName" name="firstName" value={formData.firstName} onChange={handleChange} placeholder="John" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input id="lastName" name="lastName" value={formData.lastName} onChange={handleChange} placeholder="Doe" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Select value={formData.department} onValueChange={(value) => setFormData({ ...formData, department: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="engineering">Engineering</SelectItem>
                      <SelectItem value="design">Design</SelectItem>
                      <SelectItem value="marketing">Marketing</SelectItem>
                      <SelectItem value="hr">HR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="position">Position</Label>
                  <Input id="position" name="position" value={formData.position} onChange={handleChange} placeholder="Software Engineer" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Personal Email</Label>
                  <Input id="email" name="email" type="email" value={formData.email} onChange={handleChange} placeholder="john@example.com" />
                </div>

                <Button
                  onClick={handleRegister}
                  className="w-full"
                  disabled={loading || !capturedImage}
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Register Employee'
                  )}
                </Button>

                {message && (
                  <Alert>
                    <AlertDescription>{message}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EmployeePortal;