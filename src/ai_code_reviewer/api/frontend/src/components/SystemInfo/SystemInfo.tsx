import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import api from '../../services/api';
import type { HealthResponse } from '../../types/types';

export default function SystemInfo() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getHealth();
      setHealth(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getStatusIcon = (status?: string) => {
    if (!status) return null;
    const isOk = status.toLowerCase() === 'ok' || status.toLowerCase() === 'healthy';
    return isOk ? (
      <CheckCircleIcon color="success" />
    ) : (
      <ErrorIcon color="error" />
    );
  };

  const getStatusColor = (status?: string) => {
    if (!status) return 'default';
    const isOk = status.toLowerCase() === 'ok' || status.toLowerCase() === 'healthy';
    return isOk ? 'success' : 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          System Configuration
        </Typography>
        <IconButton
          onClick={fetchHealth}
          disabled={loading}
          color="primary"
          title="Refresh"
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && !health ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : health ? (
        <Grid container spacing={3}>
          {/* Overall System Status */}
          <Grid item xs={12}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  {getStatusIcon(health.status)}
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      System Status
                    </Typography>
                    <Chip
                      label={health.status || 'Unknown'}
                      color={getStatusColor(health.status)}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Bitbucket Connection */}
          {health.bitbucket_connection !== undefined && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getStatusIcon(health.bitbucket_connection)}
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Bitbucket Connection
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                        {health.bitbucket_connection}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* LLM Status */}
          {health.llm_status !== undefined && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getStatusIcon(health.llm_status)}
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        LLM Provider
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                        {health.llm_status}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Application Version */}
          {health.version && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Application Version
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                    {health.version}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Timestamp */}
          {health.timestamp && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 600, mt: 1 }}>
                    {new Date(health.timestamp).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Information Notice */}
          <Grid item xs={12}>
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Note:</strong> This page displays system health and connection status only.
                Sensitive configuration details like API keys, webhook secrets, and internal URLs are
                not exposed for security reasons.
              </Typography>
            </Alert>
          </Grid>
        </Grid>
      ) : (
        <Alert severity="warning">No system information available</Alert>
      )}
    </Box>
  );
}
