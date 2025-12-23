//Chatbot.tsx
import { useState, useRef, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  AlertTriangle,
  Users,
  Camera,
  History,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const quickCommands = [
  { label: 'Was this person seen before?', icon: Users },
  { label: 'Show last 5 intruder events', icon: AlertTriangle },
  { label: 'Add this person to authorized list', icon: Users },
  { label: 'What is the camera status?', icon: Camera },
  { label: 'Show today\'s activity summary', icon: History },
];

export default function Chatbot() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello ${user?.username}! I'm your security assistant. I can help you with:\n\n• Checking intruder history\n• Managing authorized faces\n• Viewing camera status\n• Understanding alerts\n\nHow can I help you today?`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const processCommand = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('intruder') || lowerQuery.includes('last') || lowerQuery.includes('event')) {
      return `📋 **Intruder Logs:**\n\nNo intruder events recorded yet. The system will log events when the backend is running and detections occur.\n\nTo start monitoring:\n1. Ensure your backend server is running\n2. Go to **Live Feed** and start the camera\n3. Any detected intruders will appear in **Intruder Logs**`;
    }

    if (lowerQuery.includes('camera') || lowerQuery.includes('status')) {
      return `📹 **Camera Status:**\n\n• Camera ID: ${user?.cameraId || 'Not configured'}\n• Backend: Check if server is running\n\nTo check live status, go to **Live Feed** and start the camera.`;
    }

    if (lowerQuery.includes('add') || lowerQuery.includes('authorized')) {
      return `To add a person to the authorized list:\n\n1. Go to **Known Faces** in the sidebar\n2. Click **Add New Person**\n3. Enter their name\n4. Capture at least 5 photos\n5. Save and the system will train automatically\n\nWould you like me to take you there?`;
    }

    if (lowerQuery.includes('person') || lowerQuery.includes('seen') || lowerQuery.includes('before')) {
      return `🔍 **Face Search:**\n\nNo face data available. To check if a person has been seen:\n\n1. Ensure your backend is running\n2. Upload or capture images in **Known Faces**\n3. The system will track detections when monitoring\n\nCurrently no persons are registered in the database.`;
    }

    if (lowerQuery.includes('summary') || lowerQuery.includes('today') || lowerQuery.includes('activity')) {
      return `📊 **Activity Summary:**\n\nNo activity data available. Start monitoring to collect data:\n\n1. Run your backend server\n2. Go to **Live Feed** and start camera\n3. Activity will be tracked automatically`;
    }

    if (lowerQuery.includes('help') || lowerQuery.includes('what can')) {
      return `I can help you with:\n\n🔍 **Queries:**\n• "Show intruder events"\n• "Was this person seen before?"\n• "What is the camera status?"\n\n⚙️ **Actions:**\n• "Add person to authorized list"\n\n📊 **Reports:**\n• "Show activity summary"\n\nNote: Most features require the backend server to be running.`;
    }

    return `I understand you're asking about: "${query}"\n\nI'm your security assistant. I can help with:\n\n• Checking intruder logs\n• Camera status\n• Managing known faces\n• Activity summaries\n\n**Note:** Connect to your backend server for full functionality.`;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const response = processCommand(input);
    
    const assistantMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response,
      timestamp: new Date(),
    };

    setIsTyping(false);
    setMessages(prev => [...prev, assistantMessage]);
  };

  const handleQuickCommand = (command: string) => {
    setInput(command);
    handleSend();
  };

  return (
    <MainLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col animate-fade-in">
        {/* Header */}
        <div className="mb-4">
          <h1 className="text-3xl font-bold text-foreground">Security Assistant</h1>
          <p className="text-muted-foreground mt-1">
            Local AI chatbot for security queries (no external APIs)
          </p>
        </div>

        {/* Chat Container */}
        <Card variant="glass" className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-br-sm'
                      : 'bg-muted text-foreground rounded-bl-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-accent-foreground" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </CardContent>

          {/* Quick Commands */}
          <div className="px-4 py-2 border-t border-border">
            <div className="flex gap-2 overflow-x-auto scrollbar-thin pb-2">
              {quickCommands.map((cmd, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="whitespace-nowrap flex-shrink-0"
                  onClick={() => {
                    setInput(cmd.label);
                    setTimeout(handleSend, 100);
                  }}
                >
                  <cmd.icon className="w-3 h-3 mr-1" />
                  {cmd.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-border">
            <div className="flex gap-2">
              <Input
                placeholder="Ask about security, intruders, or system status..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                className="flex-1"
              />
              <Button onClick={handleSend} disabled={!input.trim() || isTyping}>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
}
