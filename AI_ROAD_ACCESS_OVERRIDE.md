# AI Road Access Override Feature

## Overview

The AI analysis system now automatically verifies and can override the initial GIS-based road access calculations when it detects discrepancies through image analysis.

## How It Works

### 1. Initial GIS Analysis
When properties are first processed, the GIS service checks road access using OpenStreetMap data:
- Queries for roads within 200m of the property
- Calculates distance to nearest road
- Sets `road_access` (True/False) and `road_distance_meters`

### 2. AI Analysis with Override
When you run AI analysis (POST `/analyze-ai/{job_id}`), for each property:

1. **AI analyzes satellite/street imagery** to determine road condition:
   - PAVED - Well-maintained paved road
   - DIRT - Unpaved dirt road
   - GRAVEL - Gravel road
   - POOR - Paved but poor condition
   - UNKNOWN - Cannot determine

2. **AI results are compared with GIS results**:
   - The system calls `check_and_determine_road_access_override()`
   - Compares AI road condition with GIS road access data

3. **Override conditions** (when AI confidence >= 60%):

   **Scenario A: AI sees road, GIS doesn't**
   - AI detects DIRT/GRAVEL/PAVED road
   - GIS says `road_access = False`
   - **Override Applied**: Updates to `road_access = True`, estimates distance

   **Scenario B: AI can't see road, GIS says far away**
   - AI returns UNKNOWN road condition
   - GIS says `road_access = True` but distance > 100m
   - **Override Applied**: Updates to `road_access = False` (likely landlocked)

4. **Risk recalculation**:
   - When road access is overridden, the system recalculates `overall_risk`
   - Updates `landlocked` status if needed
   - Stores reason in `road_source` field

## Database Changes

When AI overrides road access, the `risk_results` table is updated:

```sql
UPDATE risk_results SET
  road_access = <new_value>,
  road_distance_meters = <new_value>,
  road_source = 'AI Override: <reason>',
  landlocked = <updated_based_on_road_access>,
  overall_risk = <recalculated>
WHERE property_id = <property_id>;
```

## Example Scenarios

### Example 1: Unpaved Road Detection
```
Initial GIS Result:
  - road_access: False
  - road_distance_meters: 0
  - road_source: "Assumed accessible (verification unavailable)"

AI Analysis Result:
  - road_condition_type: "DIRT"
  - road_condition_confidence: 0.85

Override Applied:
  - road_access: True ✓
  - road_distance_meters: 50 (estimated)
  - road_source: "AI Override: AI detected DIRT road (confidence: 0.85) but GIS found no road access. Updated to reflect unpaved road access."
  - landlocked: False
  - overall_risk: May increase due to dirt road
```

### Example 2: No Road Confirmed
```
Initial GIS Result:
  - road_access: True
  - road_distance_meters: 150
  - road_source: "OpenStreetMap (Overpass API)"

AI Analysis Result:
  - road_condition_type: "UNKNOWN"
  - road_condition_confidence: 0.70

Override Applied:
  - road_access: False ✓
  - road_distance_meters: 150
  - road_source: "AI Override: AI cannot confirm road access and GIS shows road is 150m away. Updated to no direct access."
  - landlocked: True
  - overall_risk: HIGH (increased due to landlocked status)
```

## API Response Changes

When you fetch results (GET `/results/{job_id}`), you'll see:

```json
{
  "phase1_risk": {
    "road_access": {
      "has_access": true,
      "distance_meters": 50,
      "source": "AI Override: AI detected DIRT road (confidence: 0.85)..."
    },
    "overall_risk": "MEDIUM"
  },
  "ai_analysis": {
    "road_condition": {
      "type": "DIRT",
      "confidence": 0.85
    }
  }
}
```

## Logging

The system logs all overrides:

```
Property 123 - AI Override Applied: Road access changed from False (0m) to True (50m).
Overall risk: LOW -> MEDIUM.
Reason: AI detected DIRT road (confidence: 0.85) but GIS found no road access. Updated to reflect unpaved road access.
```

## Testing the Feature

1. **Upload CSV** with properties:
   ```bash
   POST /process-csv
   ```

2. **Wait for processing** to complete:
   ```bash
   GET /status/{job_id}
   ```

3. **Trigger AI analysis**:
   ```bash
   POST /analyze-ai/{job_id}
   ```

4. **Check results** for updated road access:
   ```bash
   GET /results/{job_id}
   ```

5. **Look for** properties where `road_source` contains "AI Override"

## Configuration

Override confidence threshold is set in `ai_analysis_service.py`:

```python
if confidence >= 0.6:  # AI is confident
    # Override logic here
```

You can adjust this threshold (0.0 - 1.0) to make the system more or less aggressive with overrides.

## Benefits

1. **More Accurate Risk Assessment**: Combines GIS data with visual verification
2. **Detects Unpaved Roads**: GIS may miss dirt/gravel roads not in OSM
3. **Identifies Truly Landlocked Properties**: Verifies claimed road access
4. **Transparent Changes**: All overrides are logged with reasons
5. **Automatic Recalculation**: Overall risk updates when road access changes

## Important Notes

- AI overrides only happen when AI confidence >= 60%
- Original GIS data is preserved in logs
- Changes are applied to the `risk_results` table
- AI analysis must be run AFTER initial GIS processing
- Overrides are property-specific and don't affect other properties
