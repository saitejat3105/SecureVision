//LiveFeed.tsx
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useCamera } from '@/contexts/CameraContext';
import {
  Camera,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Shrink,
  AlertTriangle,
  Mic,
  MicOff,
  Sun,
  Moon,
  Play,
  Square,
  BellOff,
  VideoOff,
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function LiveFeed() {
  const { user } = useAuth();
  const { stream, isStreaming, isMuted, error, startCamera, stopCamera, toggleMute } = useCamera();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMicOn, setIsMicOn] = useState(false);
  const [isNightMode, setIsNightMode] = useState(false);
  const [isAlarmActive, setIsAlarmActive] = useState(false);
  const alarmIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Cleanup alarm on unmount
  useEffect(() => {
    return () => {
      if (alarmIntervalRef.current) {
        clearInterval(alarmIntervalRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Attach stream to video element when it changes
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.muted = isMuted;
    }
  }, [stream, isMuted]);

  // Update video muted state when isMuted changes
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.muted = isMuted;
    }
  }, [isMuted]);

  const toggleFullscreen = () => {
    if (isFullscreen) {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    } else if (videoRef.current) {
      videoRef.current.requestFullscreen?.();
      setIsFullscreen(true);
    }
  };

  const handleMinimize = () => {
    // Navigate back to previous page (for floating player)
    navigate(-1);
  };

  const handleToggleMic = async () => {
    if (!isMicOn) {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsMicOn(true);
        toast.success('Microphone activated');
      } catch (error) {
        toast.error('Failed to access microphone');
      }
    } else {
      setIsMicOn(false);
      toast.info('Microphone deactivated');
    }
  };

  // Start alarm with Web Audio API (works without backend)
  const startAlarm = () => {
    // Stop any existing alarm first
    stopAlarm();
    
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    audioContextRef.current = audioContext;
    
    const playBeep = () => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Siren effect - alternate between two frequencies
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.2);
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.4);
      
      gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    };
    
    // Play immediately
    playBeep();
    
    // Repeat every 600ms
    alarmIntervalRef.current = setInterval(playBeep, 600);
  };

  const stopAlarm = () => {
    if (alarmIntervalRef.current) {
      clearInterval(alarmIntervalRef.current);
      alarmIntervalRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const handleToggleAlarm = () => {
    if (!isAlarmActive) {
      setIsAlarmActive(true);
      startAlarm();
      toast.success('Alarm triggered!');
    } else {
      setIsAlarmActive(false);
      stopAlarm();
      toast.info('Alarm stopped');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Live Camera Feed</h1>
            <p className="text-muted-foreground mt-1">
              Real-time monitoring for {user?.cameraId}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {!isStreaming ? (
              <Button variant="default" onClick={startCamera}>
                <Play className="w-4 h-4 mr-2" />
                Start Camera
              </Button>
            ) : (
              <Button variant="destructive" onClick={stopCamera}>
                <Square className="w-4 h-4 mr-2" />
                Stop Camera
              </Button>
            )}
            
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              isStreaming ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-success animate-pulse' : 'bg-danger'}`} />
              {isStreaming ? 'Camera On' : 'Camera Off'}
            </div>
          </div>
        </div>

        {/* Main Video Feed */}
        <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-background p-4' : ''}`}>
          <Card variant="glass" className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between py-3 border-b border-border">
              <CardTitle className="flex items-center gap-2 text-base">
                <Camera className="w-5 h-5 text-primary" />
                {user?.cameraId} - {isStreaming ? 'Live' : 'Offline'}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon-sm" onClick={() => setIsNightMode(!isNightMode)} disabled={!isStreaming}>
                  {isNightMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={toggleMute} disabled={!isStreaming}>
                  {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={handleToggleMic} disabled={!isStreaming}>
                  {isMicOn ? <Mic className="w-4 h-4 text-success" /> : <MicOff className="w-4 h-4" />}
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={handleMinimize} title="Back to floating player">
                  <Shrink className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon-sm" onClick={toggleFullscreen}>
                  {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0 relative">
              {/* Progress bar */}
              <div className="h-1 bg-primary/20">
                <div className={`h-full bg-primary transition-all duration-1000 ${isStreaming ? 'w-full' : 'w-0'}`} />
              </div>

              {/* Video Container */}
              <div className={`relative ${isFullscreen ? 'h-[calc(100vh-12rem)]' : ''} bg-black`} style={{ aspectRatio: isFullscreen ? undefined : '16/9' }}>
                {error ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4">
                    <VideoOff className="w-12 h-12 text-muted-foreground mb-3" />
                    <p className="text-muted-foreground text-sm">{error}</p>
                    <Button variant="outline" size="sm" className="mt-4" onClick={startCamera}>
                      Retry
                    </Button>
                  </div>
                ) : (
                  <>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted={isMuted}
                      className={`w-full h-full object-cover ${isNightMode ? 'brightness-150 contrast-125 hue-rotate-[120deg]' : ''}`}
                      style={{ display: 'block', backgroundColor: '#000' }}
                    />
                    
                    {/* Offline overlay */}
                    {!isStreaming && !error && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-black">
                        <Camera className="w-16 h-16 text-muted-foreground/50 mb-4" />
                        <p className="text-muted-foreground text-lg">Camera is offline</p>
                        <p className="text-muted-foreground/60 text-sm mt-2">Click "Start Camera" to begin</p>
                      </div>
                    )}

                    {/* Timestamp overlay */}
                    {isStreaming && (
                      <div className="absolute bottom-3 left-3 text-xs font-mono bg-black/70 text-white px-2 py-1 rounded">
                        {new Date().toLocaleString()}
                      </div>
                    )}

                    {/* REC indicator */}
                    {isStreaming && (
                      <div className="absolute top-3 left-3 flex items-center gap-2">
                        <span className="flex items-center gap-1 bg-black/70 text-primary px-2 py-1 rounded text-xs">
                          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                          REC
                        </span>
                        {!isMuted && (
                          <span className="flex items-center gap-1 bg-black/70 text-success px-2 py-1 rounded text-xs">
                            <Volume2 className="w-3 h-3" />
                            Audio On
                          </span>
                        )}
                      </div>
                    )}

                    {/* Scan line effect */}
                    {isStreaming && (
                      <div className="absolute inset-0 overflow-hidden pointer-events-none">
                        <div className="w-full h-1 bg-gradient-to-r from-transparent via-primary/30 to-transparent animate-scan" />
                      </div>
                    )}

                    {/* Night mode overlay */}
                    {isNightMode && isStreaming && (
                      <div className="absolute inset-0 bg-emerald-900/10 pointer-events-none mix-blend-overlay" />
                    )}
                  </>
                )}
              </div>

              {/* Bottom Controls */}
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background/90 to-transparent">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Button 
                      variant={isAlarmActive ? "outline" : "destructive"} 
                      onClick={handleToggleAlarm}
                    >
                      {isAlarmActive ? (
                        <>
                          <BellOff className="w-4 h-4 mr-2" />
                          Stop Alarm
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          Sound Alarm
                        </>
                      )}
                    </Button>
                    {isAlarmActive && (
                      <span className="text-danger text-sm font-medium animate-pulse">
                        🔔 Alarm Active
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-4 gap-3">
          <Button 
            variant="destructive" 
            className="gap-2 h-12"
            onClick={handleToggleAlarm}
          >
            <span className="text-lg">🚨</span>
            <span className="text-xs">ALARM</span>
          </Button>
          <Button variant="secondary" className="gap-2 h-12" onClick={handleToggleMic}>
            <Mic className="w-4 h-4" />
            <span className="text-xs">Speak</span>
          </Button>
          <Button variant="secondary" className="gap-2 h-12">
            <Camera className="w-4 h-4" />
            <span className="text-xs">Snapshot</span>
          </Button>
          <Button variant="secondary" className="gap-2 h-12" onClick={toggleMute}>
            <Volume2 className="w-4 h-4" />
            <span className="text-xs">{isMuted ? 'Unmute' : 'Mute'}</span>
          </Button>
        </div>
      </div>
    </MainLayout>
  );
}
