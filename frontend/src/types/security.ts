//security.ts
export interface User {
  id: string;
  username: string;
  email: string;
  cameraId: string;
  createdAt: string;
}

export interface Camera {
  id: string;
  name: string;
  userId: string;
  status: 'online' | 'offline' | 'error';
  lastSeen: string;
}

export interface IntruderLog {
  id: string;
  cameraId: string;
  timestamp: string;
  imagePath: string;
  confidence: number;
  severity: number;
  type: 'unknown_person' | 'weapon_detected' | 'masked_person' | 'anomaly' | 'recurring_intruder';
  details: string;
  personName?: string;
  vehiclePlate?: string;
}

export interface KnownPerson {
  id: string;
  name: string;
  imageCount: number;
  lastUpdated: string;
  userId: string;
}

export interface SystemSettings {
  dndEnabled: boolean;
  dndStart: string;
  dndEnd: string;
  cameraEnabled: boolean;
  emailAlertsEnabled: boolean;
  alarmEnabled: boolean;
  nightModeAuto: boolean;
  sensitivity: number;
  alertCooldown: number;
}

export interface TrainingStatus {
  isTraining: boolean;
  progress: number;
  currentModel: string;
  lastTrained: string;
  accuracy: number;
}

export interface DetectionResult {
  name: string;
  confidence: number;
  isIntruder: boolean;
  boundingBox: { x: number; y: number; w: number; h: number };
  additionalInfo?: {
    masked?: boolean;
    weapon?: boolean;
    pose?: string;
    vehiclePlate?: string;
  };
}

export interface SecurityStats {
  totalIntruders: number;
  totalVisitors: number;
  alertsToday: number;
  uptime: number;
  modelsActive: number;
}

export interface VoiceMessage {
  id: string;
  type: 'incoming' | 'outgoing';
  timestamp: string;
  duration: number;
  audioUrl?: string;
}
