import React from 'react';
import { Activity, ShieldAlert, Cpu, MapPin } from 'lucide-react';
import { DashboardResumo } from '../types';

interface MetricCardsProps {
  resumo: DashboardResumo | null;
  loading: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ resumo, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-slate-800/60 rounded-xl border border-slate-700/50" />
        ))}
      </div>
    );
  }

  const gravidades = resumo?.alertas_por_gravidade || {};
  const nivelCritico = (gravidades['3'] || 0) + (gravidades['4'] || 0);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Municípios */}
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase font-medium text-slate-400 tracking-wider">Municípios Monitorados</p>
            <p className="text-3xl font-bold text-white mt-1">{resumo?.total_municipios ?? 223}</p>
          </div>
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
            <MapPin className="w-6 h-6" />
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
          <span className="text-emerald-400 font-semibold">100%</span> da malha da Paraíba integrada
        </p>
      </div>

      {/* Alertas Ativos */}
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase font-medium text-slate-400 tracking-wider">Alertas Vigentes</p>
            <p className="text-3xl font-bold text-amber-400 mt-1">{resumo?.total_alertas_ativos ?? 0}</p>
          </div>
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3">
          <span className="text-amber-400 font-semibold">{nivelCritico}</span> em nível moderado a crítico
        </p>
      </div>

      {/* Previsões de IA */}
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase font-medium text-slate-400 tracking-wider">Modelos de IA Ativos</p>
            <p className="text-3xl font-bold text-cyan-400 mt-1">{resumo?.total_previsoes_ia ?? 0}</p>
          </div>
          <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl">
            <Cpu className="w-6 h-6" />
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3">Random Forest & XGBoost treinados</p>
      </div>

      {/* Risco Epidemiológico */}
      <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-5 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase font-medium text-slate-400 tracking-wider">Status Geral PB</p>
            <p className="text-xl font-bold text-emerald-400 mt-2">Vigilância Regular</p>
          </div>
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
            <Activity className="w-6 h-6" />
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3">Atualização contínua com InfoDengue</p>
      </div>
    </div>
  );
};
