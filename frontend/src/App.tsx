import React, { useState, useEffect } from 'react';
import { Shield, Bell, Zap, Activity, AlertTriangle, CheckCircle, Smartphone } from 'lucide-react';
import './index.css';

const Dashboard = () => {
  const [areas, setAreas] = useState([
    { id: 'area_1', name: 'Büro', state: 'armed', devices: 12, incidents: 0 },
    { id: 'area_2', name: 'Lager', state: 'disarmed', devices: 45, incidents: 2 },
  ]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            Bosch MAP5000
          </h1>
          <p className="text-slate-400 text-sm mt-1">System Online • Letzte Aktualisierung: gerade eben</p>
        </div>
        <div className="flex gap-4">
          <div className="px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
            System OK
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Areas Overview */}
        <section className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            Bereiche
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {areas.map(area => (
              <div key={area.id} className="relative overflow-hidden group bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6 transition-all hover:bg-slate-800 hover:border-slate-600">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-transparent opacity-50"></div>
                
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-medium">{area.name}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider
                    ${area.state === 'armed' ? 'bg-red-500/20 text-red-400 border border-red-500/20' : 
                      'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20'}`}>
                    {area.state}
                  </span>
                </div>
                
                <div className="flex gap-4 text-sm text-slate-400">
                  <span className="flex items-center gap-1">
                    <Activity className="w-4 h-4" /> {area.devices} Geräte
                  </span>
                  <span className="flex items-center gap-1 text-amber-400/80">
                    <AlertTriangle className="w-4 h-4" /> {area.incidents} Störungen
                  </span>
                </div>

                <div className="mt-6 flex gap-3">
                  <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                    Scharfschalten
                  </button>
                  <button className="flex-1 bg-slate-700/50 hover:bg-slate-700 text-white py-2 rounded-lg text-sm font-medium transition-colors">
                    Walktest
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Sidebar Status */}
        <aside className="space-y-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            System Status
          </h2>
          
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 rounded-lg bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <span>Spannungsversorgung</span>
                </div>
                <span className="text-slate-400 text-sm">OK</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-slate-400" />
                  <span>Sirenen</span>
                </div>
                <span className="text-slate-400 text-sm">Bereit</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <Smartphone className="w-5 h-5 text-blue-400" />
                  <span>REST API Verbindung</span>
                </div>
                <span className="text-emerald-400 text-sm">Verbunden</span>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
};

export default Dashboard;
