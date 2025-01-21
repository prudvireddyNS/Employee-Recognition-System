// src/components/RegistrationForm.jsx
import React from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

const RegistrationForm = ({ formData, handleChange, handleRegister, capturedImage, loading, message }) => {
  const isFormValid = () => {
    console.log('Form validation:', {
      firstName: Boolean(formData.firstName?.trim()),
      lastName: Boolean(formData.lastName?.trim()),
      department: Boolean(formData.department),
      position: Boolean(formData.position?.trim()),
      email: Boolean(formData.email?.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)),
      image: Boolean(capturedImage)
    });

    return (
      formData.firstName?.trim() && 
      formData.lastName?.trim() && 
      formData.department && 
      formData.position?.trim() && 
      formData.email?.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/) && 
      capturedImage
    );
  };

  const handleSelectChange = (value) => {
    handleChange({ target: { name: 'department', value } });
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="firstName">First Name</Label>
          <Input 
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            placeholder="John"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="lastName">Last Name</Label>
          <Input 
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            placeholder="Doe"
            required
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="department">Department</Label>
        <Select 
          value={formData.department} 
          onValueChange={handleSelectChange}
        >
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
        <Input 
          id="position"
          name="position"
          value={formData.position}
          onChange={handleChange}
          placeholder="Software Engineer"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Personal Email</Label>
        <Input 
          id="email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="john@example.com"
          required
        />
      </div>

      <Button
        onClick={handleRegister}
        className="w-full"
        disabled={!isFormValid()}
        type="button"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : (
          'Register Employee'
        )}
      </Button>

      {/* Debug info - remove in production */}
      <div className="text-sm text-gray-500">
        <p>Form Status:</p>
        <ul>
          <li>First Name: {formData.firstName ? '✓' : '×'}</li>
          <li>Last Name: {formData.lastName ? '✓' : '×'}</li>
          <li>Department: {formData.department ? '✓' : '×'}</li>
          <li>Position: {formData.position ? '✓' : '×'}</li>
          <li>Email: {formData.email?.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/) ? '✓' : '×'}</li>
          <li>Image Captured: {capturedImage ? '✓' : '×'}</li>
        </ul>
      </div>

      {message && (
        <Alert variant={message.toLowerCase().includes("error") || message.toLowerCase().includes("failed") ? "destructive" : "default"}>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default RegistrationForm;
