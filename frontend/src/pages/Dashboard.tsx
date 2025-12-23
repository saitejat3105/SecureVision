//Dashboard.tsx
import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';
import {
  Camera,
  AlertTriangle,
  Users,
  Shield,
  Activity,
  Clock,
  TrendingUp,
  Bell,
  CheckCircle,
  XCircle,
  Volume2,
  Play,
  RefreshCw,
} from 'lucide-react';
import { SecurityStats, IntruderLog } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function Dashboard() {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [stats, setStats] = useState<SecurityStats>({
    totalIntruders: 0,
    totalVisitors: 0,
    alertsToday: 0,
    uptime: 0,
    modelsActive: 0,
  });
  const [recentAlerts, setRecentAlerts] = useState<IntruderLog[]>([]);
  const [systemStatus, setSystemStatus] = useState({
    camera: false,
    models: false,
    alerts: false,
    audio: false,
  });

  const fetchData = async () => {
    try {
      // Fetch stats and known faces count from backend
      const [statsResponse, facesResponse] = await Promise.all([
        fetch(`${API_BASE}/api/stats/${user?.cameraId}`),
        fetch(`${API_BASE}/api/faces/${user?.id}`),
      ]);
      
      let knownFacesCount = 0;
      if (facesResponse.ok) {
        const facesData = await facesResponse.json();
        knownFacesCount = facesData.faces?.length || 0;
      }
      
      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats({
          totalIntruders: data.stats?.totalIntruders || 0,
          totalVisitors: knownFacesCount,
          alertsToday: data.stats?.alertsToday || 0,
          uptime: data.stats?.uptime || 0,
          modelsActive: data.stats?.modelsActive || 0,
        });
        setRecentAlerts(data.recentAlerts || []);
        setSystemStatus(data.systemStatus || {
          camera: false,
          models: false,
          alerts: false,
          audio: false,
        });
        setIsBackendOnline(true);
      } else {
        setIsBackendOnline(false);
      }
    } catch (error) {
      console.log('Backend offline');
      setIsBackendOnline(false);
      setStats({
        totalIntruders: 0,
        totalVisitors: 0,
        alertsToday: 0,
        uptime: 0,
        modelsActive: 0,
      });
      setRecentAlerts([]);
      setSystemStatus({
        camera: false,
        models: false,
        alerts: false,
        audio: false,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [user?.cameraId]);

  const handleSoundAlarm = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/alarm/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cameraId: user?.cameraId }),
      });
      if (response.ok) {
        toast.success('Alarm triggered!');
      } else {
        toast.error('Failed to trigger alarm');
      }
    } catch (error) {
      toast.error('Backend is offline');
    }
  };

  const statCards = [
    {
      title: 'Camera Status',
      value: isBackendOnline ? (systemStatus.camera ? 'Online' : 'Offline') : 'Unknown',
      icon: Camera,
      color: systemStatus.camera && isBackendOnline ? 'text-success' : 'text-danger',
      bgColor: systemStatus.camera && isBackendOnline ? 'bg-success/10' : 'bg-danger/10',
    },
    {
      title: 'Alerts Today',
      value: isLoading ? '...' : stats.alertsToday.toString(),
      icon: AlertTriangle,
      color: stats.alertsToday > 0 ? 'text-warning' : 'text-success',
      bgColor: stats.alertsToday > 0 ? 'bg-warning/10' : 'bg-success/10',
    },
    {
      title: 'Known Faces',
      value: isLoading ? '...' : stats.totalVisitors.toString(),
      icon: Users,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      title: 'ML Models Active',
      value: isLoading ? '...' : `${stats.modelsActive}/8`,
      icon: Shield,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Security Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Welcome back, {user?.username}. 
              {isBackendOnline ? ' Your system is monitoring.' : ' Backend is offline.'}
            </p>
          </div>
          <div className="flex gap-3 items-center">
            {!isBackendOnline && (
              <Button variant="outline" size="sm" onClick={fetchData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry Connection
              </Button>
            )}
            <Button variant="outline" asChild>
              <Link to="/live-feed">
                <Camera className="w-4 h-4 mr-2" />
                View Live Feed
              </Link>
            </Button>
            <Button variant="alarm" onClick={handleSoundAlarm} disabled={!isBackendOnline}>
              <Volume2 className="w-4 h-4 mr-2" />
              Sound Alarm
            </Button>
          </div>
        </div>

        {/* Backend Status Banner */}
        {!isBackendOnline && !isLoading && (
          <Card className="border-warning/50 bg-warning/10">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-warning" />
              <div className="flex-1">
                <p className="font-medium text-foreground">Backend Offline</p>
                <p className="text-sm text-muted-foreground">
                  Run <code className="px-1.5 py-0.5 bg-muted rounded text-xs">python app.py</code> in your backend folder to start the server.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((stat, index) => (
            <Card key={stat.title} variant="glass" className="animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.title}</p>
                    <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                    <stat.icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Alerts */}
          <Card variant="glass" className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-warning" />
                Recent Alerts
              </CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/intruder-logs">View All</Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">
                  <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin" />
                  <p>Loading alerts...</p>
                </div>
              ) : recentAlerts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="w-12 h-12 mx-auto mb-3 text-success" />
                  <p>No alerts - All clear!</p>
                </div>
              ) : (
                recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 border border-border/50 hover:border-warning/30 transition-colors"
                  >
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      alert.severity > 7 ? 'bg-danger/20 text-danger' :
                      alert.severity > 4 ? 'bg-warning/20 text-warning' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      <AlertTriangle className="w-6 h-6" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">{alert.details}</p>
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                        <span>Confidence: {(alert.confidence * 100).toFixed(0)}%</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          alert.severity > 7 ? 'bg-danger/20 text-danger' :
                          alert.severity > 4 ? 'bg-warning/20 text-warning' :
                          'bg-success/20 text-success'
                        }`}>
                          Severity: {alert.severity}/10
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* System Status */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(systemStatus).map(([key, status]) => (
                <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                  <span className="capitalize text-foreground">{key}</span>
                  <div className={`flex items-center gap-2 ${isBackendOnline && status ? 'text-success' : 'text-danger'}`}>
                    {isBackendOnline && status ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    <span className="text-sm font-medium">
                      {isBackendOnline ? (status ? 'Active' : 'Inactive') : 'Unknown'}
                    </span>
                  </div>
                </div>
              ))}
              
              <div className="pt-4 border-t border-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">System Uptime</span>
                  <span className="text-sm font-medium text-success">
                    {isBackendOnline ? `${stats.uptime}%` : 'N/A'}
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                  <div 
                    className="h-full gradient-primary rounded-full transition-all duration-500"
                    style={{ width: isBackendOnline ? `${stats.uptime}%` : '0%' }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
                <Link to="/known-faces">
                  <Users className="w-6 h-6" />
                  <span>Add Person</span>
                </Link>
              </Button>
              <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
                <Link to="/training">
                  <TrendingUp className="w-6 h-6" />
                  <span>Train Model</span>
                </Link>
              </Button>
              <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
                <Link to="/voice-chat">
                  <Volume2 className="w-6 h-6" />
                  <span>Voice Message</span>
                </Link>
              </Button>
              <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
                <Link to="/settings">
                  <Shield className="w-6 h-6" />
                  <span>Settings</span>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
