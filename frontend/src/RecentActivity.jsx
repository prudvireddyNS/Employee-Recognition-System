// src/components/RecentActivity.jsx
import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

const RecentActivity = () => {
  const [recentLogins, setRecentLogins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRecentLogins = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/recent-activity`);
        if (!response.ok) throw new Error('Failed to fetch recent activity');
        const data = await response.json();
        setRecentLogins(data);
        setError(null);
      } catch (error) {
        console.error('Error fetching recent logins:', error);
        setError('Failed to load recent activity');
      } finally {
        setLoading(false);
      }
    };

    fetchRecentLogins();
    const interval = setInterval(fetchRecentLogins, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center p-4">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        {error}
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-medium mb-4">Recent Activity</h3>
      <div className="space-y-3">
        {recentLogins.map((activity) => (
          <div 
            key={activity.id}
            className="flex justify-between items-center py-2 border-b last:border-0"
          >
            <div>
              <p className="font-medium">{activity.name}</p>
              <p className="text-sm text-gray-500 capitalize">{activity.department}</p>
            </div>
            <p className="text-sm text-gray-600">{activity.lastAttendance}</p>
          </div>
        ))}
        {recentLogins.length === 0 && (
          <p className="text-center text-gray-500 py-4">
            No recent activity
          </p>
        )}
      </div>
    </div>
  );
};

export default RecentActivity;
