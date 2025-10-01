# AquaPredict Frontend Structure

## Page Routes

### 1. **Home Page** (`/`)
- **File**: `app/page.tsx`
- **Purpose**: Simple demo/landing page with basic API testing
- **Features**:
  - Manual coordinate input
  - Direct API calls to backend
  - Tabbed results display (Probability, Forecast, Extraction, ISO)
  - No map integration
  - Standalone page without sidebar/header

### 2. **Dashboard** (`/dashboard`) ⭐ **MAIN APPLICATION**
- **File**: `app/dashboard/page.tsx`
- **Purpose**: Full-featured map-based analysis interface
- **Features**:
  - **Enhanced Interactive Map** with:
    - 4 major aquifer zones (color-coded by potential)
    - 8 historical prediction markers (success/failure indicators)
    - 5 water infrastructure points (boreholes/wells)
    - Toggleable layers (Aquifer Zones, Historical Data, Infrastructure)
    - Street/Satellite view switching
    - Comprehensive legend
    - 5km analysis radius for selected locations
  - **Sidebar Navigation**
  - **Header** with menu controls
  - **Quick Stats Bar** showing:
    - Total Predictions: 1,247
    - Success Rate: 87.3%
    - Active Wells: 342
    - Areas at Risk: 23
  - **Prediction Panel** (right sidebar):
    - Location details
    - Aquifer prediction tab
    - Recharge forecast tab
    - Interactive analysis tools

### 3. **Analytics** (`/analytics`)
- **File**: `app/analytics/page.tsx`
- **Purpose**: Data visualization and analytics dashboard
- **Features**: Charts, metrics, trends

### 4. **Reports** (`/reports`)
- **File**: `app/reports/page.tsx`
- **Purpose**: Generate and view reports
- **Features**: ISO 14046 reports, drilling reports

### 5. **History** (`/history`)
- **File**: `app/history/page.tsx`
- **Purpose**: View past predictions and analyses
- **Features**: Historical data, search, filters

### 6. **Settings** (`/settings`)
- **File**: `app/settings/page.tsx`
- **Purpose**: Application configuration
- **Features**:
  - General settings (theme, language, timezone)
  - Map settings (base layer, zoom, markers)
  - ML model configuration
  - Notifications preferences
  - Data source connections

## Map Component Details

### Enhanced Map Features (`components/map/map-component.tsx`)

#### Aquifer Zones
1. **Lake Victoria Basin** (High Potential - Green)
   - Volcanic and sedimentary aquifers
   - Depth: 20-80m, Yield: 5-15 L/s

2. **Rift Valley Aquifer System** (Moderate Potential - Orange)
   - Fractured volcanic rocks
   - Depth: 30-120m, Yield: 2-8 L/s

3. **Coastal Sedimentary Basin** (High Potential - Green)
   - Coastal sedimentary aquifers
   - Depth: 15-60m, Yield: 8-20 L/s

4. **Northern Kenya Basement** (Low Potential - Red)
   - Crystalline basement rocks
   - Depth: 40-150m, Yield: 0.5-3 L/s

#### Historical Predictions (8 locations)
- **Green markers**: Successful boreholes
- **Yellow markers**: Low yield boreholes
- **Red markers**: Failed drilling attempts
- Each shows: probability, result, depth, yield

#### Water Infrastructure (5 locations)
- **Blue markers**: Active boreholes/wells
- **Gray markers**: Under maintenance
- Real location names (e.g., "Nairobi Central BH-001")

#### Interactive Controls
- **Layer toggles**: Show/hide aquifer zones, historical data, infrastructure
- **Base map switch**: Street view ↔ Satellite view
- **Legend**: Comprehensive color coding guide
- **Selection radius**: 5km circle around selected point

## Component Architecture

```
app/
├── page.tsx                    # Simple demo (root)
├── dashboard/
│   └── page.tsx               # Main map-based interface ⭐
├── analytics/page.tsx
├── history/page.tsx
├── reports/page.tsx
└── settings/page.tsx

components/
├── layout/
│   ├── header.tsx             # Top navigation bar
│   └── sidebar.tsx            # Left navigation menu
├── map/
│   ├── map-component.tsx      # Enhanced map with data layers
│   └── map-view.tsx           # Map wrapper (SSR handling)
├── prediction/
│   ├── prediction-panel.tsx   # Right sidebar analysis panel
│   ├── prediction-chart.tsx   # Confidence visualization
│   └── forecast-chart.tsx     # Recharge forecast chart
├── dashboard/
│   └── stats-overview.tsx     # Statistics cards
└── ui/                        # Reusable UI components
    ├── card.tsx
    ├── button.tsx
    ├── badge.tsx
    └── ...

lib/
├── store.ts                   # Zustand state management
├── api.ts                     # API client
└── utils.ts                   # Helper functions
```

## Navigation Flow

1. **Landing** → `/` (Simple demo page)
2. **Main App** → `/dashboard` (Full map interface)
3. **Sidebar Links**:
   - Dashboard → `/dashboard`
   - Analytics → `/analytics`
   - Reports → `/reports`
   - History → `/history`
   - Settings → `/settings`

## Key Differences: Home vs Dashboard

| Feature | Home (`/`) | Dashboard (`/dashboard`) |
|---------|-----------|--------------------------|
| Map | ❌ No | ✅ Yes (Enhanced) |
| Sidebar | ❌ No | ✅ Yes |
| Header | ❌ No | ✅ Yes |
| Aquifer Zones | ❌ No | ✅ Yes (4 zones) |
| Historical Data | ❌ No | ✅ Yes (8 markers) |
| Infrastructure | ❌ No | ✅ Yes (5 points) |
| Layer Controls | ❌ No | ✅ Yes |
| Prediction Panel | ❌ No | ✅ Yes |
| Stats Bar | ❌ No | ✅ Yes |
| Use Case | API Testing | Production Use |

## Recommended Usage

- **Development/Testing**: Use `/` for quick API tests
- **Production/Demo**: Use `/dashboard` for full application experience
- **Users**: Direct them to `/dashboard` as the main interface

## Data Realism

All map data is based on realistic Kenya hydrogeological characteristics:
- Authentic aquifer system names and locations
- Realistic depth ranges and yield expectations
- Geologically accurate zone boundaries
- Real borehole naming conventions
- Historical success/failure patterns based on geological context

## Next Steps

To connect to real data:
1. Replace simulated data in `map-component.tsx` with API calls
2. Fetch aquifer zones from Oracle ADB spatial tables
3. Load historical predictions from database
4. Query infrastructure data from water authority APIs
5. Add real-time updates using WebSockets
6. Implement user authentication and personalized views
