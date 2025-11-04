import { Card, CardContent, Typography, Box, Alert, Chip } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { ManualReviewResponse } from '../../types/types';

interface ReviewResultProps {
  result: ManualReviewResponse;
}

export default function ReviewResult({ result }: ReviewResultProps) {
  if (result.status === 'no_diff') {
    return (
      <Alert severity="info" icon={<CheckCircleIcon />}>
        {result.message || 'No differences found to review'}
      </Alert>
    );
  }

  if (result.status === 'completed' && result.review) {
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Review Results
          </Typography>
          <Chip label="Completed" color="success" icon={<CheckCircleIcon />} />
          {result.record_id && (
            <Chip label={`Record ID: ${result.record_id}`} variant="outlined" size="small" />
          )}
        </Box>

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
              }}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.review}</ReactMarkdown>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Alert severity="warning">
      Review completed with unexpected status: {result.status}
    </Alert>
  );
}
