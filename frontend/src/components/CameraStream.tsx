//CameraStream.tsx
import { useRef, useEffect, useState, useCallback } from 'react';
import { RefreshCw, Camera, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface CameraStreamProps {
  cameraId: string;
  isActive: boolean;
  isNightMode?: boolean;
  className?: string;
}

export function CameraStream({ cameraId, isActive, isNightMode, className }: CameraStreamProps) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);

  const fetchFrame = useCallback(async () => {
    if (!isActive || !cameraId) return;

    try {
      // Fetch snapshot with cache-busting timestamp
      const response = await fetch(`${API_BASE}/api/camera/snapshot/${cameraId}?t=${Date.now()}`, {
        method: 'GET',
        mode: 'cors',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      
      // Revoke previous object URL to prevent memory leaks
      if (imageSrc && imageSrc.startsWith('blob:')) {
        URL.revokeObjectURL(imageSrc);
      }

      const newImageUrl = URL.createObjectURL(blob);
      setImageSrc(newImageUrl);
      setIsLoading(false);
      setHasError(false);
      retryCountRef.current = 0;
    } catch (error) {
      console.error('Failed to fetch frame:', error);
      retryCountRef.current++;
      
      if (retryCountRef.current >= 5) {
        setHasError(true);
        setIsLoading(false);
        setErrorMessage(error instanceof Error ? error.message : 'Connection failed');
        // Stop polling on repeated failures
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    }
  }, [isActive, cameraId, imageSrc]);

  const startPolling = useCallback(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    retryCountRef.current = 0;
    setIsLoading(true);
    setHasError(false);
    
    // Fetch immediately
    fetchFrame();
    
    // Then poll every 100ms (~10 FPS)
    intervalRef.current = setInterval(fetchFrame, 100);
  }, [fetchFrame]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    // Clean up blob URL
    if (imageSrc && imageSrc.startsWith('blob:')) {
      URL.revokeObjectURL(imageSrc);
    }
    setImageSrc(null);
    setIsLoading(true);
    setHasError(false);
  }, [imageSrc]);

  useEffect(() => {
    if (isActive && cameraId) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [isActive, cameraId]);

  const handleRetry = () => {
    retryCountRef.current = 0;
    startPolling();
  };

  if (!isActive) {
    return (
      <div className={`flex items-center justify-center bg-background ${className}`}>
        <div className="text-center">
          <Camera className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
          <p className="text-muted-foreground text-lg">Camera is offline</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Camera Feed Image */}
      {imageSrc && !hasError && (
        <img
          src={imageSrc}
          alt="Live camera feed"
          className={`w-full h-full object-contain ${isNightMode ? 'brightness-150 contrast-125' : ''}`}
        />
      )}

      {/* Loading state */}
      {isLoading && !hasError && !imageSrc && (
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 mx-auto mb-2 text-primary animate-spin" />
            <p className="text-muted-foreground">Connecting to camera...</p>
            <p className="text-muted-foreground/60 text-xs mt-2">
              Fetching video frames...
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 mx-auto mb-3 text-destructive" />
            <p className="text-muted-foreground mb-2">Failed to connect to camera stream</p>
            <p className="text-muted-foreground/70 text-xs mb-2 max-w-xs">
              {errorMessage}
            </p>
            <p className="text-muted-foreground/70 text-xs mb-4 max-w-xs">
              Backend needs: /api/camera/snapshot/{'{camera_id}'} endpoint returning JPEG image
            </p>
            <Button onClick={handleRetry} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry Connection
            </Button>
          </div>
        </div>
      )}

      {/* Live indicator */}
      {!isLoading && !hasError && imageSrc && (
        <div className="absolute top-2 left-2 flex items-center gap-2 px-2 py-1 bg-background/80 rounded text-xs">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-muted-foreground">Live</span>
        </div>
      )}

      {/* Night mode overlay */}
      {isNightMode && !hasError && (
        <div className="absolute inset-0 bg-emerald-900/10 pointer-events-none mix-blend-overlay" />
      )}
    </div>
  );
}
