//IntruderLogs.tsx
import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import {
  AlertTriangle,
  Calendar,
  Clock,
  Search,
  Filter,
  Download,
  Trash2,
  Image,
  ChevronLeft,
  ChevronRight,
  Eye,
} from 'lucide-react';
import { IntruderLog } from '@/types/security';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function IntruderLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<IntruderLog[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLog, setSelectedLog] = useState<IntruderLog | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [filterType, setFilterType] = useState<string>('all');
  const logsPerPage = 10;

  useEffect(() => {
    fetchLogs();
  }, [user?.cameraId]);

  const fetchLogs = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/intruder-logs/${user?.cameraId}`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      } else {
        setLogs([]);
      }
    } catch (error) {
      // Backend offline - show empty state
      console.log('Backend offline, no intruder logs available');
      setLogs([]);
    }
  };

  const handleDeleteLog = async (logId: string) => {
    try {
      await fetch(`${API_BASE}/api/intruder-logs/${logId}`, { method: 'DELETE' });
      setLogs(logs.filter(log => log.id !== logId));
      toast.success('Log deleted');
    } catch (error) {
      toast.error('Failed to delete log');
    }
  };

  const handleClearOldLogs = async () => {
    try {
      await fetch(`${API_BASE}/api/intruder-logs/clear-old`, { method: 'POST' });
      toast.success('Old logs cleared');
      fetchLogs();
    } catch (error) {
      toast.error('Failed to clear old logs');
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.details.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterType === 'all' || log.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const paginatedLogs = filteredLogs.slice(
    (currentPage - 1) * logsPerPage,
    currentPage * logsPerPage
  );

  const totalPages = Math.ceil(filteredLogs.length / logsPerPage);

  const getSeverityColor = (severity: number) => {
    if (severity >= 8) return 'bg-danger/20 text-danger border-danger/50';
    if (severity >= 5) return 'bg-warning/20 text-warning border-warning/50';
    return 'bg-muted text-muted-foreground border-border';
  };

  const getTypeIcon = (type: IntruderLog['type']) => {
    switch (type) {
      case 'weapon_detected':
        return '⚠️';
      case 'masked_person':
        return '🎭';
      case 'recurring_intruder':
        return '🔄';
      case 'anomaly':
        return '❓';
      default:
        return '👤';
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Intruder Logs</h1>
            <p className="text-muted-foreground mt-1">
              {filteredLogs.length} events recorded
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={handleClearOldLogs}>
              <Trash2 className="w-4 h-4 mr-2" />
              Clear Old Logs
            </Button>
            <Button variant="default">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card variant="glass">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                {['all', 'unknown_person', 'masked_person', 'weapon_detected', 'recurring_intruder'].map((type) => (
                  <Button
                    key={type}
                    variant={filterType === type ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFilterType(type)}
                  >
                    {type === 'all' ? 'All' : type.replace('_', ' ')}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Logs Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {paginatedLogs.map((log) => (
            <Card
              key={log.id}
              variant="glass"
              className={`cursor-pointer transition-all hover:scale-[1.01] ${
                selectedLog?.id === log.id ? 'ring-2 ring-primary' : ''
              } ${getSeverityColor(log.severity)}`}
              onClick={() => setSelectedLog(log)}
            >
              <CardContent className="p-4">
                <div className="flex gap-4">
                  <div className="w-24 h-24 rounded-lg bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
                    <Image className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getTypeIcon(log.type)}</span>
                        <h3 className="font-semibold text-foreground truncate">
                          {log.type.replace('_', ' ')}
                        </h3>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        log.severity >= 8 ? 'bg-danger text-danger-foreground' :
                        log.severity >= 5 ? 'bg-warning text-warning-foreground' :
                        'bg-muted text-muted-foreground'
                      }`}>
                        {log.severity}/10
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {log.details}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(log.timestamp).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span>Confidence: {(log.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-4 pt-4 border-t border-border/50">
                  <Button variant="ghost" size="sm" className="flex-1">
                    <Eye className="w-4 h-4 mr-1" />
                    View Details
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-danger hover:text-danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteLog(log.id);
                    }}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}

        {filteredLogs.length === 0 && (
          <Card variant="glass" className="p-12 text-center">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold text-foreground">No Logs Found</h3>
            <p className="text-muted-foreground mt-1">
              No intruder events match your search criteria.
            </p>
          </Card>
        )}
      </div>
    </MainLayout>
  );
}
