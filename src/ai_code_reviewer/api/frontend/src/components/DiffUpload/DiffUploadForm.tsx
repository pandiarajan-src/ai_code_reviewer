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
} from '@mui/material';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import ClearIcon from '@mui/icons-material/Clear';
import DownloadIcon from '@mui/icons-material/Download';
import api from '../../services/api';
import type { DiffReviewResponse } from '../../types/types';
import MarkdownPreview from './MarkdownPreview';

export default function DiffUploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [projectKey, setProjectKey] = useState('MANUAL');
  const [repoSlug, setRepoSlug] = useState('diff-upload');
  const [authorName, setAuthorName] = useState('Anonymous');
  const [authorEmail, setAuthorEmail] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiffReviewResponse | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      // Validate file extension
      if (!selectedFile.name.endsWith('.diff') && !selectedFile.name.endsWith('.patch')) {
        setError('Please select a .diff or .patch file');
        return;
      }
      // Validate file size (10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.uploadDiffForReview({
        file,
        project_key: projectKey,
        repo_slug: repoSlug,
        author_name: authorName,
        author_email: authorEmail || undefined,
        description: description || undefined,
      });
      setResult(response);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to review diff';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setError(null);
    setResult(null);
    setProjectKey('MANUAL');
    setRepoSlug('diff-upload');
    setAuthorName('Anonymous');
    setAuthorEmail('');
    setDescription('');
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.review_markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code-review-${result.metadata.filename}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Upload Diff File for Review
      </Typography>

      <Card elevation={2}>
        <CardContent>
          <Grid container spacing={3}>
            {/* File Upload */}
            <Grid item xs={12}>
              <Box
                sx={{
                  border: '2px solid',
                  borderColor: file ? 'success.main' : 'grey.300',
                  borderRadius: 3,
                  p: 4,
                  textAlign: 'center',
                  bgcolor: file ? 'success.50' : 'background.paper',
                  boxShadow: file ? 2 : 1,
                }}
              >
                <input
                  type="file"
                  hidden
                  accept=".diff,.patch"
                  onChange={handleFileChange}
                  id="file-upload-input"
                  style={{ display: 'none' }}
                />
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                  <UploadFileIcon sx={{ fontSize: 64, color: file ? 'success.main' : 'primary.main' }} />

                  {file ? (
                    <>
                      <Typography variant="h6" color="success.main" sx={{ fontWeight: 600 }}>
                        {file.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Size: {(file.size / 1024).toFixed(2)} KB
                      </Typography>
                      <Button
                        variant="outlined"
                        color="primary"
                        component="label"
                        htmlFor="file-upload-input"
                        startIcon={<UploadFileIcon />}
                      >
                        Change File
                      </Button>
                    </>
                  ) : (
                    <>
                      <Typography variant="h6" sx={{ fontWeight: 500, mb: 1 }}>
                        Select a diff file to review
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Accepts .diff or .patch files (max 10MB)
                      </Typography>
                      <Button
                        variant="contained"
                        size="large"
                        component="label"
                        htmlFor="file-upload-input"
                        startIcon={<UploadFileIcon />}
                      >
                        Choose File
                      </Button>
                    </>
                  )}
                </Box>
              </Box>
            </Grid>

            {/* Form Fields */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Project Key"
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Repository Slug"
                value={repoSlug}
                onChange={(e) => setRepoSlug(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Author Name"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Author Email (Optional)"
                value={authorEmail}
                onChange={(e) => setAuthorEmail(e.target.value)}
                variant="outlined"
                type="email"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (Optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                variant="outlined"
                multiline
                rows={3}
                placeholder="Provide context about these changes..."
              />
            </Grid>

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleSubmit}
                  disabled={!file || loading}
                  startIcon={<UploadFileIcon />}
                >
                  {loading ? 'Reviewing...' : 'Review Code'}
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
                {result && (
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={handleDownload}
                    startIcon={<DownloadIcon />}
                  >
                    Download Report
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
                AI is reviewing your code changes...
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
          <MarkdownPreview review={result} />
        </Box>
      )}
    </Box>
  );
}
