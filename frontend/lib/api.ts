const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  county: string | null;
  full_address: string;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface PropertyDetails {
  legal_description: string | null;
  lot_size_acres: number | null;
  lot_size_sqft: number | null;
}

export interface Phase1Risk {
  wetlands: {
    status: string;
    source: string;
  };
  flood_zone: {
    zone: string;
    severity: string;
    source: string;
  };
  slope: {
    percentage: number;
    severity: string;
    source: string;
  };
  road_access: {
    has_access: boolean;
    distance_meters: number;
    source: string;
  };
  landlocked: boolean;
  protected_land: {
    is_protected: boolean;
    type: string;
    source: string;
  };
  water_utility: {
    water_available: boolean | null;
    sewer_available: boolean | null;
    water_provider: string | null;
    sewer_provider: string | null;
    source: string;
  };
  overall_risk: string;
  processing_time_seconds: number;
  error: string | null;
}

export interface AIAnalysis {
  imagery: {
    satellite: {
      url: string | null;
      source: string | null;
    };
    street: {
      url: string | null;
      source: string | null;
    };
  };
  road_condition: {
    type: string | null;
    confidence: number | null;
  };
  power_lines: {
    visible: boolean;
    confidence: number | null;
    distance_meters: number | null;
    geometry: string | null;
  };
  nearby_development: {
    type: string | null;
    count: number | null;
    confidence: number | null;
  };
  overall_risk: {
    level: string | null;
    confidence: number | null;
  };
  processing_time_seconds: number | null;
  model_version: string | null;
  analyzed_at: string | null;
  error: string | null;
}

export interface OwnerInfo {
  status: string;
  found: boolean;
  name: {
    first: string | null;
    middle: string | null;
    last: string | null;
    full: string | null;
  };
  contact: {
    phone_primary: string | null;
    phone_mobile: string | null;
    phone_secondary: string | null;
    email_primary: string | null;
    email_secondary: string | null;
  };
  mailing_address: {
    street: string | null;
    city: string | null;
    state: string | null;
    zip: string | null;
    full: string | null;
  };
  details: {
    owner_type: string | null;
    owner_occupied: boolean | null;
  };
  metadata: {
    source: string | null;
    confidence: number | null;
    retrieved_at: string | null;
    processing_time_seconds: number | null;
  };
}

export interface PropertyResult {
  contact_id: string;
  name: string;
  address: Address;
  coordinates: Coordinates | null;
  property_details: PropertyDetails;
  phase1_risk: Phase1Risk | null;
  ai_analysis: AIAnalysis | null;
  owner_info: OwnerInfo | null;
}

export interface JobStatus {
  job_id: string;
  filename: string;
  status: "processing" | "completed" | "failed";
  total_rows: number;
  processed_rows: number;
  progress_percentage: number;
  uploaded_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobResults {
  job_id: string;
  status: string;
  filename: string;
  total_properties: number;
  processed_properties: number;
  completed_at: string | null;
  results: PropertyResult[];
}

export interface JobSummary {
  job_id: string;
  status: string;
  total_properties: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
  };
  risk_factors: {
    wetlands: number;
    high_flood_zone: number;
    landlocked: number;
    protected_land: number;
  };
  percentages: {
    low_risk: number;
    medium_risk: number;
    high_risk: number;
  };
}

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          response.status,
          errorData.detail || `HTTP error! status: ${response.status}`,
          errorData
        );
      }

      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  throw new Error("Max retries reached");
}

export const api = {
  async uploadCSV(file: File): Promise<{ job_id: string; status: string; total_rows: number; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchWithRetry(`${API_BASE_URL}/process-csv`, {
      method: "POST",
      body: formData,
    });

    return response.json();
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetchWithRetry(`${API_BASE_URL}/status/${jobId}`);
    return response.json();
  },

  async getResults(jobId: string): Promise<JobResults> {
    const response = await fetchWithRetry(`${API_BASE_URL}/results/${jobId}`);
    return response.json();
  },

  async getResultsSummary(jobId: string): Promise<JobSummary> {
    const response = await fetchWithRetry(`${API_BASE_URL}/results/${jobId}/summary`);
    return response.json();
  },

  async triggerAIAnalysis(jobId: string): Promise<{ job_id: string; status: string; total_properties: number; message: string }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/analyze-ai/${jobId}`, {
      method: "POST",
    });
    return response.json();
  },

  async triggerSkipTrace(jobId: string): Promise<{
    job_id: string;
    status: string;
    total_properties: number;
    already_traced: number;
    message: string;
  }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/skip-trace/${jobId}`, {
      method: "POST",
    });
    return response.json();
  },

  async getSkipTraceResults(jobId: string): Promise<{
    job_id: string;
    statistics: {
      total_properties: number;
      traced: number;
      found: number;
      not_found: number;
      pending: number;
    };
    results: Array<{
      property_id: number;
      address: Address;
      owner_info: OwnerInfo;
    }>;
  }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/skip-trace/${jobId}`);
    return response.json();
  },
};

export { APIError };
