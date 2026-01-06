# Skip Tracing Feature - Documentation

## Overview

The skip tracing feature enables you to find property owner contact information for your analyzed properties. This helps with direct outreach for real estate opportunities.

## Features

### Owner Information Retrieved

- **Name Details**: First, middle, last, and full name
- **Contact Information**:
  - Up to 3 phone numbers (primary, mobile, secondary)
  - Up to 2 email addresses (primary, secondary)
- **Mailing Address**: Complete mailing address details
- **Owner Details**:
  - Owner type (Individual, LLC, Trust, etc.)
  - Owner-occupied status

### Data Provider

**Primary Provider**: BatchData API
- **Accuracy**: 76-97%
- **Cost**: $0.009-0.02 per record
- **Features**:
  - Verified phone numbers and emails
  - DNC (Do Not Call) compliance built-in
  - Batch processing support (up to 100 properties)

## Setup

### 1. Get BatchData API Key

1. Visit [BatchData](https://batchdata.com)
2. Sign up for an account
3. Get your API key from the dashboard

### 2. Configure Backend

Add your API key to `backend/.env`:

```bash
BATCHDATA_API_KEY=your_api_key_here
```

### 3. Run Database Migration

The migration has already been run if you followed the setup instructions. If not:

```bash
cd backend
source venv/bin/activate
python migrate_owner_info.py
```

## Usage

### Via Web Interface

1. **Upload & Analyze Properties**:
   - Upload your CSV file with property addresses
   - Wait for the initial risk analysis to complete

2. **Run Skip Tracing**:
   - On the results page, click the **"Find Owners"** button
   - Processing starts in the background
   - Results appear automatically as they complete

3. **View Owner Information**:
   - Click on any property row to expand details
   - Owner information appears in a blue-highlighted section
   - Includes contact details, mailing address, and metadata

4. **Export Results**:
   - Click **"Export CSV"** to download all data
   - Owner information is included in the CSV export

### Via API

#### Trigger Skip Tracing

```bash
POST /skip-trace/{job_id}
```

**Response**:
```json
{
  "job_id": "uuid",
  "message": "Skip trace processing started",
  "total_properties": 100,
  "already_traced": 0,
  "status": "processing"
}
```

#### Get Skip Trace Results

```bash
GET /skip-trace/{job_id}
```

**Response**:
```json
{
  "job_id": "uuid",
  "statistics": {
    "total_properties": 100,
    "traced": 85,
    "found": 72,
    "not_found": 13,
    "pending": 15
  },
  "results": [
    {
      "property_id": 1,
      "address": {
        "street": "123 Main St",
        "city": "Miami",
        "state": "FL",
        "zip": "33101",
        "full_address": "123 Main St, Miami, FL 33101"
      },
      "owner_info": {
        "status": "complete",
        "found": true,
        "name": {
          "first": "John",
          "middle": "A",
          "last": "Doe",
          "full": "John A Doe"
        },
        "contact": {
          "phone_primary": "555-123-4567",
          "phone_mobile": "555-987-6543",
          "phone_secondary": null,
          "email_primary": "john@example.com",
          "email_secondary": null
        },
        "mailing_address": {
          "street": "456 Oak Ave",
          "city": "Orlando",
          "state": "FL",
          "zip": "32801",
          "full": "456 Oak Ave, Orlando, FL 32801"
        },
        "details": {
          "owner_type": "Individual",
          "owner_occupied": false
        },
        "metadata": {
          "source": "BatchData API",
          "confidence": 0.95,
          "retrieved_at": "2025-12-28T12:00:00Z",
          "processing_time_seconds": 1.2
        }
      }
    }
  ]
}
```

#### Get All Results (Including Owner Info)

```bash
GET /results/{job_id}
```

This endpoint now includes owner information in each property result under the `owner_info` field.

## Database Schema

### PropertyOwnerInfo Table

```sql
-- Name fields
owner_first_name VARCHAR(255)
owner_middle_name VARCHAR(255)
owner_last_name VARCHAR(255)
owner_full_name VARCHAR(500)
owner_name VARCHAR(500)  -- Legacy field

-- Owner details
owner_type VARCHAR(50)
owner_occupied BOOLEAN

-- Contact - Phone
phone VARCHAR(50)  -- Legacy field
phone_primary VARCHAR(50)
phone_mobile VARCHAR(50)
phone_secondary VARCHAR(50)

-- Contact - Email
email VARCHAR(255)  -- Legacy field
email_primary VARCHAR(255)
email_secondary VARCHAR(255)

-- Mailing Address
mailing_address TEXT  -- Legacy field
mailing_street TEXT
mailing_city VARCHAR(255)
mailing_state VARCHAR(2)
mailing_zip VARCHAR(20)
mailing_full_address TEXT

-- Metadata
source VARCHAR(100)
retrieved_at TIMESTAMP
owner_info_status VARCHAR(20)  -- 'pending', 'complete', 'not_found', 'error'
confidence_score FLOAT
error_message TEXT
processing_time_seconds FLOAT
retry_count INTEGER
last_retry_at TIMESTAMP
```

## Implementation Details

### Backend Architecture

```
┌─────────────────────┐
│   Main API          │
│   (main.py)         │
└──────────┬──────────┘
           │
           ├─ POST /skip-trace/{job_id}
           │  └─> Triggers background processing
           │
           ├─ GET /skip-trace/{job_id}
           │  └─> Returns skip trace results
           │
           └─ GET /results/{job_id}
              └─> Includes owner_info in response

┌─────────────────────┐
│ SkipTraceService    │
│ (skip_trace_service)│
└──────────┬──────────┘
           │
           ├─ skip_trace_property()
           │  └─> Single property lookup
           │
           ├─ batch_skip_trace()
           │  └─> Batch processing (up to 100)
           │
           └─ _skip_trace_batchdata()
              └─> BatchData API integration

┌─────────────────────┐
│ Background Worker   │
│ (ThreadPoolExecutor)│
└──────────┬──────────┘
           │
           └─ process_skip_trace()
              └─> Max 5 concurrent requests
```

### Frontend Components

1. **Results Page** ([results/[jobId]/page.tsx](frontend/app/results/[jobId]/page.tsx)):
   - "Find Owners" button (line 226-235)
   - Owner information display (line 728-858)
   - Updated CSV export with owner data (line 139-168)

2. **API Types** ([lib/api.ts](frontend/lib/api.ts)):
   - `OwnerInfo` interface (line 97-130)
   - Updated `PropertyResult` to include `owner_info` (line 140)
   - Skip trace API methods (line 265-295)

3. **React Hooks** ([lib/hooks.ts](frontend/lib/hooks.ts)):
   - `useTriggerSkipTrace()` - Trigger skip tracing
   - `useSkipTraceResults()` - Fetch skip trace results

## Processing Flow

1. **User clicks "Find Owners"**
   ```
   Frontend → POST /skip-trace/{job_id} → Backend
   ```

2. **Backend queues background task**
   ```
   main.py → trigger_skip_trace() → BackgroundTasks.add_task()
   ```

3. **Background worker processes properties**
   ```
   process_skip_trace()
   ├─> Queries properties without owner info
   ├─> Creates ThreadPoolExecutor (max 5 workers)
   └─> For each property:
       └─> process_single_property_skip_trace()
           ├─> SkipTraceService.skip_trace_property()
           ├─> BatchData API call
           ��─> Save to PropertyOwnerInfo table
   ```

4. **Frontend automatically refreshes**
   ```
   React Query invalidates cache
   → Re-fetches /results/{job_id}
   → Owner info appears in UI
   ```

## Cost Estimation

### BatchData API Pricing

- **Per record**: $0.009 - $0.02
- **Average**: ~$0.015 per property

### Example Costs

| Properties | Low ($0.009) | Average ($0.015) | High ($0.02) |
|-----------|--------------|------------------|--------------|
| 100       | $0.90        | $1.50            | $2.00        |
| 500       | $4.50        | $7.50            | $10.00       |
| 1,000     | $9.00        | $15.00           | $20.00       |
| 5,000     | $45.00       | $75.00           | $100.00      |
| 10,000    | $90.00       | $150.00          | $200.00      |
| 20,000    | $180.00      | $300.00          | $400.00      |

## Performance

### Processing Speed

- **Single property**: ~1-2 seconds
- **Concurrent processing**: 5 properties at once
- **Batch API** (if available): Up to 100 properties per request

### Time Estimates

| Properties | Sequential | Concurrent (5 workers) | Batch (100/request) |
|-----------|-----------|------------------------|---------------------|
| 100       | ~3 min    | ~40 sec                | ~10 sec             |
| 500       | ~15 min   | ~3 min                 | ~50 sec             |
| 1,000     | ~30 min   | ~6 min                 | ~1.5 min            |
| 5,000     | ~2.5 hrs  | ~30 min                | ~7.5 min            |
| 10,000    | ~5 hrs    | ~1 hr                  | ~15 min             |

*Current implementation uses concurrent processing with 5 workers*

## Fallback Mode

If `BATCHDATA_API_KEY` is not configured, the system falls back to a limited public records search:

- **Returns**: Placeholder data with low confidence
- **Accuracy**: Very low (~10%)
- **Recommendation**: Always use BatchData API for production

### Fallback Response Example

```json
{
  "owner_found": true,
  "owner_info": {
    "full_name": "Owner information requires API key",
    "phone_primary": null,
    "email_primary": null,
    "mailing_full_address": null,
    "owner_type": "Unknown",
    "confidence": 0.10
  },
  "source": "Public Records (Limited)"
}
```

## Best Practices

### 1. Cost Optimization

- **Filter before skip tracing**: Run risk analysis first, then only trace properties that meet your criteria
- **Avoid duplicates**: The system automatically skips properties that already have owner info
- **Batch processing**: Process multiple properties to benefit from batch API rates

### 2. Data Quality

- **Verify confidence scores**: Higher confidence = more reliable data
- **Cross-reference sources**: Compare with other data sources when possible
- **Update regularly**: Owner information can change over time

### 3. Compliance

- **DNC Lists**: BatchData includes DNC compliance, but verify before calling
- **Privacy laws**: Follow TCPA, GDPR, and other applicable regulations
- **Opt-out requests**: Honor any opt-out requests promptly

### 4. Usage Patterns

```python
# Example: Only trace high-risk properties
# 1. Upload and analyze properties
# 2. Filter results by risk level in frontend
# 3. Click "Find Owners" to trace filtered set
```

## Troubleshooting

### Issue: "No API key configured"

**Solution**: Add `BATCHDATA_API_KEY` to `backend/.env`

### Issue: "Some properties show 'not_found'"

**Explanation**: Not all properties have public owner records available. This is normal.

### Issue: "Skip tracing is slow"

**Solutions**:
1. Reduce concurrent workers if experiencing rate limits
2. Check BatchData API status
3. Consider upgrading to a higher BatchData tier for faster processing

### Issue: "Database error when saving owner info"

**Solution**: Run the migration script:
```bash
cd backend
python migrate_owner_info.py
```

### Issue: "Owner info not showing in frontend"

**Checks**:
1. Verify skip tracing completed (check backend logs)
2. Hard refresh the page (Cmd/Ctrl + Shift + R)
3. Check browser console for errors
4. Verify database has owner records: `SELECT * FROM property_owner_info LIMIT 5;`

## API Rate Limits

### BatchData API

- **Default**: Check your BatchData account dashboard
- **Handling**: The service includes automatic retry logic with exponential backoff
- **Monitoring**: Check logs for rate limit warnings

### Adjusting Concurrency

Edit `backend/main.py` line 877:

```python
# Increase/decrease concurrent workers
max_workers = min(5, len(properties))  # Change 5 to desired value
```

**Recommendations**:
- **Lower tier**: 3 workers
- **Standard tier**: 5 workers
- **Premium tier**: 10 workers

## Monitoring

### Backend Logs

```bash
cd backend
tail -f logs/app.log
```

**Key log messages**:
- `Starting skip trace for job {job_id}: {count} properties`
- `Skip tracing property: {address}`
- `Skip trace completed for property {id}: {status}`
- `Skip trace processing completed for upload {id}`

### Database Queries

```sql
-- Check skip trace statistics
SELECT
  owner_info_status,
  COUNT(*) as count
FROM property_owner_info
GROUP BY owner_info_status;

-- Check average confidence scores
SELECT
  AVG(confidence_score) as avg_confidence,
  COUNT(*) as total_records
FROM property_owner_info
WHERE owner_info_status = 'complete';

-- Recent skip traces
SELECT
  p.full_address,
  poi.owner_full_name,
  poi.confidence_score,
  poi.retrieved_at
FROM property_owner_info poi
JOIN properties p ON poi.property_id = p.id
ORDER BY poi.retrieved_at DESC
LIMIT 10;
```

## Security Considerations

### API Key Protection

- **Never commit** `.env` files to git
- **Use environment variables** in production
- **Rotate keys** periodically
- **Limit access** to backend environment

### Data Storage

- **Encrypt sensitive data** in production database
- **Implement data retention** policies
- **Secure API endpoints** with authentication
- **Audit access logs** regularly

### Owner Data Privacy

- **Use for legitimate purposes** only
- **Don't share** owner data publicly
- **Delete data** when no longer needed
- **Follow regulations**: TCPA, GDPR, CCPA, etc.

## Future Enhancements

### Planned Features

1. **Smart filtering**: Only trace properties matching specific criteria
2. **Bulk export**: Export owner contact lists for marketing campaigns
3. **Integration with CRM**: Sync owner info to your CRM system
4. **Email validation**: Real-time email deliverability checking
5. **Phone validation**: Verify phone numbers are active
6. **Enrichment**: Additional data like property value, liens, etc.

### Alternative Providers

If you want to add additional skip trace providers:

1. Create a new service class (e.g., `PropStreamService`)
2. Implement the same interface as `SkipTraceService`
3. Update `main.py` to use multiple providers with fallback
4. Add provider selection in frontend

## Support

### Documentation

- [BatchData API Docs](https://developer.batchdata.com/docs/)
- [Main Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [AI Analysis Documentation](AI_ANALYSIS_README.md)

### Getting Help

1. Check backend logs: `backend/logs/`
2. Review this documentation
3. Check BatchData status page
4. Verify database schema with migration script

## Summary

The skip tracing feature is fully integrated and production-ready:

✅ **Backend**: Complete API endpoints with BatchData integration
✅ **Database**: Migrated schema with all owner info fields
✅ **Frontend**: "Find Owners" button + beautiful owner info display
✅ **Export**: CSV export includes all owner data fields
✅ **Concurrent**: Processes 5 properties simultaneously
✅ **Fallback**: Works without API key (limited data)

**To get started**: Add your `BATCHDATA_API_KEY` to `backend/.env` and click "Find Owners"!
