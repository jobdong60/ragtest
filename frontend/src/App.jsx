import React, { useState, useEffect, useRef } from 'react';
import {
  Users,
  Activity,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
  Bell,
  Search,
  LayoutDashboard,
  UserCheck,
  Heart,
  Filter,
  ArrowUpRight,
  MoreVertical,
  Droplets,
  Maximize2,
  Minimize2,
  Brain,
  Calendar,
  Coffee,
  TrendingDown,
  TrendingUp
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  LineChart,
  Line
} from 'recharts';

// HRV 추이 데이터 (ms 단위)
const hrvTrendData = [
  { time: '20:00', avgHRV: 65, minHRV: 45 },
  { time: '22:00', avgHRV: 58, minHRV: 42 },
  { time: '00:00', avgHRV: 52, minHRV: 35 },
  { time: '02:00', avgHRV: 45, minHRV: 28 },
  { time: '04:00', avgHRV: 38, minHRV: 22 },
  { time: '06:00', avgHRV: 42, minHRV: 30 },
];

const riskData = [
  { name: '최상', value: 140, color: '#10b981' },
  { name: '주의', value: 65, color: '#f59e0b' },
  { name: '위험', value: 25, color: '#ef4444' },
];

// 피로 분석용 데이터 확장
const workers = [
  {
    id: 'K-042', name: '이민호', status: '위험', hrv: 24, hr: 98, hrvScore: 'Low', spo2: 94, activity: 'High',
    avg3DayWork: 9.5, avgTimeSlot: '22:00 - 07:00', totalFatigue: 88,
    scoreHistory: [
      { date: '12-18', score: 45 }, { date: '12-19', score: 52 }, { date: '12-20', score: 68 }, { date: '12-21', score: 75 }, { date: '12-22', score: 88 }
    ],
    history: [35, 32, 28, 24, 25, 24]
  },
  {
    id: 'M-011', name: '정해인', status: '위험', hrv: 18, hr: 105, hrvScore: 'Critical', spo2: 92, activity: 'High',
    avg3DayWork: 10.2, avgTimeSlot: '23:00 - 08:00', totalFatigue: 94,
    scoreHistory: [
      { date: '12-18', score: 60 }, { date: '12-19', score: 65 }, { date: '12-20', score: 82 }, { date: '12-21', score: 90 }, { date: '12-22', score: 94 }
    ],
    history: [30, 28, 22, 18, 19, 18]
  },
  {
    id: 'B-129', name: '박지수', status: '주의', hrv: 38, hr: 82, hrvScore: 'Med', spo2: 97, activity: 'Low',
    avg3DayWork: 8.0, avgTimeSlot: '21:00 - 06:00', totalFatigue: 62,
    scoreHistory: [
      { date: '12-18', score: 30 }, { date: '12-19', score: 35 }, { date: '12-20', score: 45 }, { date: '12-21', score: 55 }, { date: '12-22', score: 62 }
    ],
    history: [50, 48, 42, 38, 39, 38]
  },
  {
    id: 'A-008', name: '최현욱', status: '정상', hrv: 62, hr: 72, hrvScore: 'High', spo2: 99, activity: 'Med',
    avg3DayWork: 7.5, avgTimeSlot: '20:00 - 05:00', totalFatigue: 32,
    scoreHistory: [
      { date: '12-18', score: 25 }, { date: '12-19', score: 28 }, { date: '12-20', score: 30 }, { date: '12-21', score: 32 }, { date: '12-22', score: 32 }
    ],
    history: [60, 62, 61, 63, 62, 62]
  },
];

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [searchQuery, setSearchQuery] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);

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

  const DashboardView = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 animate-in fade-in duration-500">
        <div className="bg-[#1e293b] p-6 rounded-3xl border border-slate-800 hover:border-indigo-500/30 transition-all group relative overflow-hidden shadow-lg shadow-indigo-500/5">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Users size={120} /></div>
          <div className="flex justify-between items-start mb-4 text-blue-400">
            <div className="p-3 bg-blue-500/10 rounded-2xl border border-blue-500/20"><Users size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-blue-500/10 rounded-md">LIVE 212/230</span>
          </div>
          <h3 className="text-slate-400 text-sm mb-1 font-medium">현장 인력 가동률</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tighter">92.1%</span>
            <span className="text-slate-500 text-xs">운영 중</span>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-3xl border border-slate-800 hover:border-pink-500/30 transition-all group relative overflow-hidden shadow-lg">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Activity size={120} /></div>
          <div className="flex justify-between items-start mb-4 text-pink-400">
            <div className="p-3 bg-pink-500/10 rounded-2xl border border-pink-500/20"><Activity size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-pink-500/10 rounded-md">AVG HRV</span>
          </div>
          <h3 className="text-slate-400 text-sm mb-1 font-medium">평균 심박변이도</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tighter">54.2</span>
            <span className="text-slate-500 text-sm">ms</span>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-3xl border border-slate-800 hover:border-amber-500/30 transition-all group relative overflow-hidden shadow-lg">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Brain size={120} /></div>
          <div className="flex justify-between items-start mb-4 text-amber-400">
            <div className="p-3 bg-amber-500/10 rounded-2xl border border-amber-500/20"><Brain size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-amber-500/10 rounded-md">FATIGUE</span>
          </div>
          <h3 className="text-slate-400 text-sm mb-1 font-medium">누적 피로 지수</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tighter">72/100</span>
            <span className="text-amber-500/70 text-xs ml-1">상승 중</span>
          </div>
        </div>

        <div className="bg-[#1e293b] p-6 rounded-3xl border border-slate-800 hover:border-emerald-500/30 transition-all group relative overflow-hidden shadow-lg">
          <div className="absolute -right-4 -bottom-4 opacity-5 group-hover:opacity-10 transition-opacity"><Zap size={120} /></div>
          <div className="flex justify-between items-start mb-4 text-emerald-400">
            <div className="p-3 bg-emerald-500/10 rounded-2xl border border-emerald-500/20"><Zap size={24} /></div>
            <span className="text-xs font-bold px-2 py-1 bg-emerald-500/10 rounded-md">SAFE</span>
          </div>
          <h3 className="text-slate-400 text-sm mb-1 font-medium">무사고 가동</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tighter">1,248</span>
            <span className="text-slate-500 text-sm">Hrs</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div className="lg:col-span-2 bg-[#1e293b] p-8 rounded-[2rem] border border-slate-800 shadow-xl">
          <h3 className="text-xl font-bold text-white mb-8 italic uppercase tracking-tight flex items-center gap-2">
            <TrendingDown className="text-indigo-400" /> HRV Global Trend
          </h3>
          <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hrvTrendData}>
                <defs>
                  <linearGradient id="colorHrv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.3} /><stop offset="95%" stopColor="#818cf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderRadius: '16px', border: '1px solid #334155' }} itemStyle={{ color: '#fff' }} />
                <Area type="monotone" dataKey="avgHRV" stroke="#818cf8" strokeWidth={4} fillOpacity={1} fill="url(#colorHrv)" name="평균 HRV" />
                <Area type="monotone" dataKey="minHRV" stroke="#f43f5e" strokeWidth={2} strokeDasharray="5 5" fill="none" name="최저 HRV" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#1e293b] p-8 rounded-[2rem] border border-slate-800 shadow-xl flex flex-col">
          <h3 className="text-xl font-bold text-white mb-6 uppercase tracking-tight">Condition Mix</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} layout="vertical" barSize={32}>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: '#cbd5e1', fontWeight: 'bold' }} />
                <Bar dataKey="value" radius={[0, 12, 12, 0]}>
                  {riskData.map((entry, index) => <Cell key={index} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-8 p-5 bg-gradient-to-r from-red-500/20 to-transparent border border-red-500/20 rounded-2xl">
            <div className="flex justify-between items-center">
              <span className="text-xs font-black text-red-500 uppercase tracking-widest">Active Alerts</span>
              <span className="text-lg font-black text-white">25 Cases</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );

  const WorkersListView = () => (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-800/30 p-4 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input
            type="text"
            placeholder="근로자 검색..."
            className="w-full bg-[#0f172a] border border-slate-700 rounded-xl py-3 pl-12 pr-4 text-sm focus:outline-none focus:border-indigo-500 transition-all text-white"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <button className="flex items-center gap-2 px-5 py-3 bg-slate-800 rounded-xl text-slate-300 border border-slate-700 hover:bg-slate-700 transition-all font-bold text-sm">
          <Filter size={18} /> 리스트 필터링
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 pb-20">
        {workers.filter(w => w.name.includes(searchQuery)).map((worker) => (
          <div key={worker.id} className="bg-[#1e293b] rounded-[2.5rem] border border-slate-800 p-7 hover:border-indigo-500/40 transition-all group relative overflow-hidden">
            <div className="flex items-start justify-between mb-8">
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center border border-slate-700 group-hover:scale-105 transition-transform"><UserCheck className="text-slate-400" size={32} /></div>
                <div>
                  <h4 className="text-xl font-bold text-white">{worker.name} <span className="text-xs text-slate-500 font-mono ml-2">{worker.id}</span></h4>
                  <p className="text-sm text-slate-500">Zone B-04 Control Area</p>
                </div>
              </div>
              <div className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase border ${worker.status === '위험' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>{worker.status}</div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-[#0f172a]/40 p-4 rounded-2xl border border-slate-800/50">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-1">HRV</span>
                <span className="text-2xl font-black text-white">{worker.hrv}ms</span>
              </div>
              <div className="bg-[#0f172a]/40 p-4 rounded-2xl border border-slate-800/50">
                <span className="text-[10px] font-bold text-pink-400 uppercase tracking-widest block mb-1">HR</span>
                <span className="text-2xl font-black text-white">{worker.hr}</span>
              </div>
              <div className="bg-[#0f172a]/40 p-4 rounded-2xl border border-slate-800/50">
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest block mb-1">SpO2</span>
                <span className="text-2xl font-black text-white">{worker.spo2}%</span>
              </div>
            </div>

            <div className="h-28 w-full bg-slate-900/60 rounded-2xl p-4 border border-slate-800 overflow-hidden">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={worker.history.map((h, i) => ({ val: h, time: i }))}>
                  <defs>
                    <linearGradient id={`grad-${worker.id}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} /><stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="val" stroke="#6366f1" strokeWidth={3} fill={`url(#grad-${worker.id})`} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const FatigueAnalysisView = () => (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      {/* Analysis Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {workers.filter(w => w.name.includes(searchQuery)).map((worker) => (
          <div key={worker.id} className="bg-[#1e293b] rounded-[2.5rem] border border-slate-800 p-8 hover:border-amber-500/40 transition-all group">
            <div className="flex justify-between items-start mb-10">
              <div className="flex items-center gap-6">
                <div className="relative">
                  <div className="w-20 h-20 bg-slate-800 rounded-[2rem] flex items-center justify-center border-2 border-slate-700">
                    <Brain className={worker.totalFatigue > 80 ? 'text-red-500' : 'text-amber-500'} size={40} />
                  </div>
                  <div className={`absolute -bottom-2 -right-2 w-10 h-10 rounded-full flex items-center justify-center font-black text-sm border-4 border-[#1e293b] ${worker.totalFatigue > 80 ? 'bg-red-500 text-white' : 'bg-amber-500 text-white'}`}>
                    {worker.totalFatigue}
                  </div>
                </div>
                <div>
                  <h3 className="text-2xl font-black text-white uppercase tracking-tight">{worker.name} 피로 정밀 분석</h3>
                  <div className="flex items-center gap-3 mt-1 text-slate-500 font-mono text-sm">
                    <span className="flex items-center gap-1"><ShieldCheck size={14} /> AI Verified</span>
                    <span>|</span>
                    <span>Last Synced: Just Now</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Fatigue Status</p>
                <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-tighter ${worker.totalFatigue > 80 ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'}`}>
                  {worker.totalFatigue > 80 ? 'CRITICAL RISK' : 'HIGH CAUTION'}
                </span>
              </div>
            </div>

            {/* Variable Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
              <div className="bg-[#0f172a]/50 p-5 rounded-3xl border border-slate-800">
                <Heart className="text-pink-500 mb-2" size={20} />
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Heart Rate</p>
                <p className="text-xl font-black text-white">{worker.hr} <span className="text-xs font-normal opacity-50">BPM</span></p>
              </div>
              <div className="bg-[#0f172a]/50 p-5 rounded-3xl border border-slate-800">
                <Activity className="text-indigo-400 mb-2" size={20} />
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">HRV (Avg)</p>
                <p className="text-xl font-black text-white">{worker.hrv} <span className="text-xs font-normal opacity-50">ms</span></p>
              </div>
              <div className="bg-[#0f172a]/50 p-5 rounded-3xl border border-slate-800">
                <Clock className="text-emerald-400 mb-2" size={20} />
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">3D Avg Work</p>
                <p className="text-xl font-black text-white">{worker.avg3DayWork} <span className="text-xs font-normal opacity-50">Hrs</span></p>
              </div>
              <div className="bg-[#0f172a]/50 p-5 rounded-3xl border border-slate-800">
                <Calendar className="text-amber-400 mb-2" size={20} />
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Work Slot</p>
                <p className="text-sm font-black text-white leading-tight">{worker.avgTimeSlot}</p>
              </div>
            </div>

            {/* Score History Chart */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                  <TrendingUp size={16} className="text-red-500" /> Fatigue Score History
                </h4>
                <div className="flex gap-4">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">Daily Score</span>
                  </div>
                </div>
              </div>
              <div className="h-48 w-full bg-[#0f172a]/30 rounded-[2rem] border border-slate-800 p-6 overflow-hidden shadow-inner">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={worker.scoreHistory}>
                    <defs>
                      <linearGradient id={`score-grad-${worker.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} /><stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                    <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10, fontWeight: 'bold' }} dy={10} />
                    <YAxis hide domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', borderRadius: '12px', border: '1px solid #475569', fontSize: '12px' }}
                      cursor={{ stroke: '#f43f5e', strokeWidth: 1 }}
                    />
                    <Area
                      type="monotone"
                      dataKey="score"
                      stroke="#f43f5e"
                      strokeWidth={4}
                      fill={`url(#score-grad-${worker.id})`}
                      animationDuration={1500}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* AI Action */}
            <div className="mt-8 flex items-center justify-between p-5 bg-slate-800/40 rounded-[1.5rem] border border-slate-700/50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/10 rounded-lg text-amber-500">
                  <Coffee size={20} />
                </div>
                <div>
                  <p className="text-xs font-bold text-white">AI 권고 조치</p>
                  <p className="text-[10px] text-slate-500">수면 부채 및 심박 이상 감지: 15분 이상의 즉각 휴식 필요</p>
                </div>
              </div>
              <button className="px-5 py-2.5 bg-indigo-600 text-white text-[10px] font-black rounded-xl hover:bg-indigo-500 transition-all uppercase tracking-tight shadow-lg shadow-indigo-600/20">
                Send Alert
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-x-hidden">
      <aside className="fixed left-0 top-0 h-full w-64 bg-[#1e293b] border-r border-slate-800 hidden lg:flex flex-col z-50">
        <div className="p-8 flex items-center gap-3">
          <div className="w-11 h-11 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-indigo-600/40 transform rotate-3"><ShieldCheck className="text-white" size={26} /></div>
          <div><span className="text-xl font-black tracking-tighter text-white block leading-none uppercase">NightWatch</span><span className="text-[10px] text-indigo-400 font-bold tracking-[0.2em]">OS PRO</span></div>
        </div>

        <nav className="flex-1 px-5 py-6 space-y-3">
          {[
            { id: 'dashboard', icon: LayoutDashboard, label: '관제 홈' },
            { id: 'workers', icon: UserCheck, label: '근로자 현황' },
            { id: 'analysis', icon: Brain, label: 'AI 피로분석' },
            { id: 'alerts', icon: Bell, label: '비상 알림' },
          ].map((item) => (
            <button key={item.id} onClick={() => setActiveTab(item.id)} className={`w-full flex items-center gap-3 px-5 py-3.5 rounded-2xl transition-all duration-300 ${activeTab === item.id ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/20' : 'text-slate-400 hover:bg-slate-800/80 hover:text-white'}`}>
              <item.icon size={20} /><span className="font-bold text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="p-6 border-t border-slate-800 text-white">
          <div className="bg-gradient-to-br from-indigo-600/20 to-transparent p-5 rounded-[2rem] border border-indigo-500/20 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-800 border-2 border-indigo-500/50 flex items-center justify-center font-bold text-xs text-white uppercase tracking-tighter">AD</div>
            <div><p className="text-xs font-bold leading-none mb-1 text-white uppercase">Admin Kim</p><p className="text-[10px] text-slate-500 font-mono tracking-tighter uppercase">SEC-CLEARANCE LV.4</p></div>
          </div>
        </div>
      </aside>

      <main className="lg:ml-64 p-6 lg:p-10 transition-all duration-500">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
          <h1 className="text-4xl font-black text-white italic tracking-tight flex items-center gap-3 uppercase">
            {activeTab === 'dashboard' ? 'Overview' : activeTab === 'workers' ? 'Bio-Metrics' : 'Fatigue Intel'}
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.8)] animate-pulse"></div>
          </h1>

          <div className="flex items-center gap-4 bg-slate-800/60 backdrop-blur-xl p-3 rounded-2xl border border-slate-700/50 shadow-2xl">
            <div className="px-5 border-r border-slate-700 text-right">
              <p className="text-[10px] uppercase tracking-widest text-slate-500 font-black mb-0.5">System Time</p>
              <p className="text-xl font-mono font-bold text-white tracking-wider uppercase">{currentTime.toLocaleTimeString('ko-KR', { hour12: false })}</p>
            </div>
            <button onClick={toggleFullscreen} className="p-3 bg-slate-700/50 hover:bg-indigo-600 rounded-xl transition-all text-white shadow-lg">
              {isFullscreen ? <Minimize2 size={22} /> : <Maximize2 size={22} />}
            </button>
          </div>
        </header>

        {/* Tab Logic */}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'workers' && <WorkersListView />}
        {activeTab === 'analysis' && <FatigueAnalysisView />}

        {/* 하단 비상 관제 바 - '관제 홈' 탭에서만 보이도록 유지 */}
        {activeTab === 'dashboard' && (
          <div className="fixed bottom-8 left-1/2 -translate-x-1/2 lg:left-[calc(50%+128px)] w-[90%] lg:w-[60%] bg-[#ef4444]/10 backdrop-blur-2xl border border-red-500/30 p-5 rounded-[2rem] shadow-[0_20px_50px_rgba(239,68,68,0.2)] flex items-center justify-between z-40 animate-bounce-slow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-500 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-red-500/40"><AlertTriangle size={24} /></div>
              <div>
                <h5 className="text-white font-black text-sm uppercase leading-none mb-1">Critical Dispatch</h5>
                <p className="text-[10px] text-red-400 font-bold uppercase tracking-tight">Zone M: HRV Spike Detected on ID: M-011</p>
              </div>
            </div>
            <button className="px-6 py-3 bg-red-500 text-white text-xs font-black rounded-xl hover:bg-red-400 transition-all shadow-lg uppercase tracking-tight">Confirm</button>
          </div>
        )}
      </main>

      {/* Ambient Backgrounds */}
      <div className="fixed top-[-10%] right-[-10%] w-[800px] h-[800px] bg-indigo-600/5 blur-[150px] rounded-full -z-10 pointer-events-none"></div>
      <div className="fixed bottom-[-5%] left-[-5%] w-[600px] h-[600px] bg-pink-600/5 blur-[120px] rounded-full -z-10 pointer-events-none"></div>
    </div>
  );
};

export default App;
