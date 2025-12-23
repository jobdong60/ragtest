import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import {
  Users,
  Activity,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
  Bell,
  Search,
  CheckCircle2,
  AlertCircle,
  LayoutDashboard,
  UserCheck,
  Heart,
  Filter,
  Brain,
  Calendar,
  Coffee,
  TrendingDown,
  TrendingUp,
  Settings,
  Edit2,
  Save,
  X,
  UserPlus,
  ScrollText,
  Minimize2,
  Maximize2,
  CloudSun,
  Wind,
  Droplets,
  MapPin,
  Navigation,
  Car,
  Bike,
  Sun,
  CloudRain,
  CloudLightning,
  Cloud,
  PieChart,
  Moon,
  Map,
  Send,
  Check
} from 'lucide-react';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  YAxis,
  Cell,
  RadialBarChart,
  RadialBar
} from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, Tooltip as LeafletTooltip, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// HRV 추이 데이터 (30분 간격)
const hrvTrendData = [
  { time: '09:00', avgHRV: 62, minHRV: 45 },
  { time: '09:30', avgHRV: 60, minHRV: 42 },
  { time: '10:00', avgHRV: 58, minHRV: 40 },
  { time: '10:30', avgHRV: 55, minHRV: 38 },
  { time: '11:00', avgHRV: 53, minHRV: 35 },
  { time: '11:30', avgHRV: 50, minHRV: 32 },
  { time: '12:00', avgHRV: 65, minHRV: 48 }, // 점심시간 회복
  { time: '12:30', avgHRV: 68, minHRV: 50 },
  { time: '13:00', avgHRV: 62, minHRV: 45 },
  { time: '13:30', avgHRV: 58, minHRV: 40 },
  { time: '14:00', avgHRV: 55, minHRV: 35 },
  { time: '14:30', avgHRV: 52, minHRV: 30 },
];

const riskData = [
  { name: '최상', value: 140, color: '#10b981' },
  { name: '주의', value: 65, color: '#f59e0b' },
  { name: '위험', value: 25, color: '#ef4444' },
];

const workers = [
  {
    id: 'K-042', name: '이민호', status: '위험', hrv: 24, hr: 98, hrvScore: 'Low', spo2: 94, activity: 'High',
    avg3DayWork: 9.5, avgTimeSlot: '22:00 - 07:00', totalFatigue: 88, sleepScore: 45,
    scoreHistory: [
      { date: '12-18', score: 45 }, { date: '12-19', score: 52 }, { date: '12-20', score: 68 }, { date: '12-21', score: 75 }, { date: '12-22', score: 88 }
    ],
    history: [35, 32, 28, 24, 25, 24],
    weeklyData: [
      { day: 'Mon', workHours: 9.5, bpm: 95, avgHrv: 45 },
      { day: 'Tue', workHours: 10.0, bpm: 98, avgHrv: 40 },
      { day: 'Wed', workHours: 9.8, bpm: 94, avgHrv: 35 },
      { day: 'Thu', workHours: 10.5, bpm: 102, avgHrv: 30 },
      { day: 'Fri', workHours: 9.2, bpm: 96, avgHrv: 25 },
      { day: 'Sat', workHours: 5.5, bpm: 88, avgHrv: 45 },
      { day: 'Sun', workHours: 0, bpm: 72, avgHrv: 60 },
    ]
  },
  {
    id: 'M-011', name: '정해인', status: '위험', hrv: 18, hr: 105, hrvScore: 'Critical', spo2: 92, activity: 'High',
    avg3DayWork: 10.2, avgTimeSlot: '23:00 - 08:00', totalFatigue: 94, sleepScore: 32,
    scoreHistory: [
      { date: '12-18', score: 60 }, { date: '12-19', score: 65 }, { date: '12-20', score: 82 }, { date: '12-21', score: 90 }, { date: '12-22', score: 94 }
    ],
    history: [30, 28, 22, 18, 19, 18],
    weeklyData: [
      { day: 'Mon', workHours: 10.5, bpm: 102, avgHrv: 35 },
      { day: 'Tue', workHours: 11.0, bpm: 108, avgHrv: 30 },
      { day: 'Wed', workHours: 10.2, bpm: 105, avgHrv: 28 },
      { day: 'Thu', workHours: 10.8, bpm: 110, avgHrv: 22 },
      { day: 'Fri', workHours: 9.5, bpm: 100, avgHrv: 32 },
      { day: 'Sat', workHours: 6.0, bpm: 92, avgHrv: 45 },
      { day: 'Sun', workHours: 2.0, bpm: 85, avgHrv: 55 },
    ]
  },
  {
    id: 'B-129', name: '박지수', status: '주의', hrv: 38, hr: 82, hrvScore: 'Med', spo2: 97, activity: 'Low',
    avg3DayWork: 8.0, avgTimeSlot: '21:00 - 06:00', totalFatigue: 62, sleepScore: 68,
    scoreHistory: [
      { date: '12-18', score: 30 }, { date: '12-19', score: 35 }, { date: '12-20', score: 45 }, { date: '12-21', score: 55 }, { date: '12-22', score: 62 }
    ],
    history: [50, 48, 42, 38, 39, 38],
    weeklyData: [
      { day: 'Mon', workHours: 8.0, bpm: 80, avgHrv: 55 },
      { day: 'Tue', workHours: 8.5, bpm: 82, avgHrv: 52 },
      { day: 'Wed', workHours: 8.2, bpm: 81, avgHrv: 50 },
      { day: 'Thu', workHours: 8.8, bpm: 84, avgHrv: 45 },
      { day: 'Fri', workHours: 7.5, bpm: 78, avgHrv: 58 },
      { day: 'Sat', workHours: 3.0, bpm: 72, avgHrv: 65 },
      { day: 'Sun', workHours: 0, bpm: 65, avgHrv: 75 },
    ]
  },
  {
    id: 'A-008', name: '최현욱', status: '정상', hrv: 62, hr: 72, hrvScore: 'High', spo2: 99, activity: 'Med',
    avg3DayWork: 7.5, avgTimeSlot: '20:00 - 05:00', totalFatigue: 32, sleepScore: 88,
    scoreHistory: [
      { date: '12-18', score: 25 }, { date: '12-19', score: 28 }, { date: '12-20', score: 30 }, { date: '12-21', score: 32 }, { date: '12-22', score: 32 }
    ],
    history: [60, 62, 61, 63, 62, 62],
    weeklyData: [
      { day: 'Mon', workHours: 7.5, bpm: 78, avgHrv: 65 },
      { day: 'Tue', workHours: 8.0, bpm: 76, avgHrv: 62 },
      { day: 'Wed', workHours: 7.0, bpm: 75, avgHrv: 68 },
      { day: 'Thu', workHours: 8.5, bpm: 80, avgHrv: 58 },
      { day: 'Fri', workHours: 6.0, bpm: 72, avgHrv: 70 },
      { day: 'Sat', workHours: 0, bpm: 68, avgHrv: 80 },
      { day: 'Sun', workHours: 0, bpm: 65, avgHrv: 85 },
    ]
  },
  {
    id: 'S-201', name: '김민준', status: '주의', hrv: 45, hr: 88, hrvScore: 'Med', spo2: 96, activity: 'Med',
    avg3DayWork: 8.8, avgTimeSlot: '18:00 - 04:00', totalFatigue: 58,
    scoreHistory: [
      { date: '12-18', score: 35 }, { date: '12-19', score: 42 }, { date: '12-20', score: 50 }, { date: '12-21', score: 55 }, { date: '12-22', score: 58 }
    ],
    history: [55, 52, 48, 45, 46, 45],
    weeklyData: [
      { day: 'Mon', workHours: 8.5, bpm: 85, avgHrv: 52 },
      { day: 'Tue', workHours: 9.0, bpm: 88, avgHrv: 48 },
      { day: 'Wed', workHours: 8.5, bpm: 86, avgHrv: 50 },
      { day: 'Thu', workHours: 9.2, bpm: 90, avgHrv: 45 },
      { day: 'Fri', workHours: 8.0, bpm: 85, avgHrv: 55 },
      { day: 'Sat', workHours: 4.0, bpm: 78, avgHrv: 60 },
      { day: 'Sun', workHours: 0, bpm: 70, avgHrv: 72 },
    ]
  },
  {
    id: 'D-105', name: '장동민', status: '주의', hrv: 42, hr: 90, hrvScore: 'Low', spo2: 95, activity: 'High',
    avg3DayWork: 9.0, avgTimeSlot: '14:00 - 23:00', totalFatigue: 65,
    scoreHistory: [
      { date: '12-18', score: 40 }, { date: '12-19', score: 48 }, { date: '12-20', score: 55 }, { date: '12-21', score: 62 }, { date: '12-22', score: 65 }
    ],
    history: [50, 48, 45, 42, 43, 42],
    weeklyData: [
      { day: 'Mon', workHours: 9.0, bpm: 90, avgHrv: 48 },
      { day: 'Tue', workHours: 9.5, bpm: 92, avgHrv: 45 },
      { day: 'Wed', workHours: 9.0, bpm: 91, avgHrv: 48 },
      { day: 'Thu', workHours: 9.8, bpm: 95, avgHrv: 42 },
      { day: 'Fri', workHours: 8.5, bpm: 88, avgHrv: 50 },
      { day: 'Sat', workHours: 5.0, bpm: 82, avgHrv: 55 },
      { day: 'Sun', workHours: 0, bpm: 75, avgHrv: 65 },
    ]
  },
];

