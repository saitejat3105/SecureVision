//KnownFaces.tsx
import { useState, useEffect, useRef } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import {
  Users,
  Plus,
  Camera,
  Trash2,
  Edit,
  Image,
  StopCircle,
  Play,
  Save,
  X,
} from 'lucide-react';
import { KnownPerson } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function KnownFaces() {
  const { user } = useAuth();
  const [people, setPeople] = useState<KnownPerson[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [newPersonName, setNewPersonName] = useState('');
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [captureInterval, setCaptureInterval] = useState<NodeJS.Timeout | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    fetchPeople();
    return () => {
      stopCapturing();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [user?.cameraId]);

  const fetchPeople = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/faces/${user?.id}`);
      if (response.ok) {
        const data = await response.json();
        setPeople(data.faces || []);
      } else {
        setPeople([]);
      }
    } catch (error) {
      // Backend offline - show empty state
      console.log('Backend offline, no faces data available');
      setPeople([]);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 640, height: 480 }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      return true;
    } catch (error) {
      toast.error('Failed to access camera');
      return false;
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) {
        canvasRef.current.width = videoRef.current.videoWidth;
        canvasRef.current.height = videoRef.current.videoHeight;
        ctx.drawImage(videoRef.current, 0, 0);
        const imageData = canvasRef.current.toDataURL('image/jpeg', 0.8);
        setCapturedImages(prev => [...prev, imageData]);
        return imageData;
      }
    }
    return null;
  };

  const startCapturing = async () => {
    if (!newPersonName.trim()) {
      toast.error('Please enter a name first');
      return;
    }

    const started = await startCamera();
    if (!started) return;

    setIsCapturing(true);
    setCapturedImages([]);

    // Auto-capture every 2 seconds
    const interval = setInterval(() => {
      const image = captureImage();
      if (image) {
        toast.info(`Captured image ${capturedImages.length + 1}`);
      }
    }, 2000);

    setCaptureInterval(interval);
    toast.success('Auto-capture started (every 2 seconds)');
  };

  const stopCapturing = () => {
    if (captureInterval) {
      clearInterval(captureInterval);
      setCaptureInterval(null);
    }
    setIsCapturing(false);
    stopCamera();
    toast.info(`Captured ${capturedImages.length} images`);
  };

  const manualCapture = () => {
    const image = captureImage();
    if (image) {
      toast.success('Image captured!');
    }
  };

  const savePerson = async () => {
    if (capturedImages.length < 5) {
      toast.error('Please capture at least 5 images');
      return;
    }

    try {
      // Send images to backend - will save to data/train and data/test folders
      const response = await fetch(`${API_BASE}/api/faces/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user?.id,
          name: newPersonName,
          images: capturedImages, // Base64 images to save in data folder
        }),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`${newPersonName} added successfully! Images saved to data folder.`);
        setShowAddModal(false);
        setNewPersonName('');
        setCapturedImages([]);
        stopCapturing();
        fetchPeople();
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to save person');
      }
    } catch (error) {
      toast.error('Backend offline - cannot save to data folder');
    }
  };

  const deletePerson = async (personId: string, name: string) => {
    try {
      // Delete from backend - removes images from data/train and data/test folders
      const response = await fetch(`${API_BASE}/api/faces/${personId}`, { 
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        setPeople(prev => prev.filter(p => p.id !== personId));
        toast.success(`${name} removed from data folder`);
      } else {
        toast.error('Failed to delete from backend');
      }
    } catch (error) {
      toast.error('Backend offline - cannot delete');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Known Faces</h1>
            <p className="text-muted-foreground mt-1">
              {people.length} people registered
            </p>
          </div>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add New Person
          </Button>
        </div>

        {/* Add Person Modal */}
        {showAddModal && (
          <Card variant="glass" className="border-primary/30">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-primary" />
                Add New Person
              </CardTitle>
              <Button variant="ghost" size="icon-sm" onClick={() => {
                setShowAddModal(false);
                stopCapturing();
                setCapturedImages([]);
                setNewPersonName('');
              }}>
                <X className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Person Name</label>
                <Input
                  placeholder="Enter name (e.g., John Doe)"
                  value={newPersonName}
                  onChange={(e) => setNewPersonName(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Camera View */}
                <div className="space-y-4">
                  <div className="aspect-video bg-muted rounded-lg overflow-hidden relative">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                    {!streamRef.current && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Camera className="w-12 h-12 text-muted-foreground" />
                      </div>
                    )}
                    {isCapturing && (
                      <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-danger/90 text-danger-foreground text-sm font-medium">
                        <div className="w-2 h-2 rounded-full bg-danger-foreground animate-pulse" />
                        Recording
                      </div>
                    )}
                  </div>
                  <canvas ref={canvasRef} className="hidden" />
                  
                  <div className="flex gap-2">
                    {!isCapturing ? (
                      <Button onClick={startCapturing} className="flex-1">
                        <Play className="w-4 h-4 mr-2" />
                        Start Auto-Capture
                      </Button>
                    ) : (
                      <>
                        <Button variant="outline" onClick={manualCapture} className="flex-1">
                          <Camera className="w-4 h-4 mr-2" />
                          Manual Capture
                        </Button>
                        <Button variant="destructive" onClick={stopCapturing} className="flex-1">
                          <StopCircle className="w-4 h-4 mr-2" />
                          Stop
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                {/* Captured Images */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">
                      Captured Images ({capturedImages.length})
                    </span>
                    {capturedImages.length > 0 && (
                      <Button variant="ghost" size="sm" onClick={() => setCapturedImages([])}>
                        Clear All
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-4 gap-2 max-h-60 overflow-y-auto scrollbar-thin">
                    {capturedImages.map((img, index) => (
                      <div key={index} className="aspect-square rounded-lg overflow-hidden bg-muted relative group">
                        <img src={img} alt={`Capture ${index + 1}`} className="w-full h-full object-cover" />
                        <button
                          className="absolute inset-0 bg-danger/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => setCapturedImages(prev => prev.filter((_, i) => i !== index))}
                        >
                          <Trash2 className="w-4 h-4 text-danger-foreground" />
                        </button>
                      </div>
                    ))}
                    {capturedImages.length === 0 && (
                      <div className="col-span-4 py-8 text-center text-muted-foreground">
                        <Image className="w-8 h-8 mx-auto mb-2" />
                        <p className="text-sm">No images captured yet</p>
                      </div>
                    )}
                  </div>
                  
                  <Button
                    onClick={savePerson}
                    disabled={capturedImages.length < 5 || !newPersonName.trim()}
                    className="w-full"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Person ({capturedImages.length}/5 min)
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* People Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {people.map((person) => (
            <Card key={person.id} variant="glass" className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-2xl font-bold text-primary">
                      {person.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground truncate">{person.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {person.imageCount} images
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Updated: {new Date(person.lastUpdated).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2 mt-4 pt-4 border-t border-border/50">
                  <Button variant="ghost" size="sm" className="flex-1">
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-danger hover:text-danger"
                    onClick={() => deletePerson(person.id, person.name)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {people.length === 0 && (
          <Card variant="glass" className="p-12 text-center">
            <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold text-foreground">No People Registered</h3>
            <p className="text-muted-foreground mt-1">
              Add known faces to help the system recognize family members.
            </p>
            <Button className="mt-4" onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add First Person
            </Button>
          </Card>
        )}
      </div>
    </MainLayout>
  );
}
