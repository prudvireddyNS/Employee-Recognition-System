import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Statistics from './admin/Statistics';
import EmployeeList from './admin/EmployeeList';
import AttendanceReport from './admin/AttendanceReport';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div className="p-4">Something went wrong loading this component.</div>;
    }
    return this.props.children;
  }
}

function AdminPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Check for admin token
    const token = localStorage.getItem('adminToken');
    if (!token) {
      navigate('/login');
    }
  }, [navigate]);

  const handleApiError = (error) => {
    if (error.status === 401) {
      localStorage.removeItem('adminToken');
      navigate('/login');
    }
  };

  return (
    <div className="container mx-auto py-6 px-4">
      <h1 className="text-2xl font-semibold mb-6">Admin Dashboard</h1>
      
      <Tabs defaultValue="statistics">
        <TabsList>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
          <TabsTrigger value="employees">Employees</TabsTrigger>
          <TabsTrigger value="attendance">Attendance</TabsTrigger>
        </TabsList>
        
        <TabsContent value="statistics">
          <ErrorBoundary>
            <Statistics onError={handleApiError} />
          </ErrorBoundary>
        </TabsContent>
        
        <TabsContent value="employees">
          <ErrorBoundary>
            <EmployeeList onError={handleApiError} />
          </ErrorBoundary>
        </TabsContent>
        
        <TabsContent value="attendance">
          <ErrorBoundary>
            <AttendanceReport onError={handleApiError} />
          </ErrorBoundary>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AdminPage;
