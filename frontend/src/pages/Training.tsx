//Training.tsx
import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import {
  Brain,
  Play,
  Pause,
  RefreshCw,
  CheckCircle,
  Clock,
  TrendingUp,
  Layers,
  Cpu,
  Database,
} from 'lucide-react';
import { TrainingStatus } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const models = [
  { id: 'face_cnn', name: 'Face Recognition CNN', description: 'Custom CNN for face identification', accuracy: 94.5 },
  { id: 'face_svm', name: 'Face Recognition SVM', description: 'SVM classifier with HOG features', accuracy: 89.2 },
  { id: 'face_knn', name: 'Face Recognition KNN', description: 'K-Nearest Neighbors classifier', accuracy: 86.8 },
  { id: 'yolov8', name: 'YOLOv8 Person Detection', description: 'Real-time person detection', accuracy: 97.1 },
  { id: 'weapon', name: 'Weapon Detection', description: 'YOLOv8 trained on weapons', accuracy: 92.3 },
  { id: 'mask', name: 'Mask Detection', description: 'CNN for masked face detection', accuracy: 95.7 },
  { id: 'anomaly', name: 'Anomaly Detection', description: 'Autoencoder for scene anomalies', accuracy: 88.9 },
  { id: 'pose', name: 'Pose Estimation', description: 'MediaPipe pose detection', accuracy: 91.4 },
];

