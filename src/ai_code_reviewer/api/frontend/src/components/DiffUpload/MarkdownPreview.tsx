import { Card, CardContent, Typography, Box, Chip, Grid } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { DiffReviewResponse } from '../../types/types';

interface MarkdownPreviewProps {
  review: DiffReviewResponse;
}

export default function MarkdownPreview({ review }: MarkdownPreviewProps) {
  const { metadata } = review;

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        Review Results
      </Typography>

      {/* Metadata Card */}
      <Card elevation={1} sx={{ mb: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption" color="text.secondary">
                Filename
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {metadata.filename}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption" color="text.secondary">
                Lines Changed
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                <Chip
                  label={`+${metadata.lines_added}`}
                  size="small"
                  color="success"
                  sx={{ mr: 0.5 }}
                />
                <Chip
                  label={`-${metadata.lines_removed}`}
                  size="small"
                  color="error"
                />
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption" color="text.secondary">
                LLM Provider
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {metadata.llm_provider} ({metadata.llm_model})
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="caption" color="text.secondary">
                Processing Time
              </Typography>
              <Typography variant="body2" fontWeight={500}>
                {metadata.processing_time_seconds}s
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Markdown Review Content */}
      <Card elevation={2}>
        <CardContent>
          <Box
            sx={{
              '& h1': { fontSize: '1.75rem', fontWeight: 600, mt: 2, mb: 1.5 },
              '& h2': { fontSize: '1.5rem', fontWeight: 600, mt: 2, mb: 1.5 },
              '& h3': { fontSize: '1.25rem', fontWeight: 600, mt: 2, mb: 1 },
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
              '& blockquote': {
                borderLeft: '4px solid',
                borderColor: 'primary.main',
                pl: 2,
                ml: 0,
                fontStyle: 'italic',
                color: 'text.secondary',
              },
              '& table': {
                width: '100%',
                borderCollapse: 'collapse',
                mb: 2,
              },
              '& th, & td': {
                border: '1px solid',
                borderColor: 'divider',
                p: 1,
                textAlign: 'left',
              },
              '& th': {
                bgcolor: 'grey.100',
                fontWeight: 600,
              },
            }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {review.review_markdown}
            </ReactMarkdown>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
