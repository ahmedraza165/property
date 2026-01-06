import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";

export function useJobStatus(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["jobStatus", jobId],
    queryFn: () => api.getJobStatus(jobId!),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "processing") {
        return 2000; // Poll every 2 seconds while processing
      }
      return false;
    },
  });
}

export function useJobResults(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["jobResults", jobId],
    queryFn: () => api.getResults(jobId!),
    enabled: enabled && !!jobId,
  });
}

export function useJobSummary(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["jobSummary", jobId],
    queryFn: () => api.getResultsSummary(jobId!),
    enabled: enabled && !!jobId,
  });
}

export function useUploadCSV() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.uploadCSV(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobStatus", data.job_id] });
    },
  });
}

export function useTriggerAIAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => api.triggerAIAnalysis(jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobStatus", data.job_id] });
      queryClient.invalidateQueries({ queryKey: ["jobResults", data.job_id] });
    },
  });
}

export function useTriggerSkipTrace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => api.triggerSkipTrace(jobId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["jobStatus", data.job_id] });
      queryClient.invalidateQueries({ queryKey: ["jobResults", data.job_id] });
      queryClient.invalidateQueries({ queryKey: ["skipTraceResults", data.job_id] });
    },
  });
}

export function useSkipTraceResults(jobId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["skipTraceResults", jobId],
    queryFn: () => api.getSkipTraceResults(jobId!),
    enabled: enabled && !!jobId,
  });
}
