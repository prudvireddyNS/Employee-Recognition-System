// src/components/EmployeePortal.jsx
import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import RecognitionTab from './RecognitionTab';
import RegistrationTab from './RegistrationTab';

const EmployeePortal = () => {
  const [activeTab, setActiveTab] = useState('recognition');
  const [cameraActive, setCameraActive] = useState(true);

  return (
    <div className="w-full max-w-4xl mx-auto p-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="recognition">Recognition</TabsTrigger>
          <TabsTrigger value="register">New Employee</TabsTrigger>
        </TabsList>

        <TabsContent value="recognition">
          <RecognitionTab cameraActive={cameraActive} setCameraActive={setCameraActive} />
        </TabsContent>

        <TabsContent value="register">
          <RegistrationTab />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EmployeePortal;