export default function Training() {
  const { user } = useAuth();
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus>({
    isTraining: false,
    progress: 0,
    currentModel: '',
    lastTrained: new Date(Date.now() - 86400000).toISOString(),
    accuracy: 92.5,
  });
  const [modelStats, setModelStats] = useState<Record<string, { accuracy: number; status: string }>>({});

  useEffect(() => {
    // Initialize model stats with defaults
    const stats: Record<string, { accuracy: number; status: string }> = {};
    models.forEach(model => {
      stats[model.id] = { accuracy: model.accuracy, status: 'ready' };
    });
    setModelStats(stats);
  }, []);

  const fetchTrainingStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/training/status/${user?.id}`);
      if (response.ok) {
        const data = await response.json();
        if (data.models) {
          const updatedStats: Record<string, { accuracy: number; status: string }> = {};
          data.models.forEach((m: { id: string; accuracy: number; status: string }) => {
            updatedStats[m.id] = { accuracy: m.accuracy, status: m.status };
          });
          setModelStats(updatedStats);
        }
        if (data.avgAccuracy) {
          setTrainingStatus(prev => ({ ...prev, accuracy: data.avgAccuracy }));
        }
      }
    } catch (error) {
      console.log('Using default model stats');
    }
  };

  useEffect(() => {
    fetchTrainingStatus();
  }, [user?.id]);

  const startTraining = async (modelId?: string) => {
    setTrainingStatus(prev => ({
      ...prev,
      isTraining: true,
      progress: 0,
      currentModel: modelId || 'all',
    }));

    try {
      const response = await fetch(`${API_BASE}/api/training/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user?.id, modelId }),
      });

      if (response.ok) {
        // Poll for progress
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(`${API_BASE}/api/training/progress/${user?.id}`);
            if (statusRes.ok) {
              const status = await statusRes.json();
              setTrainingStatus(prev => ({
                ...prev,
                progress: status.progress || prev.progress,
              }));
              
              if (status.progress >= 100 || status.completed) {
                clearInterval(pollInterval);
                setTrainingStatus(prev => ({
                  ...prev,
                  isTraining: false,
                  progress: 100,
                  lastTrained: new Date().toISOString(),
                  accuracy: status.accuracy || prev.accuracy,
                }));
                fetchTrainingStatus(); // Refresh model stats
                toast.success('Training completed!');
              }
            }
          } catch {
            // Continue polling
          }
        }, 2000);

        // Timeout after 5 minutes
        setTimeout(() => clearInterval(pollInterval), 300000);
      }
    } catch (error) {
      // Fallback to simulation if backend unavailable
      const interval = setInterval(() => {
        setTrainingStatus(prev => {
          if (prev.progress >= 100) {
            clearInterval(interval);
            toast.success('Training completed (simulated)');
            return {
              ...prev,
              isTraining: false,
              progress: 100,
              lastTrained: new Date().toISOString(),
            };
          }
          return { ...prev, progress: prev.progress + 10 };
        });
      }, 500);
    }
  };

  const stopTraining = () => {
    setTrainingStatus(prev => ({ ...prev, isTraining: false, progress: 0 }));
    toast.info('Training stopped');
  };

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Model Training</h1>
            <p className="text-muted-foreground mt-1">
              Train and manage your ML models
            </p>
          </div>
          <div className="flex gap-3">
            {trainingStatus.isTraining ? (
              <Button variant="destructive" onClick={stopTraining}>
                <Pause className="w-4 h-4 mr-2" />
                Stop Training
              </Button>
            ) : (
              <Button onClick={() => startTraining()}>
                <Play className="w-4 h-4 mr-2" />
                Train All Models
              </Button>
            )}
          </div>
        </div>

        {/* Training Status */}
        {trainingStatus.isTraining && (
          <Card variant="glass" className="border-primary/30">
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center">
                  <Brain className="w-6 h-6 text-primary-foreground animate-pulse" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground">Training in Progress</h3>
                  <p className="text-sm text-muted-foreground">
                    Training: {trainingStatus.currentModel === 'all' ? 'All Models' : trainingStatus.currentModel}
                  </p>
                </div>
                <span className="text-2xl font-bold text-primary">{trainingStatus.progress}%</span>
              </div>
              <div className="w-full h-3 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full gradient-primary rounded-full transition-all duration-300"
                  style={{ width: `${trainingStatus.progress}%` }}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card variant="glass">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Active Models</p>
                  <p className="text-xl font-bold text-foreground">{models.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-success" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg Accuracy</p>
                  <p className="text-xl font-bold text-success">{trainingStatus.accuracy}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Last Trained</p>
                  <p className="text-sm font-medium text-foreground">
                    {new Date(trainingStatus.lastTrained).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card variant="glass">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                  <Database className="w-5 h-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Training Data</p>
                  <p className="text-xl font-bold text-foreground">2.4k</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Models Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {models.map((model) => (
            <Card key={model.id} variant="glass" className="hover:border-primary/30 transition-colors">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Layers className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{model.name}</h3>
                      <p className="text-sm text-muted-foreground">{model.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success" />
                    <span className="text-sm font-medium text-success">Ready</span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Accuracy</span>
                    <span className="font-medium text-foreground">
                      {modelStats[model.id]?.accuracy ?? model.accuracy}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        (modelStats[model.id]?.accuracy ?? model.accuracy) >= 95 ? 'bg-success' :
                        (modelStats[model.id]?.accuracy ?? model.accuracy) >= 90 ? 'gradient-primary' :
                        'bg-warning'
                      }`}
                      style={{ width: `${modelStats[model.id]?.accuracy ?? model.accuracy}%` }}
                    />
                  </div>
                </div>

                <div className="flex gap-2 mt-4 pt-4 border-t border-border/50">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => startTraining(model.id)}
                    disabled={trainingStatus.isTraining}
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Retrain
                  </Button>
                  <Button variant="ghost" size="sm">
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Training Info */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Incremental Learning</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-foreground">Frozen Layers</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-muted" />
                    Base CNN layers (feature extraction)
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-muted" />
                    YOLO backbone weights
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-muted" />
                    Pretrained embeddings
                  </li>
                </ul>
              </div>
              <div className="space-y-4">
                <h4 className="font-medium text-foreground">Trainable Layers</h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    Classification head (new faces)
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    Fine-tuning layers
                  </li>
                  <li className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                    Embedding projection
                  </li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
