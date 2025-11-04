import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import api from '../../services/api';
import type { ReviewRecord } from '../../types/types';
import Pagination from './Pagination';
import ReviewDetails from './ReviewDetails';

const ITEMS_PER_PAGE = 25;

export default function ReviewsTable() {
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedReview, setSelectedReview] = useState<ReviewRecord | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const fetchReviews = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const offset = pageNum * ITEMS_PER_PAGE;
      const response = await api.getReviews(offset, ITEMS_PER_PAGE);
      setReviews(response.records);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch reviews');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews(page);
  }, [page]);

  const handleViewDetails = async (review: ReviewRecord) => {
    setSelectedReview(review);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedReview(null);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const truncate = (text: string, maxLength: number) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Successful Reviews
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card elevation={2}>
        <TableContainer>
          <Table>
            <TableHead sx={{ bgcolor: 'grey.100' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>ID</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Created At</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Trigger</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Project</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Repository</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Author</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>PR/Commit</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Email</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : reviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">No reviews found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                reviews.map((review) => (
                  <TableRow key={review.id} hover>
                    <TableCell>{review.id}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {formatDate(review.created_at)}
                    </TableCell>
                    <TableCell>
                      <Chip label={review.review_type} size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip label={review.trigger_type} size="small" />
                    </TableCell>
                    <TableCell>{review.project_key}</TableCell>
                    <TableCell>{truncate(review.repo_slug, 20)}</TableCell>
                    <TableCell>{truncate(review.author_name || 'N/A', 20)}</TableCell>
                    <TableCell>
                      {review.pr_id ? `PR #${review.pr_id}` : review.commit_id ? truncate(review.commit_id, 10) : 'N/A'}
                    </TableCell>
                    <TableCell>
                      {review.email_sent ? (
                        <Chip label="Sent" size="small" color="success" />
                      ) : (
                        <Chip label="Not Sent" size="small" color="default" />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleViewDetails(review)}
                        title="View details"
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {!loading && reviews.length > 0 && (
          <Box sx={{ p: 2 }}>
            <Pagination
              total={total}
              page={page}
              itemsPerPage={ITEMS_PER_PAGE}
              onPageChange={setPage}
            />
          </Box>
        )}
      </Card>

      {/* Details Modal */}
      {selectedReview && (
        <ReviewDetails
          review={selectedReview}
          open={detailsOpen}
          onClose={handleCloseDetails}
        />
      )}
    </Box>
  );
}
