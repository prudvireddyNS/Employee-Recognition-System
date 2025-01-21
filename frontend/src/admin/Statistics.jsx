import React, { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, Users, Clock, Building } from 'lucide-react';

const Statistics = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/admin/statistics`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardContent className="flex items-center p-6">
          <Users className="h-8 w-8 text-blue-500 mr-4" />
          <div>
            <p className="text-sm font-medium">Total Employees</p>
            <p className="text-2xl font-bold">{stats?.total_employees}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center p-6">
          <Clock className="h-8 w-8 text-green-500 mr-4" />
          <div>
            <p className="text-sm font-medium">Today's Attendance</p>
            <p className="text-2xl font-bold">{stats?.today_attendance}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center p-6">
          <Building className="h-8 w-8 text-purple-500 mr-4" />
          <div>
            <p className="text-sm font-medium">Departments</p>
            <p className="text-2xl font-bold">
              {stats?.department_distribution.length}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="md:col-span-2 lg:col-span-3">
        <CardContent className="p-6">
          <h3 className="font-medium mb-4">Department Distribution</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {stats?.department_distribution.map((dept) => (
              <div 
                key={dept.department} 
                className="p-4 rounded-lg border bg-card"
              >
                <p className="text-sm capitalize">{dept.department}</p>
                <p className="text-xl font-bold">{dept.count}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Statistics;