const defaultWeeklyData = [
  { day: 'Mon', workHours: 8.5, bpm: 82 },
  { day: 'Tue', workHours: 9.2, bpm: 85 },
  { day: 'Wed', workHours: 8.8, bpm: 84 },
  { day: 'Thu', workHours: 9.5, bpm: 88 },
  { day: 'Fri', workHours: 8.0, bpm: 80 },
  { day: 'Sat', workHours: 4.0, bpm: 75 },
  { day: 'Sun', workHours: 0, bpm: 68 },
];

// Custom Icons
const carIcon = L.divIcon({
  html: `<div style="background-color: #6366f1; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>
         </div>`,
  className: '',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  tooltipAnchor: [16, -10]
});

const bikeIcon = L.divIcon({
  html: `<div style="background-color: #10b981; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="15" cy="5" r="1"/><path d="M12 17.5V14l-3-3 4-3 2 3h2"/></svg>
         </div>`,
  className: '',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  tooltipAnchor: [16, -10]
});

// Gasan-dong Coordinates
const CENTER_LAT = 37.481;
const CENTER_LNG = 126.882;

const workerNames = ["김철수", "이영희", "박지민", "최동훈", "정수진", "강현우", "조민수", "윤서연", "임재범", "한소희", "오지호", "송미경"];

