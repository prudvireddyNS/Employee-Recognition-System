// src/components/RecentActivity.jsx
import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { formatDistanceToNow, parseISO, format } from 'date-fns';

const RecentActivity = () => {
  const [recentLogins, setRecentLogins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchRecentLogins = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/recent-activity`);
      if (!response.ok) throw new Error('Failed to fetch recent activity');
      const data = await response.json();
      
      const formattedData = data.map(activity => {
        const timestamp = parseISO(activity.lastAttendance);
        return {
          ...activity,
          timestamp,
          relativeTime: formatDistanceToNow(timestamp, { 
            addSuffix: true,
            includeSeconds: true 
          })
        };
      });
      
      setRecentLogins(formattedData);
      setLastUpdate(new Date());
      setError(null);
    } catch (error) {
      console.error('Error fetching recent logins:', error);
      setError('Failed to load recent activity');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecentLogins();
    // Update every 30 seconds
    const interval = setInterval(fetchRecentLogins, 30000);
    return () => clearInterval(interval);
  }, []);

  // Update relative times every minute
  useEffect(() => {
    const intervalId = setInterval(() => {
      setRecentLogins(current => 
        current.map(activity => ({
          ...activity,
          relativeTime: formatDistanceToNow(new Date(activity.lastAttendance), { addSuffix: true })
        }))
      );
    }, 60000);

    return () => clearInterval(intervalId);
  }, []);

  const formatTime = (timestamp) => {
    return format(parseISO(timestamp), 'hh:mm a');
  };

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
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-medium">Recent Activity</h3>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            Last updated: {formatDistanceToNow(lastUpdate, { addSuffix: true, includeSeconds: true })}
          </span>
        )}
      </div>
      <div className="space-y-3">
        {recentLogins.map((activity) => (
          <div 
            key={`${activity.id}-${activity.timestamp.getTime()}`}
            className="flex justify-between items-center py-2 border-b last:border-0"
          >
            <div>
              <p className="font-medium">{activity.name}</p>
              <p className="text-sm text-gray-500 capitalize">{activity.department}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">{activity.relativeTime}</p>
              <p className="text-xs text-gray-400">
                {formatTime(activity.lastAttendance)}
              </p>
            </div>
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
