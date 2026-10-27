import React from 'react';
import { SerieEpidemiologica, PrevisaoIA } from '../types';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  Area,
} from 'recharts';
import { TrendingUp, Cpu, Calendar } from 'lucide-react';

interface EpidemicChartProps {
  series: SerieEpidemiologica[];
  previsoes: PrevisaoIA[];
  municipioNome: string;
  doenca: string;
}

export const EpidemicChart: React.FC<EpidemicChartProps> = ({
  series,
  previsoes,
  municipioNome,
  doenca,
}) => {
  // Combinar dados da série com projeções da IA
  const chartData = series.map((s) => ({
    label: `SE ${s.semana_epidemiologica}/${s.ano}`,
    casos_notificados: s.casos_notificados,
    casos_estimados: s.casos_estimados,
    temperatura_media: s.temperatura_media,
    previsao: null as number | null,
    limite_inferior: null as number | null,
    limite_superior: null as number | null,
  }));

  // Adicionar projeções futuras da IA
  previsoes.forEach((p) => {
    chartData.push({
      label: `SE ${p.semana_alvo}/${p.ano_alvo} (Prev)`,
      casos_notificados: null as any,
      casos_estimados: null as any,
      temperatura_media: null as any,
      previsao: Math.round(p.casos_previstos),
      limite_inferior: p.intervalo_inferior !== null ? Math.round(p.intervalo_inferior) : null,
      limite_superior: p.intervalo_superior !== null ? Math.round(p.intervalo_superior) : null,
    });
  });

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-xl backdrop-blur-sm space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            Série Histórica e Projeção Preditiva (IA)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Município: <span className="text-emerald-400 font-semibold">{municipioNome}</span> | Arbovirose: <span className="capitalize font-semibold text-white">{doenca}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Histórico Observado
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block" /> Previsão IA
          </span>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="h-72 flex items-center justify-center text-slate-500 border border-dashed border-slate-700 rounded-lg">
          Sem registros de séries para os parâmetros selecionados.
        </div>
      ) : (
        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis
                dataKey="label"
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                angle={-35}
                textAnchor="end"
                interval="preserveStartEnd"
              />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '15px' }} />

              {/* Casos Notificados */}
              <Bar
                name="Casos Notificados"
                dataKey="casos_notificados"
                fill="#22c55e"
                radius={[4, 4, 0, 0]}
              />

              {/* Casos Estimados */}
              <Line
                name="Casos Estimados (Nowcasting)"
                type="monotone"
                dataKey="casos_estimados"
                stroke="#eab308"
                strokeWidth={2}
                dot={false}
              />

              {/* Previsão IA */}
              <Line
                name="Previsão Modelo IA"
                type="monotone"
                dataKey="previsao"
                stroke="#06b6d4"
                strokeWidth={3}
                strokeDasharray="4 4"
                dot={{ r: 4, fill: '#06b6d4' }}
              />

              {/* Faixa de Confiança Superior/Inferior */}
              <Area
                name="Intervalo de Confiança"
                type="monotone"
                dataKey="limite_superior"
                stroke="transparent"
                fill="#06b6d4"
                fillOpacity={0.15}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Cards de Métricas do Município */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50">
          <p className="text-[11px] text-slate-400 uppercase font-semibold">Total Notificado no Período</p>
          <p className="text-xl font-bold text-white mt-0.5">
            {series.reduce((acc, curr) => acc + (curr.casos_notificados || 0), 0)} casos
          </p>
        </div>
        <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50">
          <p className="text-[11px] text-slate-400 uppercase font-semibold">Previsão Próximas Semanas</p>
          <p className="text-xl font-bold text-cyan-400 mt-0.5">
            {previsoes.length > 0
              ? `${Math.round(previsoes[0].casos_previstos)} casos (SE ${previsoes[0].semana_alvo})`
              : 'Sem projeções'}
          </p>
        </div>
        <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-700/50">
          <p className="text-[11px] text-slate-400 uppercase font-semibold">Nível de Risco Predito</p>
          <p className="text-xl font-bold text-emerald-400 mt-0.5">
            {previsoes.length > 0 ? `Nível ${previsoes[0].nivel_risco_previsto} (Baixo)` : 'Regular'}
          </p>
        </div>
      </div>
    </div>
  );
};
