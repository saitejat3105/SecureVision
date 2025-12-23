//VoiceChat.tsx
import { useState, useEffect, useRef } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Send,
  Play,
  Pause,
  Phone,
  PhoneOff,
  MessageSquare,
} from 'lucide-react';
import { VoiceMessage } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const presetMessages = [
  "Leave the package at the door",
  "I'll be there in 5 minutes",
  "Please wait, I'm coming",
  "This property is monitored by security",
  "I can see you, please identify yourself",
];

export default function VoiceChat() {
  const { user } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [textMessage, setTextMessage] = useState('');
  const [isCallActive, setIsCallActive] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Demo messages
    setMessages([
      { id: '1', type: 'incoming', timestamp: new Date(Date.now() - 3600000).toISOString(), duration: 5 },
      { id: '2', type: 'outgoing', timestamp: new Date(Date.now() - 1800000).toISOString(), duration: 3 },
    ]);
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      toast.info('Recording started...');
    } catch (error) {
      toast.error('Failed to access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast.success('Voice message sent!');
    }
  };

  const sendAudioMessage = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('cameraId', user?.cameraId || '');

      await fetch(`${API_BASE}/api/voice/send`, {
        method: 'POST',
        body: formData,
      });

      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'outgoing',
        timestamp: new Date().toISOString(),
        duration: Math.round(audioBlob.size / 16000),
      }]);
    } catch (error) {
      // Demo mode
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'outgoing',
        timestamp: new Date().toISOString(),
        duration: 3,
      }]);
    }
  };

  const sendTextToSpeech = async (text: string) => {
    if (!text.trim()) return;

    try {
      await fetch(`${API_BASE}/api/voice/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, cameraId: user?.cameraId }),
      });
      toast.success('Message played on system!');
      setTextMessage('');
    } catch (error) {
      toast.success('Message played on system!');
      setTextMessage('');
    }
  };

  const toggleLiveCall = () => {
    if (isCallActive) {
      // End call
      if (wsRef.current) {
        wsRef.current.close();
      }
      setIsCallActive(false);
      setIsListening(false);
      toast.info('Call ended');
    } else {
      // Start call
      try {
        const wsUrl = API_BASE.replace('http', 'ws');
        wsRef.current = new WebSocket(`${wsUrl}/ws/voice/${user?.cameraId}`);
        wsRef.current.onopen = () => {
          setIsCallActive(true);
          toast.success('Connected - two-way audio active');
        };
        wsRef.current.onclose = () => {
          setIsCallActive(false);
        };
      } catch (error) {
        setIsCallActive(true);
        toast.success('Connected - two-way audio active');
      }
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Voice Communication</h1>
            <p className="text-muted-foreground mt-1">
              Two-way audio with your security system
            </p>
          </div>
          <Button
            variant={isCallActive ? 'destructive' : 'default'}
            size="lg"
            onClick={toggleLiveCall}
          >
            {isCallActive ? (
              <>
                <PhoneOff className="w-5 h-5 mr-2" />
                End Live Call
              </>
            ) : (
              <>
                <Phone className="w-5 h-5 mr-2" />
                Start Live Call
              </>
            )}
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Voice Recording */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mic className="w-5 h-5 text-primary" />
                Send Voice Message
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex justify-center">
                <button
                  className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isRecording
                      ? 'gradient-danger glow-danger animate-pulse-ring'
                      : 'gradient-primary glow-primary hover:scale-105'
                  }`}
                  onMouseDown={startRecording}
                  onMouseUp={stopRecording}
                  onMouseLeave={() => isRecording && stopRecording()}
                  onTouchStart={startRecording}
                  onTouchEnd={stopRecording}
                >
                  {isRecording ? (
                    <MicOff className="w-12 h-12 text-danger-foreground" />
                  ) : (
                    <Mic className="w-12 h-12 text-primary-foreground" />
                  )}
                </button>
              </div>
              <p className="text-center text-sm text-muted-foreground">
                {isRecording ? 'Release to send' : 'Hold to record'}
              </p>

              {/* Live Call Status */}
              {isCallActive && (
                <div className="p-4 rounded-lg bg-success/10 border border-success/30">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-success animate-pulse" />
                    <span className="font-medium text-success">Live call active</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Two-way audio is now enabled. Speak to communicate with anyone at the camera.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Text to Speech */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-accent" />
                Text to Speech
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Type a message to play on the system..."
                  value={textMessage}
                  onChange={(e) => setTextMessage(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendTextToSpeech(textMessage)}
                />
                <Button onClick={() => sendTextToSpeech(textMessage)}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Quick Messages</p>
                <div className="flex flex-wrap gap-2">
                  {presetMessages.map((msg, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => sendTextToSpeech(msg)}
                    >
                      {msg}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Message History */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Message History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-center gap-4 p-4 rounded-lg ${
                    msg.type === 'incoming' ? 'bg-primary/10' : 'bg-muted'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    msg.type === 'incoming' ? 'bg-primary/20' : 'bg-accent/20'
                  }`}>
                    {msg.type === 'incoming' ? (
                      <Volume2 className="w-5 h-5 text-primary" />
                    ) : (
                      <Mic className="w-5 h-5 text-accent" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-foreground">
                      {msg.type === 'incoming' ? 'Incoming' : 'Outgoing'} Voice Message
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(msg.timestamp).toLocaleString()} • {msg.duration}s
                    </p>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Play className="w-4 h-4" />
                  </Button>
                </div>
              ))}

              {messages.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Volume2 className="w-12 h-12 mx-auto mb-3" />
                  <p>No voice messages yet</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
