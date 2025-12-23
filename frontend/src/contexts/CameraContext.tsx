//CameraContext.tsx
import { createContext, useContext, useState, useRef, useCallback, ReactNode } from 'react';
import { toast } from 'sonner';

interface CameraContextType {
  stream: MediaStream | null;
  isStreaming: boolean;
  isMuted: boolean;
  error: string | null;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  toggleMute: () => void;
  videoRef: React.RefObject<HTMLVideoElement>;
  attachVideo: (video: HTMLVideoElement) => void;
}

const CameraContext = createContext<CameraContextType | null>(null);

export function CameraProvider({ children }: { children: ReactNode }) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 }, 
        audio: true 
      });
      
      streamRef.current = mediaStream;
      setStream(mediaStream);
      setIsStreaming(true);
      toast.success('Camera started successfully');
    } catch (err) {
      setError('Camera access denied or unavailable');
      setIsStreaming(false);
      toast.error('Failed to access camera');
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setStream(null);
    setIsStreaming(false);
    toast.info('Camera stopped');
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
  }, []);

  const attachVideo = useCallback((video: HTMLVideoElement) => {
    if (streamRef.current && video) {
      video.srcObject = streamRef.current;
      video.muted = isMuted;
    }
  }, [isMuted]);

  return (
    <CameraContext.Provider value={{
      stream,
      isStreaming,
      isMuted,
      error,
      startCamera,
      stopCamera,
      toggleMute,
      videoRef,
      attachVideo,
    }}>
      {children}
    </CameraContext.Provider>
  );
}

export function useCamera() {
  const context = useContext(CameraContext);
  if (!context) {
    throw new Error('useCamera must be used within a CameraProvider');
  }
  return context;
}


