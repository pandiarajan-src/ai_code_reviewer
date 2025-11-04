import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Chip,
  Divider,
  Alert,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import type { FailureRecord } from '../../types/types';

interface FailureDetailsProps {
  failure: FailureRecord;
  open: boolean;
  onClose: () => void;
}

export default function FailureDetails({ failure, open, onClose }: FailureDetailsProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Failure Details - ID: {failure.id}
        </Typography>
        <Button onClick={onClose} size="small" startIcon={<CloseIcon />}>
          Close
        </Button>
      </DialogTitle>

      <DialogContent dividers>
        {/* Metadata Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Failure Metadata
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Created At
              </Typography>
              <Typography variant="body2">{formatDate(failure.created_at)}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Event Type
              </Typography>
              <Box>
                <Chip label={failure.event_type} size="small" color="warning" />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Event Key
              </Typography>
              <Typography variant="body2">{failure.event_key}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Failure Stage
              </Typography>
              <Box>
                <Chip label={failure.failure_stage} size="small" color="error" />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Error Type
              </Typography>
              <Typography variant="body2">{failure.error_type}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Retry Count
              </Typography>
              <Typography variant="body2">{failure.retry_count}</Typography>
            </Grid>
            {failure.project_key && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Project Key
                </Typography>
                <Typography variant="body2">{failure.project_key}</Typography>
              </Grid>
            )}
            {failure.repo_slug && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Repository
                </Typography>
                <Typography variant="body2">{failure.repo_slug}</Typography>
              </Grid>
            )}
            {failure.author_name && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Author
                </Typography>
                <Typography variant="body2">{failure.author_name}</Typography>
              </Grid>
            )}
            {failure.pr_id && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Pull Request ID
                </Typography>
                <Typography variant="body2">#{failure.pr_id}</Typography>
              </Grid>
            )}
            {failure.commit_id && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Commit ID
                </Typography>
                <Typography variant="body2" fontFamily="monospace" fontSize="0.875rem">
                  {failure.commit_id}
                </Typography>
              </Grid>
            )}
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Status
              </Typography>
              <Box>
                <Chip
                  label={failure.resolved ? 'Resolved' : 'Unresolved'}
                  size="small"
                  color={failure.resolved ? 'success' : 'error'}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Error Message */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Error Message
          </Typography>
          <Alert severity="error" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
            {failure.error_message}
          </Alert>
        </Box>

        {/* Stacktrace */}
        {failure.error_stacktrace && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Stack Trace
              </Typography>
              <Box
                sx={{
                  bgcolor: 'grey.900',
                  color: 'common.white',
                  p: 2,
                  borderRadius: 2,
                  overflow: 'auto',
                  maxHeight: 400,
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {failure.error_stacktrace}
              </Box>
            </Box>
          </>
        )}

        {/* Request Payload */}
        {failure.request_payload && Object.keys(failure.request_payload).length > 0 && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Request Payload
              </Typography>
              <Box
                sx={{
                  bgcolor: 'grey.100',
                  p: 2,
                  borderRadius: 2,
                  overflow: 'auto',
                  maxHeight: 200,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                }}
              >
                <pre>{JSON.stringify(failure.request_payload, null, 2)}</pre>
              </Box>
            </Box>
          </>
        )}

        {/* Resolution Notes */}
        {failure.resolved && failure.resolution_notes && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Resolution Notes
              </Typography>
              <Alert severity="success">{failure.resolution_notes}</Alert>
            </Box>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
