import { useState } from 'react';
import {
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Grid,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ClearIcon from '@mui/icons-material/Clear';
import DownloadIcon from '@mui/icons-material/Download';
import api from '../../services/api';
import type { ManualReviewResponse } from '../../types/types';
import ReviewResult from './ReviewResult';

export default function ManualReviewForm() {
  const [projectKey, setProjectKey] = useState('');
  const [repoSlug, setRepoSlug] = useState('');
  const [reviewTarget, setReviewTarget] = useState<'pr' | 'commit'>('pr');
  const [prId, setPrId] = useState('');
  const [commitId, setCommitId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ManualReviewResponse | null>(null);

  const handleSubmit = async () => {
    // Validation
    if (!projectKey.trim() || !repoSlug.trim()) {
      setError('Project Key and Repository Slug are required');
      return;
    }

    if (reviewTarget === 'pr' && !prId.trim()) {
      setError('Pull Request ID is required');
      return;
    }

    if (reviewTarget === 'commit' && !commitId.trim()) {
      setError('Commit ID is required');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.triggerManualReview({
        project_key: projectKey,
        repo_slug: repoSlug,
        pr_id: reviewTarget === 'pr' ? parseInt(prId, 10) : undefined,
        commit_id: reviewTarget === 'commit' ? commitId : undefined,
      });
      setResult(response);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger review';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setProjectKey('');
    setRepoSlug('');
    setPrId('');
    setCommitId('');
    setError(null);
    setResult(null);
    setReviewTarget('pr');
  };

  const handleDownload = () => {
    if (!result || !result.review) return;
    const blob = new Blob([result.review], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `manual-review-${projectKey}-${repoSlug}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Manual Code Review
      </Typography>

      <Card elevation={2}>
        <CardContent>
          <Grid container spacing={3}>
            {/* Project and Repo */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Project Key"
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value)}
                variant="outlined"
                placeholder="e.g., MYPROJECT"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Repository Slug"
                value={repoSlug}
                onChange={(e) => setRepoSlug(e.target.value)}
                variant="outlined"
                placeholder="e.g., my-repo"
              />
            </Grid>

            {/* Review Target Selection */}
            <Grid item xs={12}>
              <FormControl component="fieldset">
                <FormLabel component="legend">Review Target</FormLabel>
                <RadioGroup
                  row
                  value={reviewTarget}
                  onChange={(e) => setReviewTarget(e.target.value as 'pr' | 'commit')}
                >
                  <FormControlLabel value="pr" control={<Radio />} label="Pull Request" />
                  <FormControlLabel value="commit" control={<Radio />} label="Commit" />
                </RadioGroup>
              </FormControl>
            </Grid>

            {/* PR ID or Commit ID */}
            {reviewTarget === 'pr' ? (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Pull Request ID"
                  value={prId}
                  onChange={(e) => setPrId(e.target.value)}
                  variant="outlined"
                  type="number"
                  placeholder="e.g., 123"
                />
              </Grid>
            ) : (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Commit ID"
                  value={commitId}
                  onChange={(e) => setCommitId(e.target.value)}
                  variant="outlined"
                  placeholder="e.g., abc123def456"
                />
              </Grid>
            )}

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleSubmit}
                  disabled={loading}
                  startIcon={<PlayArrowIcon />}
                >
                  {loading ? 'Reviewing...' : 'Trigger Review'}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={handleClear}
                  disabled={loading}
                  startIcon={<ClearIcon />}
                >
                  Clear
                </Button>
                {result && result.review && (
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={handleDownload}
                    startIcon={<DownloadIcon />}
                  >
                    Download
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>

          {/* Progress Bar */}
          {loading && (
            <Box sx={{ mt: 3 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Fetching diff from Bitbucket and reviewing with AI...
              </Typography>
            </Box>
          )}

          {/* Error Message */}
          {error && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {error}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Box sx={{ mt: 4 }}>
          <ReviewResult result={result} />
        </Box>
      )}
    </Box>
  );
}
