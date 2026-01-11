# Data Sources for Manual Verification

## 🌊 FLOOD ZONE DATA SOURCES

### Primary Source: FEMA NFHL (National Flood Hazard Layer)
**API Endpoint:**
```
https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query
```

**Manual Verification Tools:**

1. **FEMA Flood Map Service Center (Official)**
   - URL: https://msc.fema.gov/portal/home
   - This is the official FEMA flood map viewer
   - Enter any address to see official flood zone designation

2. **FEMA NFHL Web Map Viewer**
   - URL: https://hazards-fema.maps.arcgis.com/apps/webappviewer/index.html?id=8b0adb51996444d4879338b5529aa9cd
   - Interactive map showing all flood zones
   - Can zoom to specific coordinates

3. **Example Query for 909 Monroe Ave, Lehigh Acres, FL**
   - Coordinates: approximately 26.6251, -81.6248
   - Direct API test: https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query?geometry=-81.6248,26.6251&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=FLD_ZONE,ZONE_SUBTY,SFHA_TF&returnGeometry=false&f=json

### Alternative Source: FEMA MSC
**API Endpoint:**
```
https://msc.fema.gov/arcgis/rest/services/public/NFHLWMS/MapServer/identify
```

---

## 🌿 WETLANDS DATA SOURCES

### Primary Source: USFWS National Wetlands Inventory (NWI)
**API Endpoint:**
```
https://www.fws.gov/wetlands/arcgis/rest/services/Wetlands/MapServer/0/query
```

**Manual Verification Tools:**

1. **USFWS Wetlands Mapper (Official)**
   - URL: https://www.fws.gov/wetlands/data/mapper.html
   - Official U.S. Fish & Wildlife Service wetlands map
   - Enter any address to see wetlands designation
   - Most accurate and up-to-date source

2. **Example Query for 927 Lakeside, Lehigh Acres, FL**
   - Coordinates: approximately 26.6250, -81.6240
   - Direct API test: https://www.fws.gov/wetlands/arcgis/rest/services/Wetlands/MapServer/0/query?geometry=-81.6240,26.6250&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=WETLAND_TYPE,ATTRIBUTE&returnGeometry=false&f=json

---

## 🧪 TEST ADDRESSES FROM CLIENT

### Address 1: 909 Monroe Ave, Lehigh Acres, FL
**Client Reports:** AE Flood Zone
**Expected:** High flood risk (AE zone requires flood insurance)

**Test Links:**
- FEMA Map: https://msc.fema.gov/portal/search?AddressQuery=909%20Monroe%20Ave%2C%20Lehigh%20Acres%2C%20FL
- Wetlands Map: https://www.fws.gov/wetlands/data/mapper.html

### Address 2: 927 Lakeside, Lehigh Acres, FL
**Client Reports:** Wetland
**Expected:** High wetlands presence

**Test Links:**
- FEMA Map: https://msc.fema.gov/portal/search?AddressQuery=927%20Lakeside%2C%20Lehigh%20Acres%2C%20FL
- Wetlands Map: https://www.fws.gov/wetlands/data/mapper.html

---

## 🔍 HOW TO MANUALLY VERIFY

### For Flood Zones:
1. Go to https://msc.fema.gov/portal/home
2. Click "Search By Address"
3. Enter the full address
4. View the flood zone designation (X, AE, AH, VE, etc.)
5. Download official Flood Insurance Rate Map (FIRM) if needed

### For Wetlands:
1. Go to https://www.fws.gov/wetlands/data/mapper.html
2. Enter the address in the search box
3. View the map - wetlands are shown in different colors
4. Click on any wetland polygon to see details
5. Green/blue areas indicate wetlands presence

---

## ⚠️ CURRENT ISSUES IDENTIFIED

### Issue 1: FEMA API Connectivity
- **Problem:** SSL connection errors when querying FEMA API
- **Result:** Fallback to geographic estimates (showing "Zone X" for all Lehigh Acres)
- **Impact:** Missing AE zones and other high-risk flood zones

### Issue 2: Wetlands False Positives
- **Problem:** Geographic fallback in lines 164-170 of gis_service.py
- **Code:**
```python
if 26.0 <= latitude <= 27.5 and -82.0 <= longitude <= -81.0:
    return {
        "status": True,  # Returns TRUE for ALL SW Florida!
        "confidence": "MEDIUM",
        "source": "Geographic heuristic (SW Florida wetlands zone)"
    }
```
- **Result:** Shows wetlands for ALL properties in SW Florida coordinates
- **Impact:** ~99% false positive rate for wetlands

---

## 🎯 RECOMMENDED FIXES

### Fix 1: Remove Geographic Fallbacks
- Remove lines 164-170 (wetlands geographic fallback)
- Remove lines 324-346 (flood zone geographic fallback)
- Only return data from official APIs or mark as "Unable to verify"

### Fix 2: Fix FEMA API Connectivity
- Update SSL handling
- Try alternative query parameters
- Consider using paid FEMA API if public API is unreliable

### Fix 3: Consider Paid Data Providers
If public APIs continue to fail:
- CoreLogic Property API
- Zillow API (has flood zone data)
- ATTOM Data Solutions
- First Street Foundation Flood Risk API
