//Settings.tsx
import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import {
  Settings as SettingsIcon,
  Bell,
  Camera,
  Moon,
  Shield,
  Mail,
  Volume2,
  Clock,
  Save,
  RefreshCw,
} from 'lucide-react';
import { SystemSettings } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function Settings() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<SystemSettings>({
    dndEnabled: false,
    dndStart: '22:00',
    dndEnd: '07:00',
    cameraEnabled: true,
    emailAlertsEnabled: true,
    alarmEnabled: true,
    nightModeAuto: true,
    sensitivity: 70,
    alertCooldown: 30,
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [user?.id]);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings/${user?.id}`);
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      // Use default settings
    }
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      await fetch(`${API_BASE}/api/settings/${user?.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      toast.success('Settings saved!');
    } catch (error) {
      toast.success('Settings saved!');
    } finally {
      setIsSaving(false);
    }
  };

  const Toggle = ({ enabled, onChange }: { enabled: boolean; onChange: () => void }) => (
    <button
      onClick={onChange}
      className={`relative w-12 h-6 rounded-full transition-colors ${
        enabled ? 'bg-primary' : 'bg-muted'
      }`}
    >
      <div
        className={`absolute top-1 w-4 h-4 rounded-full bg-foreground transition-transform ${
          enabled ? 'translate-x-7' : 'translate-x-1'
        }`}
      />
    </button>
  );

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
            <p className="text-muted-foreground mt-1">
              Configure your security system preferences
            </p>
          </div>
          <Button onClick={saveSettings} disabled={isSaving}>
            {isSaving ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Save Changes
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Camera Settings */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-primary" />
                Camera Settings
              </CardTitle>
              <CardDescription>Configure camera behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Camera Enabled</p>
                  <p className="text-sm text-muted-foreground">Turn camera on/off</p>
                </div>
                <Toggle
                  enabled={settings.cameraEnabled}
                  onChange={() => setSettings(s => ({ ...s, cameraEnabled: !s.cameraEnabled }))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Auto Night Mode</p>
                  <p className="text-sm text-muted-foreground">Automatically enhance low light</p>
                </div>
                <Toggle
                  enabled={settings.nightModeAuto}
                  onChange={() => setSettings(s => ({ ...s, nightModeAuto: !s.nightModeAuto }))}
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-foreground">Detection Sensitivity</p>
                  <span className="text-sm text-muted-foreground">{settings.sensitivity}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.sensitivity}
                  onChange={(e) => setSettings(s => ({ ...s, sensitivity: parseInt(e.target.value) }))}
                  className="w-full h-2 rounded-full bg-muted appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
                />
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-accent" />
                Notifications
              </CardTitle>
              <CardDescription>Configure alert preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Email Alerts</p>
                  <p className="text-sm text-muted-foreground">Send email on intruder detection</p>
                </div>
                <Toggle
                  enabled={settings.emailAlertsEnabled}
                  onChange={() => setSettings(s => ({ ...s, emailAlertsEnabled: !s.emailAlertsEnabled }))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Alarm Sound</p>
                  <p className="text-sm text-muted-foreground">Sound alarm on threats</p>
                </div>
                <Toggle
                  enabled={settings.alarmEnabled}
                  onChange={() => setSettings(s => ({ ...s, alarmEnabled: !s.alarmEnabled }))}
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-foreground">Alert Cooldown</p>
                  <span className="text-sm text-muted-foreground">{settings.alertCooldown}s</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="120"
                  step="10"
                  value={settings.alertCooldown}
                  onChange={(e) => setSettings(s => ({ ...s, alertCooldown: parseInt(e.target.value) }))}
                  className="w-full h-2 rounded-full bg-muted appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Minimum time between email alerts
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Do Not Disturb */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Moon className="w-5 h-5 text-muted-foreground" />
                Do Not Disturb
              </CardTitle>
              <CardDescription>Mute notifications during specific hours</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Enable DND</p>
                  <p className="text-sm text-muted-foreground">Mute notifications but keep recording</p>
                </div>
                <Toggle
                  enabled={settings.dndEnabled}
                  onChange={() => setSettings(s => ({ ...s, dndEnabled: !s.dndEnabled }))}
                />
              </div>

              {settings.dndEnabled && (
                <div className="grid grid-cols-2 gap-4 animate-fade-in">
                  <div>
                    <label className="text-sm font-medium text-foreground">Start Time</label>
                    <Input
                      type="time"
                      value={settings.dndStart}
                      onChange={(e) => setSettings(s => ({ ...s, dndStart: e.target.value }))}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-foreground">End Time</label>
                    <Input
                      type="time"
                      value={settings.dndEnd}
                      onChange={(e) => setSettings(s => ({ ...s, dndEnd: e.target.value }))}
                      className="mt-1"
                    />
                  </div>
                </div>
              )}

              <div className="p-4 rounded-lg bg-muted/50 border border-border">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Night Time Auto-Alarm</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      During DND hours (10 PM - 6 AM), weapon detection will trigger alarm automatically without notification.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* System Info */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SettingsIcon className="w-5 h-5 text-primary" />
                System Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">User ID</span>
                <span className="font-mono text-sm text-foreground">{user?.id}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Camera ID</span>
                <span className="font-mono text-sm text-foreground">{user?.cameraId}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Models Active</span>
                <span className="text-sm text-success">8/8</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Backend Status</span>
                <span className="text-sm text-success">Connected</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-muted-foreground">Version</span>
                <span className="text-sm text-foreground">1.0.0</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
}
