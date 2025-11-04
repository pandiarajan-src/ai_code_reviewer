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
import type { FailureRecord } from '../../types/types';
import Pagination from '../ReviewsTable/Pagination';
import FailureDetails from './FailureDetails';

const ITEMS_PER_PAGE = 25;

export default function FailuresTable() {
  const [failures, setFailures] = useState<FailureRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFailure, setSelectedFailure] = useState<FailureRecord | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const fetchFailures = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const offset = pageNum * ITEMS_PER_PAGE;
      const response = await api.getFailures(offset, ITEMS_PER_PAGE);
      setFailures(response.failures);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch failures');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFailures(page);
  }, [page]);

  const handleViewDetails = async (failure: FailureRecord) => {
    try {
      // Fetch full details including stacktrace
      const fullDetails = await api.getFailureById(failure.id);
      setSelectedFailure(fullDetails);
      setDetailsOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch failure details');
    }
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedFailure(null);
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
        Failed Reviews
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
                <TableCell sx={{ fontWeight: 600 }}>Event Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Event Key</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Stage</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Error Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Project</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Repository</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
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
              ) : failures.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">No failures found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                failures.map((failure) => (
                  <TableRow key={failure.id} hover>
                    <TableCell>{failure.id}</TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      {formatDate(failure.created_at)}
                    </TableCell>
                    <TableCell>
                      <Chip label={failure.event_type} size="small" color="warning" variant="outlined" />
                    </TableCell>
                    <TableCell>{truncate(failure.event_key, 15)}</TableCell>
                    <TableCell>
                      <Chip label={failure.failure_stage} size="small" color="error" />
                    </TableCell>
                    <TableCell>{truncate(failure.error_type, 20)}</TableCell>
                    <TableCell>{failure.project_key || 'N/A'}</TableCell>
                    <TableCell>{truncate(failure.repo_slug || 'N/A', 20)}</TableCell>
                    <TableCell>
                      {failure.resolved ? (
                        <Chip label="Resolved" size="small" color="success" />
                      ) : (
                        <Chip label="Unresolved" size="small" color="error" />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleViewDetails(failure)}
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

        {!loading && failures.length > 0 && (
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
      {selectedFailure && (
        <FailureDetails
          failure={selectedFailure}
          open={detailsOpen}
          onClose={handleCloseDetails}
        />
      )}
    </Box>
  );
}
