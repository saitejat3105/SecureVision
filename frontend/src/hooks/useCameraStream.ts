//useCameraStream.ts
import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface UseCameraStreamOptions {
  cameraId: string;
  enabled: boolean;
  frameRate?: number; // frames per second
}

export function useCameraStream({ cameraId, enabled, frameRate = 15 }: UseCameraStreamOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const lastFrameTime = useRef<number>(0);

  const fetchFrame = useCallback(async () => {
    if (!enabled || !canvasRef.current) return false;

    try {
      const response = await fetch(`${API_BASE}/api/camera/snapshot/${cameraId}?t=${Date.now()}`, {
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch frame');
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);

      return new Promise<boolean>((resolve) => {
        if (!imgRef.current) {
          imgRef.current = new Image();
        }

        imgRef.current.onload = () => {
          if (canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            if (ctx) {
              // Set canvas size to match image
              canvasRef.current.width = imgRef.current!.width;
              canvasRef.current.height = imgRef.current!.height;
              ctx.drawImage(imgRef.current!, 0, 0);
              setIsStreaming(true);
              setError(null);
            }
          }
          URL.revokeObjectURL(imageUrl);
          resolve(true);
        };

        imgRef.current.onerror = () => {
          URL.revokeObjectURL(imageUrl);
          resolve(false);
        };

        imgRef.current.src = imageUrl;
      });
    } catch (err) {
      return false;
    }
  }, [cameraId, enabled]);

  const startStreaming = useCallback(() => {
    if (!enabled) return;

    setIsLoading(true);
    setError(null);

    const frameInterval = 1000 / frameRate;

    const streamLoop = async (timestamp: number) => {
      if (!enabled) return;

      const elapsed = timestamp - lastFrameTime.current;

      if (elapsed >= frameInterval) {
        const success = await fetchFrame();
        if (!success) {
          setError('Stream interrupted');
        }
        lastFrameTime.current = timestamp;
        setIsLoading(false);
      }

      animationRef.current = requestAnimationFrame(streamLoop);
    };

    animationRef.current = requestAnimationFrame(streamLoop);
  }, [enabled, frameRate, fetchFrame]);

  const stopStreaming = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      startStreaming();
    } else {
      stopStreaming();
    }

    return () => {
      stopStreaming();
    };
  }, [enabled, startStreaming, stopStreaming]);

  const setCanvas = useCallback((canvas: HTMLCanvasElement | null) => {
    canvasRef.current = canvas;
  }, []);

  return {
    setCanvas,
    isLoading,
    error,
    isStreaming,
    retry: startStreaming,
  };
}
