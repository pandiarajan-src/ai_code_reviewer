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
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ReviewRecord } from '../../types/types';

interface ReviewDetailsProps {
  review: ReviewRecord;
  open: boolean;
  onClose: () => void;
}

export default function ReviewDetails({ review, open, onClose }: ReviewDetailsProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Review Details - ID: {review.id}
        </Typography>
        <Button onClick={onClose} size="small" startIcon={<CloseIcon />}>
          Close
        </Button>
      </DialogTitle>

      <DialogContent dividers>
        {/* Metadata Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Metadata
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Created At
              </Typography>
              <Typography variant="body2">{formatDate(review.created_at)}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Review Type
              </Typography>
              <Box>
                <Chip label={review.review_type} size="small" color="primary" />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Trigger Type
              </Typography>
              <Box>
                <Chip label={review.trigger_type} size="small" />
              </Box>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Project Key
              </Typography>
              <Typography variant="body2">{review.project_key}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Repository
              </Typography>
              <Typography variant="body2">{review.repo_slug}</Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Author
              </Typography>
              <Typography variant="body2">{review.author_name || 'N/A'}</Typography>
            </Grid>
            {review.author_email && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Author Email
                </Typography>
                <Typography variant="body2">{review.author_email}</Typography>
              </Grid>
            )}
            {review.pr_id && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Pull Request ID
                </Typography>
                <Typography variant="body2">#{review.pr_id}</Typography>
              </Grid>
            )}
            {review.commit_id && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  Commit ID
                </Typography>
                <Typography variant="body2" fontFamily="monospace" fontSize="0.875rem">
                  {review.commit_id}
                </Typography>
              </Grid>
            )}
            <Grid item xs={12} sm={6} md={4}>
              <Typography variant="caption" color="text.secondary">
                Email Status
              </Typography>
              <Box>
                <Chip
                  label={review.email_sent ? 'Sent' : 'Not Sent'}
                  size="small"
                  color={review.email_sent ? 'success' : 'default'}
                />
              </Box>
            </Grid>
            {review.llm_provider && (
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="caption" color="text.secondary">
                  LLM Provider
                </Typography>
                <Typography variant="body2">
                  {review.llm_provider} ({review.llm_model})
                </Typography>
              </Grid>
            )}
          </Grid>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Diff Content Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Diff Content
          </Typography>
          <Box
            sx={{
              bgcolor: 'grey.900',
              color: 'common.white',
              p: 2,
              borderRadius: 2,
              overflow: 'auto',
              maxHeight: 300,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
            }}
          >
            {review.diff_content}
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Review Feedback Section */}
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
            Review Feedback
          </Typography>
          <Box
            sx={{
              '& h1': { fontSize: '1.5rem', fontWeight: 600, mt: 2, mb: 1.5 },
              '& h2': { fontSize: '1.25rem', fontWeight: 600, mt: 2, mb: 1.5 },
              '& h3': { fontSize: '1.1rem', fontWeight: 600, mt: 2, mb: 1 },
              '& p': { mb: 1.5, lineHeight: 1.7 },
              '& ul, & ol': { mb: 2, pl: 3 },
              '& li': { mb: 0.5 },
              '& code': {
                bgcolor: 'grey.100',
                px: 0.8,
                py: 0.4,
                borderRadius: 1,
                fontSize: '0.875rem',
                fontFamily: 'monospace',
              },
              '& pre': {
                bgcolor: 'grey.900',
                color: 'common.white',
                p: 2,
                borderRadius: 2,
                overflow: 'auto',
                '& code': {
                  bgcolor: 'transparent',
                  color: 'inherit',
                  px: 0,
                  py: 0,
                },
              },
            }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.review_feedback}</ReactMarkdown>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
