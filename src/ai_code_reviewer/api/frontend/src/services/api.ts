import axios, { AxiosInstance } from 'axios';
import type {
  ReviewListResponse,
  FailureListResponse,
  DiffReviewResponse,
  ManualReviewResponse,
  HealthResponse,
  ReviewRecord,
  FailureRecord,
  DiffUploadFormData,
  ManualReviewFormData,
} from '../types/types';

// Create axios instance with base URL from environment
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes timeout for LLM processing
});

// API Service
export const api = {
  // Health check
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },

  // Diff upload review
  async uploadDiffForReview(formData: DiffUploadFormData): Promise<DiffReviewResponse> {
    const form = new FormData();
    form.append('file', formData.file);
    form.append('project_key', formData.project_key);
    form.append('repo_slug', formData.repo_slug);
    form.append('author_name', formData.author_name);
    if (formData.author_email) {
      form.append('author_email', formData.author_email);
    }
    if (formData.description) {
      form.append('description', formData.description);
    }

    const response = await apiClient.post<DiffReviewResponse>('/review-diff', form, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Manual review
  async triggerManualReview(formData: ManualReviewFormData): Promise<ManualReviewResponse> {
    const params: Record<string, string | number> = {
      project_key: formData.project_key,
      repo_slug: formData.repo_slug,
    };

    if (formData.pr_id) {
      params.pr_id = formData.pr_id;
    }
    if (formData.commit_id) {
      params.commit_id = formData.commit_id;
    }

    const response = await apiClient.post<ManualReviewResponse>('/manual-review', null, {
      params,
    });
    return response.data;
  },

  // Reviews endpoints
  async getReviews(offset: number = 0, limit: number = 25): Promise<ReviewListResponse> {
    const response = await apiClient.get<ReviewListResponse>('/reviews', {
      params: { offset, limit },
    });
    return response.data;
  },

  async getReviewById(id: number): Promise<ReviewRecord> {
    const response = await apiClient.get<ReviewRecord>(`/reviews/${id}`);
    return response.data;
  },

  // Failures endpoints
  async getFailures(offset: number = 0, limit: number = 25): Promise<FailureListResponse> {
    const response = await apiClient.get<FailureListResponse>('/failures', {
      params: { offset, limit },
    });
    return response.data;
  },

  async getFailureById(id: number): Promise<FailureRecord> {
    const response = await apiClient.get<FailureRecord>(`/failures/${id}`);
    return response.data;
  },
};

export default api;