const LiveMap = () => {
  const [mapWorkers, setMapWorkers] = useState([]);

  useEffect(() => {
    // Generate initial workers
    const initialWorkers = Array.from({ length: 12 }, (_, i) => ({
      id: i,
      name: workerNames[i],
      lat: CENTER_LAT + (Math.random() - 0.5) * 0.015,
      lng: CENTER_LNG + (Math.random() - 0.5) * 0.015,
      type: Math.random() > 0.5 ? 'car' : 'bike',
      dirLat: (Math.random() - 0.5) * 0.0001,
      dirLng: (Math.random() - 0.5) * 0.0001,
      hrv: Math.floor(20 + Math.random() * 60), // Mock 1h Avg HRV
      fatigue: Math.floor(10 + Math.random() * 80) // Mock Fatigue Score
    }));
    setMapWorkers(initialWorkers);

    const interval = setInterval(() => {
      setMapWorkers(prev => prev.map(w => {
        let newLat = w.lat + w.dirLat;
        let newLng = w.lng + w.dirLng;

        // Bounce off bounds
        if (Math.abs(newLat - CENTER_LAT) > 0.008) w.dirLat *= -1;
        if (Math.abs(newLng - CENTER_LNG) > 0.008) w.dirLng *= -1;

        return {
          ...w,
          lat: newLat,
          lng: newLng
        };
      }));
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <MapContainer
      center={[CENTER_LAT, CENTER_LNG]}
      zoom={15}
      style={{ height: '100%', width: '100%', borderRadius: '2rem', zIndex: 0 }}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />
      {mapWorkers.map(w => (
        <Marker
          key={w.id}
          position={[w.lat, w.lng]}
          icon={w.type === 'car' ? carIcon : bikeIcon}
        >
          <LeafletTooltip direction="top" offset={[0, -10]} opacity={1} className="custom-tooltip">
            <div className="p-2 text-center min-w-[120px]">
              <div className="font-bold text-sm mb-1 text-slate-900">{w.name}</div>
              <div className="text-xs text-slate-600 flex justify-between gap-2">
                <span>1시간 평균 HRV:</span>
                <span className="font-bold text-indigo-600">{w.hrv}ms</span>
              </div>
              <div className="text-xs text-slate-600 flex justify-between gap-2">
                <span>누적 피로 지수:</span>
                <span className={`font-bold ${w.fatigue > 70 ? 'text-red-600' : 'text-emerald-600'}`}>{w.fatigue}</span>
              </div>
            </div>
          </LeafletTooltip>
        </Marker>
      ))}
    </MapContainer>
  );
};

// --- Weather Widget with Open-Meteo ---

const WeatherWidget = () => {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=37.481&longitude=126.882&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia%2FSeoul');
        const data = await res.json();
        setWeather(data.current);
      } catch (e) {
        console.error("Failed to fetch weather", e);
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();
    const interval = setInterval(fetchWeather, 600000); // Update every 10 min
    return () => clearInterval(interval);
  }, []);

  const getWeatherInfo = (code) => {
    // WMO Weather interpretation codes (WW)
    if (code === 0) return { label: '맑음', icon: <Sun className="text-yellow-400 animate-spin-slow" size={64} />, bg: 'from-blue-400 to-blue-600' };
    if (code >= 1 && code <= 3) return { label: '구름 많음', icon: <CloudSun className="text-white" size={64} />, bg: 'from-blue-500 to-slate-400' };
    if (code >= 45 && code <= 48) return { label: '안개', icon: <Cloud className="text-slate-200" size={64} />, bg: 'from-slate-500 to-slate-700' };
    if (code >= 51 && code <= 55) return { label: '이슬비', icon: <CloudRain className="text-blue-200" size={64} />, bg: 'from-slate-700 to-blue-900' };
    if (code >= 61 && code <= 65) return { label: '비', icon: <CloudRain className="text-blue-300" size={64} />, bg: 'from-slate-800 to-blue-900' };
    if (code >= 71 && code <= 77) return { label: '눈', icon: <CloudSnow className="text-white" size={64} />, bg: 'from-slate-800 to-slate-500' };
    if (code >= 80 && code <= 82) return { label: '오락가락 비', icon: <CloudRain className="text-blue-200" size={64} />, bg: 'from-slate-700 to-blue-800' };
    if (code >= 85 && code <= 86) return { label: '눈발', icon: <CloudSnow className="text-white" size={64} />, bg: 'from-slate-700 to-slate-500' };
    if (code >= 95) return { label: '뇌우', icon: <CloudLightning className="text-yellow-300" size={64} />, bg: 'from-slate-900 to-purple-900' };

    return { label: '맑음', icon: <Sun className="text-yellow-400" size={64} />, bg: 'from-blue-400 to-blue-600' };
  };

  if (loading || !weather) {
    return (
      <div className="bg-[#1e293b] p-8 rounded-[2rem] border border-slate-800 shadow-xl h-[400px] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const { label, icon, bg } = getWeatherInfo(weather.weather_code);
  const isNight = new Date().getHours() >= 19 || new Date().getHours() <= 6;
  const backgroundClass = isNight ? 'bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700' : `bg-gradient-to-br ${bg} border-transparent`;

  return (
    <div className={`${backgroundClass} p-8 rounded-[2rem] shadow-xl flex flex-col justify-between overflow-hidden relative group h-[400px] transition-all duration-1000 border`}>
      {/* Background Effects */}
      <div className="absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-gradient-to-b from-white/10 to-transparent rotate-45 pointer-events-none"></div>
      {isNight && <div className="absolute top-10 right-10 w-20 h-20 bg-yellow-100/20 rounded-full blur-xl"></div>}

      <div className="flex justify-between items-start relative z-10">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2 drop-shadow-md"><MapPin size={18} /> 서울시 금천구 가산동</h3>
          <p className="text-sm text-white/70 mt-1 font-medium">{new Date().toLocaleDateString('ko-KR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center my-4 relative z-10">
        <div className="mb-4 drop-shadow-2xl filter">{icon}</div>
        <div className="text-6xl font-black text-white tracking-tighter drop-shadow-lg">{Math.round(weather.temperature_2m)}°</div>
        <p className="text-xl font-bold text-white/90 drop-shadow-md">{label}</p>
        <p className="text-sm text-white/70 mt-1">체감 {Math.round(weather.apparent_temperature)}°</p>
      </div>

      <div className="grid grid-cols-2 gap-4 relative z-10">
        <div className="bg-black/20 backdrop-blur-md p-4 rounded-2xl border border-white/10 hover:bg-black/30 transition-colors">
          <div className="flex items-center gap-2 text-white/70 mb-1">
            <Droplets size={14} /> <span className="text-xs font-bold">습도</span>
          </div>
          <p className="text-lg font-bold text-white">{weather.relative_humidity_2m}%</p>
        </div>
        <div className="bg-black/20 backdrop-blur-md p-4 rounded-2xl border border-white/10 hover:bg-black/30 transition-colors">
          <div className="flex items-center gap-2 text-white/70 mb-1">
            <Wind size={14} /> <span className="text-xs font-bold">풍속</span>
          </div>
          <p className="text-lg font-bold text-white">{weather.wind_speed_10m} <span className="text-xs font-normal">km/h</span></p>
        </div>
      </div>
    </div>
  );
};


// --- Sub Components ---

const DashboardView = () => {
  const [selectedWorker, setSelectedWorker] = useState(null);

  const averageWeeklyData = useMemo(() => {
    // 1. Initialize sums
    const sums = {
      Mon: { workHours: 0, bpm: 0, count: 0 },
      Tue: { workHours: 0, bpm: 0, count: 0 },
      Wed: { workHours: 0, bpm: 0, count: 0 },
      Thu: { workHours: 0, bpm: 0, count: 0 },
      Fri: { workHours: 0, bpm: 0, count: 0 },
      Sat: { workHours: 0, bpm: 0, count: 0 },
      Sun: { workHours: 0, bpm: 0, count: 0 }
    };

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // 2. Sum up data from all workers who have weeklyData
    workers.forEach(worker => {
      if (worker.weeklyData) {
        worker.weeklyData.forEach(d => {
          if (sums[d.day]) {
            sums[d.day].workHours += d.workHours;
            sums[d.day].bpm += d.bpm;
            sums[d.day].count += 1;
          }
        });
      }
    });

    // 3. specific ordering
    return days.map(day => ({
      day,
      workHours: sums[day].count ? parseFloat((sums[day].workHours / sums[day].count).toFixed(1)) : 0,
      bpm: sums[day].count ? Math.round(sums[day].bpm / sums[day].count) : 0
    }));
  }, []);

  const riskDistribution = useMemo(() => [
    { name: '고위험', value: 15, fill: '#ef4444' },
    { name: '주의', value: 45, fill: '#f59e0b' },
    { name: '정상', value: 132, fill: '#10b981' }
  ], []);

  return (
    <div className="animate-in fade-in duration-500">
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Dashboard Monitor</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* 1. Live Workers */}
        <div className="bg-white p-6 rounded-3xl border-2 border-indigo-200 shadow-lg shadow-indigo-100/50">
          <div className="flex justify-between items-start mb-4 text-indigo-600">
            <div className="p-3 bg-indigo-50 rounded-2xl border border-indigo-100"><Users size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-indigo-50 rounded-md">LIVE</span>
          </div>
          <h3 className="text-slate-500 text-sm mb-1 font-bold">현장 인력 현황</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800 tracking-tighter">192/230</span>
            <span className="text-slate-500 text-xs font-bold">명</span>
          </div>
        </div>

        {/* 2. HRV */}
        <div className="bg-white p-6 rounded-3xl border-2 border-pink-200 shadow-lg shadow-pink-100/50">
          <div className="flex justify-between items-start mb-4 text-pink-600">
            <div className="p-3 bg-pink-50 rounded-2xl border border-pink-100"><Activity size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-pink-50 rounded-md">AVG HRV</span>
          </div>
          <h3 className="text-slate-500 text-sm mb-1 font-bold">평균 심박변이도</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800 tracking-tighter">54.2</span>
            <span className="text-slate-500 text-sm font-bold">ms</span>
          </div>
        </div>

        {/* 3. Sleep */}
        <div className="bg-white p-6 rounded-3xl border-2 border-violet-200 shadow-lg shadow-violet-100/50">
          <div className="flex justify-between items-start mb-4 text-violet-600">
            <div className="p-3 bg-violet-50 rounded-2xl border border-violet-100"><Brain size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-violet-50 rounded-md">SLEEP</span>
          </div>
          <h3 className="text-slate-500 text-sm mb-1 font-bold">평균 수면 점수</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800 tracking-tighter">78</span>
            <span className="text-slate-500 text-xs font-bold">점</span>
          </div>
        </div>

        {/* 4. Fatigue */}
        <div className="bg-white p-6 rounded-3xl border-2 border-amber-200 shadow-lg shadow-amber-100/50">
          <div className="flex justify-between items-start mb-4 text-amber-600">
            <div className="p-3 bg-amber-50 rounded-2xl border border-amber-100"><Zap size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-amber-50 rounded-md">FATIGUE</span>
          </div>
          <h3 className="text-slate-500 text-sm mb-1 font-bold">누적 피로 지수</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-slate-800 tracking-tighter">72/100</span>
            <span className="text-amber-500 text-xs font-bold ml-1">주의</span>
          </div>
        </div>
      </div>

      {/* Middle Section: Trend (Placeholder) BUT NO RISK LIST YET */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div className="lg:col-span-2 bg-white p-8 rounded-[2rem] border border-slate-200 shadow-xl shadow-slate-200/50">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-xl font-black text-slate-800 italic tracking-tight flex items-center gap-2">
                <TrendingDown className="text-indigo-600" /> 주간 과로 지수 트렌드
              </h3>
              <p className="text-sm text-slate-500 font-bold mt-1">고강도 작업 시간 및 평균 심박수 분석</p>
            </div>
          </div>
          <div className="h-[400px] w-full bg-slate-50 rounded-2xl border border-slate-100 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={selectedWorker ? selectedWorker.weeklyData : averageWeeklyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorWork" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorBpm" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ec4899" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ec4899" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 'bold' }} dy={10} />
                <YAxis yAxisId="left" orientation="left" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 'bold' }} />
                <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12, fontWeight: 'bold' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                  cursor={{ fill: '#f8fafc' }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
                <Bar yAxisId="left" dataKey="workHours" name="Work Hours" fill="url(#colorWork)" radius={[6, 6, 0, 0]} barSize={20} />
                <Bar yAxisId="right" dataKey="bpm" name="Avg Heart Rate" fill="url(#colorBpm)" radius={[6, 6, 0, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk List */}
        <div className="glass-card p-8 rounded-[2rem] flex flex-col h-[630px]">
          <h3 className="text-xl font-black text-slate-800 mb-6 tracking-tight flex items-center justify-between">
            <span>과로 위험자 리스트</span>
            <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-lg">High Risk</span>
          </h3>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
            {workers
              .sort((a, b) => b.totalFatigue - a.totalFatigue)
              .map((worker) => (
                <div
                  key={worker.id}
                  onClick={() => setSelectedWorker(worker)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group ${selectedWorker?.id === worker.id ? 'bg-indigo-50 border-indigo-200 shadow-md' : 'bg-slate-50 border-slate-100 hover:bg-slate-100'}`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-lg ${worker.totalFatigue >= 80 ? 'bg-red-500 shadow-red-200' : 'bg-amber-500 shadow-amber-200'}`}>
                      {worker.totalFatigue}
                    </div>
                    <div>
                      <div className="font-bold text-slate-800 text-sm">{worker.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{worker.id}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400 font-bold mb-0.5">HRV</p>
                    <p className={`font-black ${worker.hrv < 30 ? 'text-red-500' : 'text-slate-700'}`}>{worker.hrv}</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Bottom Section: Risk Distribution & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div className="lg:col-span-1 glass-card p-8 rounded-[2rem] flex flex-col h-[400px]">
          <h3 className="text-xl font-black text-slate-800 mb-2 tracking-tight flex items-center gap-2">
            <PieChart className="text-indigo-600" size={24} /> 과로 위험도 분포
          </h3>
          <p className="text-sm text-slate-500 font-bold mb-6">전체 근로자 위험 수준 비율 (Total: 192)</p>
          <div className="flex-1 w-full relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart innerRadius="20%" outerRadius="100%" data={riskDistribution} startAngle={180} endAngle={0} barSize={20}>
                <RadialBar minAngle={15} label={{ position: 'insideStart', fill: '#fff', fontSize: '10px', fontWeight: 'bold' }} background clockWise dataKey="value" />
                <Legend iconSize={10} layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ fontSize: '12px', fontWeight: 'bold', color: '#64748b' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-2 glass-card p-8 rounded-[2rem] flex flex-col h-[400px]">
          <h3 className="text-xl font-black text-slate-800 mb-6 tracking-tight flex items-center justify-between">
            <span className="flex items-center gap-2"><Bell className="text-rose-500 animate-pulse" /> 실시간 이슈 알림</span>
            <span className="text-xs bg-rose-100 text-rose-600 px-3 py-1 rounded-full animate-pulse border border-rose-200">LIVE FEED</span>
          </h3>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {[
              { id: 1, type: 'critical', msg: '이명호 근로자 심박 급상승 감지 (165 BPM)', time: '방금 전', worker: '이명호' },
              { id: 2, type: 'info', msg: '이종민 근로자 금일 근무 시작 (현장 진입)', time: '2분 전', worker: '이종민' },
              { id: 3, type: 'warning', msg: '박지수 근로자 금일 근무 9시간 초과', time: '10분 전', worker: '박지수' },
              { id: 4, type: 'info', msg: '김양욱 근로자 수면 시간 입력 완료 (6.5시간)', time: '15분 전', worker: '김양욱' },
              { id: 5, type: 'critical', msg: '최현욱 근로자 HRV 수치 극저하 (28ms) - 휴식 권고', time: '18분 전', worker: '최현욱' },
              { id: 6, type: 'warning', msg: '김민준 근로자 연속 작업 4시간 경과', time: '25분 전', worker: '김민준' },
              { id: 7, type: 'critical', msg: '장동민 근로자 움직임 감지 안됨 (10분)', time: '30분 전', worker: '장동민' },
            ].map((alert) => (
              <div key={alert.id} className={`flex items-center justify-between p-4 rounded-2xl border transition-all hover:scale-[1.01] ${alert.type === 'critical' ? 'bg-red-50 border-red-100 hover:bg-red-100/50' : alert.type === 'warning' ? 'bg-amber-50 border-amber-100 hover:bg-amber-100/50' : 'bg-emerald-50 border-emerald-100 hover:bg-emerald-100/50'}`}>
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${alert.type === 'critical' ? 'bg-red-500 text-white shadow-lg shadow-red-200' : alert.type === 'warning' ? 'bg-amber-500 text-white shadow-lg shadow-amber-200' : 'bg-emerald-500 text-white shadow-lg shadow-emerald-200'}`}>
                    {alert.type === 'critical' ? <AlertTriangle size={20} /> : alert.type === 'warning' ? <Clock size={20} /> : <UserCheck size={20} />}
                  </div>
                  <div>
                    <p className={`text-sm font-black ${alert.type === 'critical' ? 'text-red-700' : alert.type === 'warning' ? 'text-amber-700' : 'text-emerald-700'}`}>{alert.msg}</p>
                    <p className="text-xs text-slate-500 font-mono flex items-center gap-1 mt-0.5"><Clock size={10} /> {alert.time} • {alert.worker}</p>
                  </div>
                </div>
                {alert.type !== 'info' && <button className={`text-xs font-black px-3 py-1.5 rounded-lg border transition-colors ${alert.type === 'critical' ? 'bg-white text-red-600 border-red-200 hover:bg-red-50' : 'bg-white text-amber-600 border-amber-200 hover:bg-amber-50'}`}>조치 필요</button>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const WorkersListView = ({ searchQuery, setSearchQuery }) => {
  const [sortOption, setSortOption] = useState('riskDesc');

  const riskMap = useMemo(() => ({ '위험': 3, '주의': 2, '정상': 1 }), []);

  const sortedWorkers = useMemo(() => {
    return [...workers].filter(w => w.name.includes(searchQuery)).sort((a, b) => {
      if (sortOption === 'riskDesc') return riskMap[b.status] - riskMap[a.status];
      if (sortOption === 'riskAsc') return riskMap[a.status] - riskMap[b.status];
      if (sortOption === 'nameAsc') return a.name.localeCompare(b.name);
      if (sortOption === 'nameDesc') return b.name.localeCompare(a.name);
      return 0;
    });
  }, [workers, searchQuery, sortOption, riskMap]);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white/70 backdrop-blur-xl p-4 rounded-3xl border border-white/50 shadow-lg shadow-slate-200/50">
        <div className="relative w-full md:w-96 group">
          <div className="absolute inset-0 bg-indigo-500/5 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={20} />
          <input
            type="text"
            placeholder="근로자 이름 검색..."
            className="w-full bg-white/80 border border-slate-200 rounded-2xl py-3.5 pl-12 pr-4 text-sm font-bold text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all shadow-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
            className="px-5 py-3.5 bg-white border border-slate-200 rounded-2xl text-slate-600 font-bold text-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 shadow-sm cursor-pointer hover:bg-slate-50 transition-all appearance-none"
          >
            <option value="riskDesc">위험도 높은순</option>
            <option value="riskAsc">위험도 낮은순</option>
            <option value="nameAsc">이름 오름차순</option>
            <option value="nameDesc">이름 내림차순</option>
          </select>
          <button className="p-3.5 bg-indigo-50 rounded-2xl text-indigo-600 hover:bg-indigo-100 hover:scale-105 transition-all shadow-sm border border-indigo-100">
            <Filter size={20} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-20">
        {sortedWorkers.map((worker) => (
          <div key={worker.id} className="bg-white/80 backdrop-blur-xl rounded-[2.5rem] p-8 border border-white/60 shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:shadow-indigo-500/10 hover:border-indigo-100 hover:-translate-y-1 transition-all duration-300 group relative overflow-hidden">

            {/* Background Decoration */}
            <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-[80px] opacity-20 -translate-y-1/2 translate-x-1/4 pointer-events-none transition-colors duration-500 ${worker.status === '위험' ? 'bg-red-500' : worker.status === '주의' ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>

            <div className="flex items-start justify-between mb-8 relative z-10">
              <div className="flex items-center gap-5">
                <div className="w-18 h-18 p-1 rounded-3xl bg-gradient-to-br from-slate-100 to-white border border-slate-100 shadow-inner">
                  <div className="w-full h-full bg-white rounded-2xl flex items-center justify-center border border-slate-100 shadow-sm group-hover:scale-95 transition-transform">
                    <UserCheck className={`transition-colors duration-300 ${worker.status === '위험' ? 'text-red-500' : 'text-slate-400'}`} size={32} />
                  </div>
                </div>
                <div>
                  <h4 className="text-2xl font-black text-slate-800 flex items-center gap-2">
                    {worker.name}
                    <span className="px-2 py-0.5 rounded-lg bg-slate-100 text-[10px] text-slate-500 font-mono border border-slate-200">{worker.id}</span>
                  </h4>
                  <p className="text-sm text-slate-500 font-medium mt-1 flex items-center gap-1"><ShieldCheck size={14} /> Zone B-04 Control Area</p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-2xl text-xs font-black uppercase tracking-wide border shadow-sm backdrop-blur-sm ${worker.status === '위험' ? 'bg-red-50 text-red-600 border-red-100' :
                worker.status === '주의' ? 'bg-amber-50 text-amber-600 border-amber-100' :
                  'bg-emerald-50 text-emerald-600 border-emerald-100'
                }`}>
                {worker.status}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-8 relative z-10">
              <div className="bg-slate-50/50 p-5 rounded-3xl border border-slate-100 hover:bg-white hover:border-indigo-100 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 group/item">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1 group-hover/item:text-indigo-500 transition-colors">HRV</span>
                <span className="text-2xl font-black text-slate-800">{worker.hrv}<span className="text-sm text-slate-400 ml-0.5 font-bold">ms</span></span>
              </div>
              <div className="bg-slate-50/50 p-5 rounded-3xl border border-slate-100 hover:bg-white hover:border-pink-100 hover:shadow-lg hover:shadow-pink-500/5 transition-all duration-300 group/item">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1 group-hover/item:text-pink-500 transition-colors">HR</span>
                <span className="text-2xl font-black text-slate-800">{worker.hr}<span className="text-sm text-slate-400 ml-0.5 font-bold">bpm</span></span>
              </div>
              <div className="bg-slate-50/50 p-5 rounded-3xl border border-slate-100 hover:bg-white hover:border-emerald-100 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300 group/item">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-1 group-hover/item:text-emerald-500 transition-colors">SpO2</span>
                <span className="text-2xl font-black text-slate-800">{worker.spo2}<span className="text-sm text-slate-400 ml-0.5 font-bold">%</span></span>
              </div>
            </div>

            <div className="h-64 w-full bg-slate-50 rounded-3xl p-5 border border-slate-100 overflow-hidden relative group-hover:bg-white transition-colors">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[12px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div> 주간 과로 지수 (Weekly Overwork Index)
                </span>
                <span className="px-2 py-1 rounded-lg bg-indigo-50 text-[10px] font-black text-indigo-600 border border-indigo-100">Live Analysis</span>
              </div>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={worker.weeklyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id={`barGradient-${worker.id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.8} />
                      <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.4} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} />
                  <Tooltip
                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', backgroundColor: 'rgba(255, 255, 255, 0.9)', padding: '12px' }}
                    itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                    cursor={{ fill: '#f1f5f9', opacity: 0.5 }}
                  />
                  <Bar
                    dataKey="workHours"
                    name="고강도 작업(시간)"
                    fill={`url(#barGradient-${worker.id})`}
                    radius={[6, 6, 6, 6]}
                    barSize={12}
                  />
                  <Bar
                    dataKey="avgHrv"
                    name="평균 HRV"
                    fill="#6366f1"
                    radius={[6, 6, 6, 6]}
                    barSize={6}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const FatigueAnalysisView = ({ searchQuery }) => (
  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
    {/* Analysis Grid */}
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
      {workers.filter(w => w.name.includes(searchQuery)).map((worker) => (
        <div key={worker.id} className="bg-white/80 backdrop-blur-xl rounded-[2.5rem] border border-white/50 p-8 shadow-xl shadow-slate-200/50 hover:shadow-indigo-500/10 hover:border-indigo-100 transition-all group">
          <div className="flex justify-between items-start mb-10">
            <div className="flex items-center gap-6">
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-50 to-white rounded-[2rem] flex items-center justify-center border border-indigo-100 shadow-inner">
                  <Brain className={worker.totalFatigue > 80 ? 'text-red-500' : 'text-amber-500'} size={40} />
                </div>
                <div className={`absolute -bottom-2 -right-2 w-10 h-10 rounded-full flex items-center justify-center font-black text-sm border-4 border-white shadow-lg ${worker.totalFatigue > 80 ? 'bg-red-500 text-white' : 'bg-amber-500 text-white'}`}>
                  {worker.totalFatigue}
                </div>
              </div>
              <div>
                <h3 className="text-2xl font-black text-slate-800 uppercase tracking-tight">{worker.name} 피로 정밀 분석</h3>
                <div className="flex items-center gap-3 mt-1 text-slate-500 font-mono text-sm">
                  <span className="flex items-center gap-1 font-bold text-indigo-600"><ShieldCheck size={14} /> AI Verified</span>
                  <span className="text-slate-300">|</span>
                  <span className="font-bold text-slate-400">Last Synced: Just Now</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Fatigue Status</p>
              <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-tighter shadow-sm border ${worker.totalFatigue > 80 ? 'bg-red-50 text-red-600 border-red-100' : 'bg-amber-50 text-amber-600 border-amber-100'}`}>
                {worker.totalFatigue > 80 ? 'CRITICAL RISK' : 'HIGH CAUTION'}
              </span>
            </div>
          </div>

          {/* Variable Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
            <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 group-hover:bg-white transition-colors">
              <Heart className="text-pink-500 mb-2" size={20} />
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Heart Rate</p>
              <p className="text-xl font-black text-slate-800">{worker.hr} <span className="text-xs font-normal text-slate-400 opacity-80">BPM</span></p>
            </div>
            <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 group-hover:bg-white transition-colors">
              <Activity className="text-indigo-500 mb-2" size={20} />
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">HRV (Avg)</p>
              <p className="text-xl font-black text-slate-800">{worker.hrv} <span className="text-xs font-normal text-slate-400 opacity-80">ms</span></p>
            </div>
            <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 group-hover:bg-white transition-colors">
              <Clock className="text-emerald-500 mb-2" size={20} />
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">3D Avg Work</p>
              <p className="text-xl font-black text-slate-800">{worker.avg3DayWork} <span className="text-xs font-normal text-slate-400 opacity-80">Hrs</span></p>
            </div>
            <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 group-hover:bg-white transition-colors">
              <Calendar className="text-amber-500 mb-2" size={20} />
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Work Slot</p>
              <p className="text-sm font-black text-slate-800 leading-tight">{worker.avgTimeSlot}</p>
            </div>
            <div className="bg-slate-50 p-5 rounded-3xl border border-slate-100 group-hover:bg-white transition-colors">
              <Moon className="text-violet-500 mb-2" size={20} />
              <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Sleep Score</p>
              <p className="text-xl font-black text-slate-800">{worker.sleepScore} <span className="text-xs font-normal text-slate-400 opacity-80">/100</span></p>
            </div>
          </div>

          {/* Score History Chart */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-black text-slate-600 uppercase tracking-widest flex items-center gap-2">
                <TrendingUp size={16} className="text-rose-500" /> Fatigue Score History
              </h4>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-rose-500 shadow-sm shadow-rose-200"></div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">Daily Score</span>
                </div>
              </div>
            </div>
            <div className="h-48 w-full bg-white rounded-[2rem] border border-slate-100 p-6 overflow-hidden shadow-sm">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={worker.scoreHistory}>
                  <defs>
                    <linearGradient id={`score-grad-${worker.id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} /><stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} dy={10} />
                  <YAxis hide domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold', color: '#1e293b' }}
                    itemStyle={{ color: '#f43f5e' }}
                    cursor={{ stroke: '#f43f5e', strokeWidth: 1, strokeDasharray: '4 4' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#f43f5e"
                    strokeWidth={3}
                    fill={`url(#score-grad-${worker.id})`}
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Action */}
          <div className="mt-8 flex items-center justify-between p-5 bg-gradient-to-r from-amber-50 to-orange-50 rounded-[1.5rem] border border-amber-100/50">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white rounded-lg text-amber-500 shadow-sm">
                <Coffee size={20} />
              </div>
              <div>
                <p className="text-xs font-bold text-amber-900">AI 권고 조치</p>
                <p className="text-[10px] text-amber-700 font-bold">수면 부채 및 심박 이상 감지: 15분 이상의 즉각 휴식 필요</p>
              </div>
            </div>
            <button className="px-5 py-2.5 bg-indigo-600 text-white text-[10px] font-black rounded-xl hover:bg-indigo-500 transition-all uppercase tracking-tight shadow-md shadow-indigo-200">
              Send Alert
            </button>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const FlyToWorker = ({ coords }) => {
  const map = useMap();
  useEffect(() => {
    if (coords) {
      map.flyTo(coords, 16, { duration: 1.5 });
    }
  }, [coords, map]);
  return null;
};

const LiveMapView = () => {
  const [mapWorkers, setMapWorkers] = useState(() => {
    // Generate map workers from real data + dummy data
    const baseLat = 37.4979;
    const baseLng = 127.0276;

    const realWorkers = workers.map(w => ({
      id: w.id,
      name: w.name,
      status: w.status === '위험' ? 'danger' : w.status === '주의' ? 'warn' : 'safe',
      bpm: w.hr,
      load: w.status === '위험' ? 90 + Math.floor(Math.random() * 10) :
        w.status === '주의' ? 70 + Math.floor(Math.random() * 10) :
          40 + Math.floor(Math.random() * 20),
      battery: Math.floor(Math.random() * 40 + 60),
      lat: baseLat + (Math.random() - 0.5) * 0.008, // Clusters near center
      lng: baseLng + (Math.random() - 0.5) * 0.008,
    }));

    const dummyNames = [
      "김도윤", "이하준", "박서준", "최지우", "정민재", "강현우", "조예준", "윤시우",
      "장하은", "임서윤", "한지안", "오서현", "서민지", "신채원", "권소율", "황다은"
    ];

    const dummyWorkers = dummyNames.map((name, i) => {
      const statuses = ['safe', 'safe', 'warn', 'safe', 'danger'];
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      const hr = status === 'danger' ? 160 + Math.floor(Math.random() * 30) :
        status === 'warn' ? 130 + Math.floor(Math.random() * 20) :
          70 + Math.floor(Math.random() * 40);

      return {
        id: `dummy-${i}`,
        name: name,
        status: status,
        bpm: hr,
        load: Math.floor(hr / 2 + (Math.random() * 10)),
        battery: Math.floor(Math.random() * 100),
        lat: baseLat + (Math.random() - 0.5) * 0.02, // Spread out more
        lng: baseLng + (Math.random() - 0.5) * 0.02,
      };
    });

    return [...realWorkers, ...dummyWorkers];
  });
  const [filter, setFilter] = useState('all');
  const [flyCoords, setFlyCoords] = useState(null);

  // Real-time movement simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setMapWorkers(prev => prev.map(w => ({
        ...w,
        lat: w.lat + (Math.random() - 0.5) * 0.0002,
        lng: w.lng + (Math.random() - 0.5) * 0.0002
      })));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const filteredWorkers = filter === 'all' ? mapWorkers : mapWorkers.filter(w => w.status === filter);

  const getStatusColor = (status) => {
    if (status === 'danger') return '#EF4444';
    if (status === 'warn') return '#F59E0B';
    return '#22C55E';
  };

  return (
    <div className="relative h-[calc(100vh-140px)] w-full rounded-3xl overflow-hidden border border-slate-200 shadow-xl bg-slate-50">
      <style>{`
        .marker-inner {
          width: 100%; height: 100%;
          display: flex; justify-content: center; align-items: center;
          color: white; font-size: 1rem; border-radius: 50%;
          border: 3px solid white; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
          transition: transform 0.2s;
        }
        .inner-danger { background: #EF4444; animation: bounce 1s infinite; }
        .inner-warn { background: #F59E0B; }
        .inner-safe { background: #22C55E; }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
      `}</style>

      <MapContainer center={[37.4979, 127.0276]} zoom={14} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        <FlyToWorker coords={flyCoords} />

        {/* Heatmap Simulation Circle */}
        <Circle
          center={[37.5010, 127.0260]}
          radius={400}
          pathOptions={{ color: 'red', fillColor: '#f03', fillOpacity: 0.2, stroke: false }}
        >
          <LeafletTooltip direction="center" permanent className="font-bold text-red-600 bg-white/90 border-red-200 px-2 py-1 rounded shadow-sm text-xs">
            ⚠️ 고부하 집중 구역
          </LeafletTooltip>
        </Circle>

        {filteredWorkers.map(w => (
          <Marker
            key={w.id}
            position={[w.lat, w.lng]}
            icon={L.divIcon({
              className: 'bg-transparent border-none',
              html: `<div class="marker-inner inner-${w.status}"><div style="font-size:12px;">🚴</div></div>`,
              iconSize: [36, 36],
              iconAnchor: [18, 36],
              popupAnchor: [0, -36]
            })}
          >
            <Popup className="rounded-xl overflow-hidden shadow-xl">
              <div className="w-[200px] font-sans">
                <div className="bg-slate-800 text-white p-3 font-bold text-sm flex justify-between items-center">
                  <span>{w.name} (라이더)</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${w.status === 'danger' ? 'bg-red-500' : 'bg-green-500'}`}>{w.status.toUpperCase()}</span>
                </div>
                <div className="p-4 space-y-2">
                  <div className="flex justify-between text-xs"><span className="text-slate-500">심박수</span> <span className="font-bold" style={{ color: getStatusColor(w.status) }}>{w.bpm} bpm</span></div>
                  <div className="flex justify-between text-xs"><span className="text-slate-500">부하량</span> <span className="font-bold">{w.load}%</span></div>
                  <div className="flex justify-between text-xs"><span className="text-slate-500">배터리</span> <span className="font-bold">{w.battery}%</span></div>
                  <button className="w-full mt-2 py-1.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 transition-colors">
                    메시지 전송
                  </button>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Floating Panel (Sidebar) */}
      <div className="absolute top-5 right-5 w-80 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-slate-200 z-[1000] flex flex-col max-h-[calc(100%-40px)] animate-in slide-in-from-right-10 duration-500">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h3 className="font-bold text-slate-800">작업자 리스트</h3>
            <p className="text-xs text-slate-400 font-bold mt-0.5">총 {mapWorkers.length}명 접속 중</p>
          </div>
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse box-content border-2 border-green-200"></div>
        </div>

        <div className="flex p-3 gap-2 border-b border-slate-100 bg-slate-50/50">
          <button onClick={() => setFilter('all')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors border ${filter === 'all' ? 'bg-white text-indigo-600 border-indigo-200 shadow-sm' : 'text-slate-500 border-transparent hover:bg-white/50'}`}>전체</button>
          <button onClick={() => setFilter('danger')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors border ${filter === 'danger' ? 'bg-red-50 text-red-600 border-red-200 shadow-sm' : 'text-slate-500 border-transparent hover:bg-white/50'}`}>위험 ({mapWorkers.filter(w => w.status === 'danger').length})</button>
          <button onClick={() => setFilter('warn')} className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-colors border ${filter === 'warn' ? 'bg-amber-50 text-amber-600 border-amber-200 shadow-sm' : 'text-slate-500 border-transparent hover:bg-white/50'}`}>주의 ({mapWorkers.filter(w => w.status === 'warn').length})</button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
          {filteredWorkers.map(w => (
            <div
              key={w.id}
              onClick={() => setFlyCoords([w.lat, w.lng])}
              className="p-3 bg-white border border-slate-100 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${w.status === 'danger' ? 'bg-red-500' : w.status === 'warn' ? 'bg-amber-500' : 'bg-green-500'}`}></div>
                <div>
                  <div className="text-sm font-bold text-slate-700 group-hover:text-indigo-700">{w.name}</div>
                  <div className="text-[10px] text-slate-400 font-mono">Load: {w.load}%</div>
                </div>
              </div>
              <div className={`text-xs font-black ${w.status === 'danger' ? 'text-red-600' : w.status === 'warn' ? 'text-amber-600' : 'text-slate-600'}`}>
                {w.bpm} <span className="text-[10px] font-normal text-slate-400">bpm</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-5 left-5 bg-white/90 backdrop-blur rounded-xl shadow-lg border border-slate-200 p-4 z-[1000]">
        <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Map Legend</h4>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <div className="w-3 h-3 rounded-full bg-green-500"></div> 안정 (심박부하 60% 미만)
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <div className="w-3 h-3 rounded-full bg-amber-500"></div> 주의 (심박부하 60~80%)
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div> 위험 (심박부하 80% 초과)
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-slate-600 mt-2 pt-2 border-t border-slate-100">
            <div className="w-3 h-3 rounded-full border border-red-500 bg-red-500/20"></div> 과부하 집중 구역
          </div>
        </div>
      </div>
    </div>
  );
};


const SubjectRegistrationModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    birth_year: '',
    gender: '남성',
    height: '',
    weight: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/manager/administration/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();

      if (data.success) {
        onSuccess();
        onClose();
        setFormData({ full_name: '', phone_number: '', birth_year: '', gender: '남성', height: '', weight: '' });
      } else {
        setError(data.error || '등록 실패');
      }
    } catch (err) {
      setError('서버 통신 오류');
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm" onClick={onClose}></div>
      <div className="bg-[#1e293b] w-full max-w-lg rounded-[2rem] border border-slate-700 shadow-2xl relative z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-300">
        <div className="p-8 border-b border-slate-700/50 flex justify-between items-center">
          <h3 className="text-2xl font-black text-white uppercase tracking-tight">신규 대상자 등록</h3>
          <button onClick={onClose} className="p-2 hover:bg-slate-700 rounded-full transition-colors"><X size={24} className="text-slate-400" /></button>
        </div>

        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {error && <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-bold flex items-center gap-2"><AlertTriangle size={16} /> {error}</div>}

          <div className="grid grid-cols-2 gap-6">
            <div className="col-span-2">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">이름</label>
              <input required name="full_name" value={formData.full_name} onChange={handleChange} type="text" className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="홍길동" />
            </div>

            <div className="col-span-2">
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">전화번호</label>
              <input required name="phone_number" value={formData.phone_number} onChange={handleChange} type="tel" className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="010-1234-5678" />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">출생연도</label>
              <input required name="birth_year" value={formData.birth_year} onChange={handleChange} type="number" className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="1990" />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">성별</label>
              <select name="gender" value={formData.gender} onChange={handleChange} className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all appearance-none">
                <option value="남성">남성</option>
                <option value="여성">여성</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">키 (cm)</label>
              <input name="height" value={formData.height} onChange={handleChange} type="number" step="0.1" className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="175.5" />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">체중 (kg)</label>
              <input name="weight" value={formData.weight} onChange={handleChange} type="number" step="0.1" className="w-full bg-slate-900/50 border border-slate-700 rounded-xl py-3 px-4 text-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="70.0" />
            </div>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-6 py-3 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700 transition-all">취소</button>
            <button type="submit" disabled={loading} className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2">
              {loading && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>}
              대상자 등록
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
};

const SubjectsView = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    try {
      setLoading(true);
      const response = await fetch('/manager/administration/subjects/');
      const data = await response.json();

      if (data.success) {
        setSubjects(data.subjects);
      } else {
        setError(data.error || '대상자 목록을 불러오는데 실패했습니다.');
      }
    } catch (err) {
      console.error('Error fetching subjects:', err);
      setError('서버 통신 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const filteredSubjects = subjects.filter(subject =>
    subject.full_name.includes(searchTerm) ||
    subject.username.includes(searchTerm)
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex justify-between items-center bg-white/60 p-8 rounded-[2rem] border border-white/60 backdrop-blur-xl shadow-sm hover:shadow-md transition-all">
        <div>
          <h2 className="text-3xl font-black text-slate-800 tracking-tight mb-2 flex items-center gap-2">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-indigo-800 to-slate-900">대상자 관리</span>
          </h2>
          <p className="text-slate-500 font-bold">등록된 대상자 정보를 조회하고 관리합니다.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="flex items-center gap-2 px-6 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold transition-all shadow-lg shadow-indigo-600/20 hover:scale-105 active:scale-95">
          <UserPlus size={20} />
          <span>신규 대상자 등록</span>
        </button>
      </div>

      <SubjectRegistrationModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSuccess={fetchSubjects} />

      <div className="glass-card rounded-[2rem] overflow-hidden flex flex-col min-h-[600px]">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-white/50">
          <div className="relative w-96 group">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={20} />
            <input
              type="text"
              placeholder="이름 또는 ID 검색..."
              className="w-full bg-white border-2 border-slate-100 rounded-2xl py-3 pl-14 pr-4 text-sm text-slate-800 focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all font-bold placeholder:font-normal"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500 font-bold bg-slate-100 px-4 py-2 rounded-xl">
            <Users size={16} className="text-slate-400" />
            <span>총 <span className="text-indigo-600">{filteredSubjects.length}</span>명</span>
          </div>
        </div>

        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 text-slate-500 text-xs uppercase tracking-wider font-extrabold border-b border-slate-100">
                <th className="px-8 py-5">사용자 정보</th>
                <th className="px-6 py-5">성별/나이</th>
                <th className="px-6 py-5">신체 정보</th>
                <th className="px-6 py-5">생년월일</th>
                <th className="px-8 py-5 text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white/40">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-20 text-center text-slate-500">
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                      <span className="font-bold animate-pulse">데이터를 불러오는 중입니다...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredSubjects.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-20 text-center">
                    <div className="flex flex-col items-center gap-2 opacity-50">
                      <Search size={48} className="text-slate-300 mb-2" />
                      <span className="text-lg font-bold text-slate-400">검색 결과가 없습니다.</span>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredSubjects.map((subject) => (
                  <tr key={subject.username} className="hover:bg-indigo-50/50 transition-colors group">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center text-indigo-600 font-black text-lg border border-indigo-100 shadow-sm group-hover:scale-110 group-hover:shadow-md transition-all duration-300">
                          {subject.full_name[0]}
                        </div>
                        <div>
                          <div className="font-black text-slate-800 text-base">{subject.full_name}</div>
                          <div className="text-xs text-indigo-400 font-bold bg-indigo-50 px-2 py-0.5 rounded-lg inline-block mt-1">{subject.username}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-sm font-bold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg">{subject.gender === '남성' ? 'Male' : 'Female'} / {subject.age}세</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="text-sm font-bold text-slate-600 flex items-center gap-4">
                        <div className="flex flex-col">
                          <span className="text-[10px] text-slate-400 uppercase">Height</span>
                          <span>{subject.height}cm</span>
                        </div>
                        <div className="w-px h-8 bg-slate-200"></div>
                        <div className="flex flex-col">
                          <span className="text-[10px] text-slate-400 uppercase">Weight</span>
                          <span>{subject.weight}kg</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-sm font-bold text-slate-600 font-mono tracking-tight">{subject.date_of_birth}</span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button className="p-2.5 hover:bg-indigo-100 rounded-xl text-slate-400 hover:text-indigo-600 transition-all active:scale-95">
                        <Edit2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const EmergencyAlertsView = () => {
  // Augment workers with risk reasons and alert state
  const [alertWorkers, setAlertWorkers] = useState(() => {
    // Sort logic: Danger > Warn > Safe
    const sorted = [...workers].sort((a, b) => {
      const score = { 'danger': 3, 'warn': 2, 'safe': 1 };
      return score[b.status] - score[a.status];
    });

    return sorted.map(w => ({
      ...w,
      riskReason: w.status === 'danger'
        ? (w.hr > 150 ? '심박수 위험 수준 지속 (2시간+)' : '작업 부하 한계 초과')
        : w.status === 'warning'
          ? '휴식 없는 연속 작업 감지'
          : '특이사항 없음',
      lastAlert: null,
      readStatus: null, // 'unread', 'read'
    }));
  });

  const [appNotification, setAppNotification] = useState(null);

  useEffect(() => {
    if (appNotification) {
      const timer = setTimeout(() => setAppNotification(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [appNotification]);

  const sendAlert = (workerId, messageType) => {
    const now = new Date();
    setAlertWorkers(prev => prev.map(w => {
      if (w.id === workerId) {
        return {
          ...w,
          lastAlert: { type: messageType, time: now },
          readStatus: 'unread'
        };
      }
      return w;
    }));
    setAppNotification(`${messageType} 메시지가 전송되었습니다.`);

    // Simulate Read Receipt after 3-5 seconds
    setTimeout(() => {
      setAlertWorkers(prev => prev.map(w => {
        if (w.id === workerId && w.readStatus === 'unread') {
          return { ...w, readStatus: 'read' };
        }
        return w;
      }));
    }, 4000);
  };

  const macros = [
    { id: 'rest', label: '🛑 휴식 권고', desc: '즉시 작업을 중단하고 휴식을 취하세요.' },
    { id: 'sleep', label: '💤 수면 권고', desc: '수면 부족이 감지되었습니다.' },
    { id: 'home', label: '🏠 조기 퇴근', desc: '금일 건강 상태로 인해 조기 퇴근을 권고합니다.' },
    { id: 'check', label: '🩺 건강 검진', desc: '가까운 센터에서 건강 검진을 받으세요.' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      {/* Header Section */}
      <div className="flex justify-between items-center bg-white/60 p-8 rounded-[2rem] border border-white/60 backdrop-blur-xl shadow-sm hover:shadow-md transition-all">
        <div>
          <h2 className="text-3xl font-black text-slate-800 tracking-tight mb-2 flex items-center gap-2">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-red-600 to-orange-600">비상 상황 전파</span>
          </h2>
          <p className="text-slate-500 font-bold">고위험 근로자에게 즉시 알림을 전송하고 수신 여부를 확인합니다.</p>
        </div>
        <div className="flex gap-3">
          <div className="bg-red-50 text-red-600 px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2">
            <AlertTriangle size={18} />
            위험: {alertWorkers.filter(w => w.status === 'danger').length}명
          </div>
          <div className="bg-amber-50 text-amber-600 px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2">
            <AlertCircle size={18} />
            주의: {alertWorkers.filter(w => w.status === 'warn').length}명
          </div>
        </div>
      </div>

      {/* Worker List Grid */}
      <div className="grid grid-cols-1 gap-4">
        {alertWorkers.map((worker) => (
          <div key={worker.id} className={`group relative overflow-hidden rounded-3xl p-6 transition-all border-2 ${worker.status === 'danger' ? 'bg-white border-red-100 shadow-xl shadow-red-100/50' : worker.status === 'warn' ? 'bg-white border-amber-50' : 'bg-slate-50 border-transparent opacity-80'}`}>
            <div className="flex items-center justify-between">
              {/* Left: Info */}
              <div className="flex items-center gap-6">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-black shadow-inner ${worker.status === 'danger' ? 'bg-red-100 text-red-600' : worker.status === 'warn' ? 'bg-amber-100 text-amber-600' : 'bg-slate-200 text-slate-400'}`}>
                  {worker.name[0]}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl font-black text-slate-800">{worker.name}</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${worker.status === 'danger' ? 'bg-red-600 text-white' : worker.status === 'warn' ? 'bg-amber-500 text-white' : 'bg-slate-200 text-slate-500'}`}>
                      {worker.status === 'danger' ? 'Danger' : worker.status === 'warn' ? 'Warning' : 'Normal'}
                    </span>
                  </div>
                  <p className={`text-sm font-bold ${worker.status === 'danger' ? 'text-red-500' : 'text-slate-400'}`}>
                    {worker.riskReason}
                  </p>
                </div>
              </div>

              {/* Middle: Last Action */}
              <div className="hidden md:block w-[300px]">
                {worker.lastAlert ? (
                  <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                    <div className="flex justify-between items-center text-xs font-bold mb-1">
                      <span className="text-slate-400">최근 전송 메시지</span>
                      <span className="text-slate-300">{worker.lastAlert.time.toLocaleTimeString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-indigo-600">{worker.lastAlert.type}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1 ${worker.readStatus === 'read' ? 'bg-green-100 text-green-600' : 'bg-slate-200 text-slate-500'}`}>
                        {worker.readStatus === 'read' ? <CheckCircle2 size={10} /> : <Clock size={10} />}
                        {worker.readStatus === 'read' ? '읽음' : '전송됨'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-slate-300 text-sm font-bold">전송 이력 없음</div>
                )}
              </div>

              {/* Right: Actions */}
              <div className="flex gap-2">
                {macros.slice(0, 2).map(macro => (
                  <button
                    key={macro.id}
                    onClick={() => sendAlert(worker.id, macro.label)}
                    className="px-4 py-3 bg-white border-2 border-slate-100 hover:border-indigo-100 hover:bg-indigo-50 text-slate-600 hover:text-indigo-600 rounded-xl text-sm font-bold transition-all whitespace-nowrap active:scale-95"
                  >
                    {macro.label}
                  </button>
                ))}
                <button className="px-4 py-3 bg-red-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-red-500/30 hover:bg-red-500 transition-all flex items-center gap-2 active:scale-95">
                  <Send size={16} />
                  <span>직접 입력</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Global Notification Toast */}
      {appNotification && (
        <div className="fixed bottom-10 right-10 bg-slate-900 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-4 animate-in slide-in-from-right-10 fade-in duration-300 z-50">
          <div className="bg-green-500 rounded-full p-1"><Check size={14} /></div>
          <span className="font-bold">{appNotification}</span>
        </div>
      )}
    </div>
  );
};

const App = () => {
  console.log('App component rendering...');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Added for premium design

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  useEffect(() => {
    const handleFsChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-50 via-gray-50 to-slate-100 text-slate-800 font-sans">
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-slate-900/95 backdrop-blur-xl text-white transition-all duration-300 z-50 flex flex-col items-center py-8 border-r border-slate-800/50 shadow-2xl ${isSidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="mb-12 flex items-center justify-center w-full px-4">
          {isSidebarOpen ? (
            <div className="flex items-center gap-2 animate-in fade-in duration-300">
              <div className="w-8 h-8 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/30">
                <Activity size={20} className="text-white" />
              </div>
              <span className="text-xl font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">Safety Tower</span>
            </div>
          ) : (
            <div className="w-10 h-10 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Activity size={24} className="text-white" />
            </div>
          )}
        </div>
        <nav className="flex-1 px-3 py-6 space-y-3 w-full">
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: '관제 홈' },
            { id: 'workers', icon: UserCheck, label: '근로자 현황' },
            { id: 'livemap', icon: Map, label: '실시간 관제 지도' },
            { id: 'subjects', icon: Users, label: '대상자 관리' },
            { id: 'analysis', icon: Brain, label: 'AI 피로분석' },
            { id: 'alerts', icon: Bell, label: '비상 알림' },
          ].map((item) => (
            <button key={item.id} onClick={() => setActiveTab(item.id)} className={`w-full flex items-center gap-3 px-5 py-3.5 rounded-2xl transition-all duration-300 ${activeTab === item.id ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/20' : 'text-slate-400 hover:bg-slate-800/80 hover:text-white'}`}>
              <item.icon size={20} /><span className="font-bold text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="p-6 border-t border-slate-200 text-slate-800">
          <div className="bg-gradient-to-br from-indigo-50 to-transparent p-5 rounded-[2rem] border border-indigo-100 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-indigo-100 flex items-center justify-center font-bold text-xs text-indigo-600 uppercase tracking-tighter shadow-sm">AD</div>
            <div><p className="text-xs font-bold leading-none mb-1 text-slate-800">김철수 팀장</p><p className="text-[10px] text-slate-400 font-mono tracking-tighter uppercase">안전관리팀 (Safety Manager)</p></div>
          </div>
        </div>
      </aside>

      <main className="lg:ml-64 p-6 lg:p-10 transition-all duration-500">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
          <div className="flex flex-col gap-1">
            <h1 className="text-5xl font-black flex items-center gap-3 drop-shadow-sm">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 font-[KyoboHandwriting2019] tracking-tighter">
                스마트 안전 관제 타워
              </span>
              <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.8)] animate-pulse"></div>
            </h1>
            <p className="text-lg text-slate-500 font-bold tracking-widest pl-1 uppercase">{activeTab === 'dashboard' ? '플랫폼 노동자 통합 관제 대시보드' : 'Real-time Bio-Signal Analysis System'}</p>
          </div>

          <div className="flex items-center gap-6 bg-white/80 backdrop-blur-xl px-6 py-4 rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50">
            <div className="flex items-center gap-4 border-r border-slate-200 pr-6">
              <div className="p-2.5 bg-indigo-50 rounded-xl text-indigo-600">
                <Calendar size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">DATE</p>
                <p className="text-sm font-black text-slate-700 tracking-tight">
                  {currentTime.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' })}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-pink-50 rounded-xl text-pink-500">
                <Clock size={20} />
              </div>
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">TIME</p>
                <p className="text-sm font-black text-slate-800 tracking-tight font-mono">
                  {currentTime.toLocaleTimeString('ko-KR', { hour12: false })}
                </p>
              </div>
            </div>
            <button onClick={toggleFullscreen} className="p-3 bg-white hover:bg-indigo-50 rounded-xl transition-all text-slate-600 shadow-sm border border-slate-200">
              {isFullscreen ? <Minimize2 size={22} /> : <Maximize2 size={22} />}
            </button>
          </div>
        </header>

        {/* Tab Logic */}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'workers' && <WorkersListView searchQuery={searchQuery} setSearchQuery={setSearchQuery} />}
        {activeTab === 'livemap' && <LiveMapView />}
        {activeTab === 'analysis' && <FatigueAnalysisView searchQuery={searchQuery} />}
        {activeTab === 'alerts' && <EmergencyAlertsView />}


      </main>

      {/* Ambient Backgrounds */}
      <div className="fixed top-[-10%] right-[-10%] w-[800px] h-[800px] bg-indigo-600/5 blur-[150px] rounded-full -z-10 pointer-events-none"></div>
      <div className="fixed bottom-[-5%] left-[-5%] w-[600px] h-[600px] bg-pink-600/5 blur-[120px] rounded-full -z-10 pointer-events-none"></div>
    </div>
  );
};


export default App;
