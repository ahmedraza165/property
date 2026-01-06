# ParcelIQ - Bulk Property Intelligence Platform

A modern, premium web application for bulk land risk analysis designed for real estate investors. ParcelIQ analyzes flood zones, wetlands, road access, slope, and other critical property factors in seconds.

## Project Structure

```
property-anyslis/
├── backend/          # Python FastAPI backend
│   ├── main.py              # Main API application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── gis_service.py       # GIS risk analysis service
│   ├── geocoding_service.py # Address geocoding
│   ├── ai_service.py        # AI/ML image analysis (Phase 2)
│   ├── skip_tracing_service.py # Owner lookup (Phase 3)
│   └── requirements.txt     # Python dependencies
│
└── frontend/         # Next.js React frontend
    ├── app/                 # Next.js App Router pages
    │   ├── page.tsx         # Dashboard/Landing page
    │   ├── upload/          # CSV upload flow
    │   ├── status/[jobId]/  # Processing status
    │   └── results/[jobId]/ # Results table & analysis
    ├── components/          # React components
    │   ├── ui/              # Reusable UI components
    │   └── header.tsx       # App header/navigation
    ├── lib/                 # Utilities and API layer
    │   ├── api.ts           # API client with error handling
    │   ├── hooks.ts         # React Query hooks
    │   ├── providers.tsx    # React Query provider
    │   └── utils.ts         # Helper functions
    └── package.json         # Node dependencies
```

## Features

### Core Functionality
- **CSV Upload** - Drag-and-drop interface for bulk property uploads (up to 20,000 properties)
- **Real-time Processing** - Live progress tracking with animated status indicators
- **Risk Analysis** - Comprehensive GIS-based risk assessment:
  - Flood zone analysis (FEMA data)
  - Wetlands detection (USFWS NWI)
  - Slope calculation (USGS 3DEP)
  - Road access verification (OSM)
  - Protected land identification
  - Landlocked property detection
- **Interactive Results** - Sortable, filterable data table with expandable details
- **Export Functionality** - Download analyzed data as CSV
- **Dashboard** - Overview with statistics and recent uploads

### Design Features
- Premium, minimal UI design
- Smooth animations with Framer Motion
- Responsive layout (desktop-first)
- Loading states and skeleton loaders
- Error handling with retry logic
- Color-coded risk badges (Low, Medium, High)

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Requests** - HTTP client for external APIs

### Frontend
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **React Query (@tanstack/react-query)** - Server state management
- **Lucide React** - Icons

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 14+

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `NOMINATIM_USER_AGENT` - User agent for geocoding
- API keys for external services (if applicable)

5. Initialize the database:
```bash
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

6. Run the backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Default configuration:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Build for Production

Backend:
```bash
# From backend directory
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Frontend:
```bash
# From frontend directory
npm run build
npm start
```

## Usage

1. **Upload CSV**: Navigate to `/upload` and drag-and-drop or select a CSV file
   - Required columns: `Street address`, `City`, `State`, `Postal Code`
   - Optional columns: `Contact Id`, `First Name`, `Last Name`, `Name`, `Tags`

2. **Monitor Progress**: Automatically redirected to `/status/[jobId]` to watch processing

3. **View Results**: After completion, view detailed analysis at `/results/[jobId]`
   - Sort by address or risk level
   - Filter by risk category (Low, Medium, High)
   - Search by address or name
   - Export results as CSV
   - Expand rows for detailed risk breakdowns

## API Endpoints

### Core Endpoints
- `POST /process-csv` - Upload and process CSV file
- `GET /status/{job_id}` - Get processing status
- `GET /results/{job_id}` - Get analysis results
- `GET /results/{job_id}/summary` - Get summary statistics

### Advanced Features (Optional)
- `POST /analyze-ai/{job_id}` - Trigger AI image analysis
- `POST /skiptrace/{job_id}` - Run owner lookup
- `GET /skiptrace/{job_id}` - Get owner information

## Development

### Code Structure

Frontend follows modern React patterns:
- **Server Components** where possible
- **Client Components** (`"use client"`) for interactivity
- **React Query** for API state management
- **TypeScript** for type safety
- **Tailwind CSS** with custom theme

Key frontend patterns:
- API layer with automatic retries (`lib/api.ts`)
- Custom hooks for data fetching (`lib/hooks.ts`)
- Reusable UI components (`components/ui/`)
- Utility functions for formatting (`lib/utils.ts`)

### Customization

**Branding**: Update product name in:
- `frontend/app/layout.tsx` (metadata)
- `frontend/components/header.tsx` (logo/name)
- `frontend/lib/utils.ts` (localStorage keys)

**Styling**: Modify theme in:
- `frontend/app/globals.css` (CSS variables)
- Tailwind color palette can be extended in CSS custom properties

**API URL**: Set in:
- `frontend/.env.local` (development)
- Environment variables (production)

## Performance

- **Backend**: Processes 1-2 properties per second
- **Frontend**: Optimistic UI updates, skeleton loaders
- **Database**: Indexed queries for fast lookups
- **Caching**: React Query with 1-minute stale time

## Security

- Input validation on CSV uploads
- File size limits (10MB)
- Row limits (20,000 properties)
- API error handling and retries
- XSS protection via React
- CORS configuration in backend

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

Proprietary - All rights reserved

## Support

For issues or questions, please contact the development team.

---

**Built with modern web technologies for real estate professionals.**
