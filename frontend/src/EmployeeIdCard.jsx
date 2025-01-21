// src/components/EmployeeIdCard.jsx
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';

const EmployeeIdCard = ({ employee, photo }) => {
  if (!employee || !photo) {
    return <p className="text-center text-red-500">Invalid employee data or photo</p>;
  }

  return (
    <Card className="max-w-md mx-auto bg-white">
      <CardContent className="p-6">
        <div className="flex flex-col items-center space-y-4">
          {/* Employee Photo */}
          <div className="w-32 h-32 rounded-full overflow-hidden border-4 border-blue-500">
            <img 
              src={photo} 
              alt={`${employee.firstName} ${employee.lastName}`}
              className="w-full h-full object-cover"
            />
          </div>
          
          {/* Employee Details */}
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-gray-800">
              {employee.firstName} {employee.lastName}
            </h2>
            <p className="text-lg font-medium text-gray-600 capitalize">
              {employee.position}
            </p>
            <p className="text-sm text-gray-500 capitalize">
              {employee.department} Department
            </p>
          </div>
          
          {/* Company Email */}
          <div className="w-full pt-4 border-t border-gray-200">
            <p className="text-sm text-center text-gray-600">
              <span className="font-medium">Company Email:</span><br />
              {employee.companyEmail}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default EmployeeIdCard;