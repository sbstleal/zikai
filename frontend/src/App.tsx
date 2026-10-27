import React, { useEffect, useState } from 'react';
import {
  fetchMunicipios,
  fetchDashboardResumo,
  fetchAlertas,
  fetchSeries,
  fetchPrevisoes,
} from './services/api';
import {
  Municipio,
  DashboardResumo,
  AlertaVigilancia,
  SerieEpidemiologica,
  PrevisaoIA,
} from './types';
import { MetricCards } from './components/MetricCards';
import { AlertsManager } from './components/AlertsManager';
import { EpidemicChart } from './components/EpidemicChart';
import { ParaibaMap } from './components/ParaibaMap';
import { Activity, Bug, RefreshCw, Filter } from 'lucide-react';

export function App() {
  const [municipios, setMunicipios] = useState<Municipio[]>([]);
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [alertas, setAlertas] = useState<AlertaVigilancia[]>([]);
  const [series, setSeries] = useState<SerieEpidemiologica[]>([]);
  const [previsoes, setPrevisoes] = useState<PrevisaoIA[]>([]);

  // Filtros Globais
  const [selectedGeocode, setSelectedGeocode] = useState<number>(2507507); // João Pessoa por padrão
  const [doenca, setDoenca] = useState<string>('dengue');
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Carregar dados gerais iniciais
  const carregarDadosGerais = async () => {
    try {
      const [munsData, resumoData, alertasData] = await Promise.all([
        fetchMunicipios(),
        fetchDashboardResumo(),
        fetchAlertas(1), // alertas ativos
      ]);
      setMunicipios(munsData);
      setResumo(resumoData);
      setAlertas(alertasData);
    } catch (err) {
      console.error('Erro ao carregar dados gerais:', err);
    } finally {
      setLoading(false);
    }
  };

  // Carregar série e previsões do município selecionado
  const carregarDadosMunicipio = async (geocode: number, doencaAlvo: string) => {
    try {
      const [seriesData, prevData] = await Promise.all([
        fetchSeries(geocode, doencaAlvo, 52),
        fetchPrevisoes(geocode, doencaAlvo),
      ]);
      setSeries(seriesData);
      setPrevisoes(prevData);
    } catch (err) {
      console.error('Erro ao carregar dados do município:', err);
      setSeries([]);
      setPrevisoes([]);
    }
  };

  useEffect(() => {
    carregarDadosGerais();
  }, []);

  useEffect(() => {
    if (selectedGeocode) {
      carregarDadosMunicipio(selectedGeocode, doenca);
    }
  }, [selectedGeocode, doenca]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      carregarDadosGerais(),
      carregarDadosMunicipio(selectedGeocode, doenca),
    ]);
    setRefreshing(false);
  };

  const selectedMunicipioObj = municipios.find((m) => m.geocode === selectedGeocode);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
              <Bug className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-black tracking-tight text-white">ZikAI Paraíba</h1>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  TCC • 2026
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Sistema Inteligente de Vigilância Epidemiológica e Previsão de Arboviroses
              </p>
            </div>
          </div>

          {/* Controles de Filtro Global */}
          <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
            {/* Seletor de Município */}
            <div className="flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedGeocode}
                onChange={(e) => setSelectedGeocode(Number(e.target.value))}
                className="bg-transparent text-xs text-white focus:outline-none cursor-pointer"
              >
                {municipios.map((m) => (
                  <option key={m.geocode} value={m.geocode} className="bg-slate-900 text-white">
                    {m.nome}
                  </option>
                ))}
              </select>
            </div>

            {/* Seletor de Arbovirose */}
            <div className="flex items-center gap-1 bg-slate-800 border border-slate-700 rounded-lg p-1 text-xs font-semibold">
              {(['dengue', 'chikungunya', 'zika'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setDoenca(d)}
                  className={`px-3 py-1 rounded-md capitalize transition-all ${
                    doenca === d
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>

            {/* Botão de Atualizar */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-all active:scale-95 disabled:opacity-50"
              title="Atualizar dados da API"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6 w-full">
        {/* Cards de Métricas Principais */}
        <MetricCards resumo={resumo} loading={loading} />

        {/* Linha Principal: Gráfico e Mapa */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EpidemicChart
            series={series}
            previsoes={previsoes}
            municipioNome={selectedMunicipioObj?.nome || 'Paraíba'}
            doenca={doenca}
          />
          <ParaibaMap
            municipios={municipios}
            selectedGeocode={selectedGeocode}
            onSelectMunicipio={(geo) => setSelectedGeocode(geo)}
          />
        </div>

        {/* Seção de Gestão de Alertas */}
        <AlertsManager
          alertas={alertas}
          municipios={municipios}
          onRefresh={handleRefresh}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500 bg-slate-900/40">
        ZikAI Paraíba • Trabalho de Conclusão de Curso (TCC) • Integração InfoDengue & IBGE • FastAPI + React
      </footer>
    </div>
  );
}

export default App;
