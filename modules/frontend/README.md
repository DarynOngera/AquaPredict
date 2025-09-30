# AquaPredict Frontend

Modern, responsive dashboard for aquifer prediction and groundwater analysis.

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS + shadcn/ui components
- **Maps**: Leaflet + React Leaflet
- **Charts**: Recharts
- **Icons**: Lucide React
- **State**: Zustand
- **Data Fetching**: SWR
- **Type Safety**: TypeScript

## Features

### 🗺️ Interactive Map
- Leaflet-based map with custom layers
- Click to predict aquifer at location
- Heatmap overlays for predictions
- Spatial query tools
- Layer controls (precipitation, elevation, predictions)

### 📊 Dashboards
- **Overview**: Summary statistics and key metrics
- **Predictions**: Aquifer presence/depth predictions
- **Forecasts**: Groundwater recharge forecasts
- **Analysis**: Feature importance and model insights

### 📈 Visualizations
- Time-series charts (precipitation, recharge)
- Bar charts (feature importance)
- Heatmaps (spatial predictions)
- Confidence intervals
- Interactive tooltips

### 📄 Reports
- Generate ISO 14046 reports
- Export predictions to CSV/GeoJSON
- PDF download
- Share reports

### 🎨 Design
- Mobile-first responsive design
- Dark/light mode support
- Minimalist, modern UI
- Accessible (WCAG 2.1 AA)
- Fast loading with Next.js optimization

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Home page
│   ├── dashboard/         # Dashboard pages
│   ├── predictions/       # Prediction pages
│   └── reports/           # Report pages
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── map/               # Map components
│   ├── charts/            # Chart components
│   └── layout/            # Layout components
├── lib/
│   ├── api.ts             # API client
│   ├── utils.ts           # Utilities
│   └── store.ts           # Zustand store
├── public/                # Static assets
├── styles/                # Global styles
└── types/                 # TypeScript types
```

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

## Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

## Key Components

### Map Component

```tsx
import { MapContainer, TileLayer, Marker } from 'react-leaflet';

<MapContainer center={[0, 36]} zoom={6}>
  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
  <PredictionLayer />
</MapContainer>
```

### Prediction Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Aquifer Prediction</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      <div className="flex justify-between">
        <span>Presence:</span>
        <Badge>{prediction.result}</Badge>
      </div>
      <Progress value={prediction.probability * 100} />
    </div>
  </CardContent>
</Card>
```

### Forecast Chart

```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

<LineChart data={forecastData}>
  <XAxis dataKey="month" />
  <YAxis />
  <Tooltip />
  <Line type="monotone" dataKey="recharge" stroke="#8884d8" />
  <Line type="monotone" dataKey="lower" stroke="#82ca9d" strokeDasharray="5 5" />
  <Line type="monotone" dataKey="upper" stroke="#82ca9d" strokeDasharray="5 5" />
</LineChart>
```

## API Integration

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

export const predictAquifer = async (location: Location) => {
  const response = await api.post('/api/v1/predict/aquifer', {
    location,
    use_cached_features: true,
  });
  return response.data;
};

export const forecastRecharge = async (location: Location, horizon: number) => {
  const response = await api.post('/api/v1/predict/recharge', {
    location,
    horizon,
  });
  return response.data;
};
```

## Styling with Tailwind

```tsx
<div className="container mx-auto px-4 py-8">
  <h1 className="text-4xl font-bold mb-6">AquaPredict</h1>
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {/* Cards */}
  </div>
</div>
```

## State Management

```typescript
// lib/store.ts
import create from 'zustand';

interface AppState {
  selectedLocation: Location | null;
  predictions: Prediction[];
  setLocation: (location: Location) => void;
  addPrediction: (prediction: Prediction) => void;
}

export const useStore = create<AppState>((set) => ({
  selectedLocation: null,
  predictions: [],
  setLocation: (location) => set({ selectedLocation: location }),
  addPrediction: (prediction) => 
    set((state) => ({ predictions: [...state.predictions, prediction] })),
}));
```

## Testing

```bash
npm test
```

## Deployment

### Vercel (Recommended)

```bash
vercel deploy
```

### Docker

```bash
docker build -t aquapredict-frontend .
docker run -p 3000:3000 aquapredict-frontend
```

## Performance Optimization

- Image optimization with Next.js Image
- Code splitting and lazy loading
- SWR for data caching
- Memoization of expensive components
- Debounced map interactions

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support
- Color contrast compliance
