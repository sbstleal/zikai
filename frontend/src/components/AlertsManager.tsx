import React, { useState } from 'react';
import { AlertaVigilancia, Municipio } from '../types';
import { ShieldAlert, CheckCircle2, PlusCircle, AlertTriangle } from 'lucide-react';
import { resolverAlerta, criarAlerta } from '../services/api';

interface AlertsManagerProps {
  alertas: AlertaVigilancia[];
  municipios: Municipio[];
  onRefresh: () => void;
}

export const AlertsManager: React.FC<AlertsManagerProps> = ({ alertas, municipios, onRefresh }) => {
  const [modalAberto, setModalAberto] = useState(false);
  const [loading, setLoading] = useState(false);

  // Formulário de novo alerta
  const [selectedGeocode, setSelectedGeocode] = useState<number>(municipios[0]?.geocode || 2507507);
  const [doenca, setDoenca] = useState('dengue');
  const [titulo, setTitulo] = useState('');
  const [mensagem, setMensagem] = useState('');
  const [gravidade, setGravidade] = useState(2);

  const handleResolver = async (id: number) => {
    try {
      await resolverAlerta(id, 0);
      onRefresh();
    } catch (err) {
      alert('Erro ao marcar alerta como resolvido.');
    }
  };

  const handleCriarAlerta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!titulo || !mensagem) {
      alert('Preencha todos os campos do formulário.');
      return;
    }
    setLoading(true);
    try {
      await criarAlerta({
        municipio_geocode: Number(selectedGeocode),
        doenca,
        titulo,
        mensagem,
        nivel_gravidade: Number(gravidade),
      });
      setModalAberto(false);
      setTitulo('');
      setMensagem('');
      onRefresh();
    } catch (err) {
      alert('Erro ao criar alerta de vigilância.');
    } finally {
      setLoading(false);
    }
  };

  const getBadgeGravidade = (nivel: number) => {
    switch (nivel) {
      case 1:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Nível 1 - Verde</span>;
      case 2:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">Nível 2 - Amarelo</span>;
      case 3:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-orange-500/20 text-orange-400 border border-orange-500/30">Nível 3 - Laranja</span>;
      case 4:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">Nível 4 - Vermelho</span>;
      default:
        return null;
    }
  };

  // Mapear geocode para nome do município
  const getNomeMunicipio = (geocode: number) => {
    const mun = municipios.find((m) => m.geocode === geocode);
    return mun ? mun.nome : `Geocode: ${geocode}`;
  };

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
            Central de Alertas Epidemiológicos
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Notificações ativas geradas pelos modelos preditivos e vigilância em saúde
          </p>
        </div>
        <button
          onClick={() => setModalAberto(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-all shadow-md active:scale-95"
        >
          <PlusCircle className="w-4 h-4" />
          Emitir Novo Alerta
        </button>
      </div>

      {alertas.length === 0 ? (
        <div className="text-center py-10 text-slate-400 border border-dashed border-slate-700 rounded-lg">
          <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-400 mb-2 opacity-80" />
          <p className="text-sm font-medium">Nenhum alerta pendente no estado da Paraíba.</p>
          <p className="text-xs text-slate-500">Todos os alertas foram resolvidos ou estão inativos.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alertas.map((alerta) => (
            <div
              key={alerta.id}
              className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-slate-900/60 border border-slate-700/50 rounded-xl hover:border-slate-600 transition-all gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-white text-sm">{alerta.titulo}</span>
                  {getBadgeGravidade(alerta.nivel_gravidade)}
                  <span className="text-xs uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {alerta.doenca}
                  </span>
                  <span className="text-xs text-slate-400">• {getNomeMunicipio(alerta.municipio_geocode)}</span>
                </div>
                <p className="text-xs text-slate-300">{alerta.mensagem}</p>
                <p className="text-[11px] text-slate-500">
                  Emitido em: {new Date(alerta.emitido_em).toLocaleString('pt-BR')}
                </p>
              </div>

              <button
                onClick={() => handleResolver(alerta.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-400 border border-slate-700 hover:border-emerald-500/30 rounded-lg text-xs font-medium transition-all self-end md:self-center"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Marcar como Resolvido
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Modal de Criação de Alerta */}
      {modalAberto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-700 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Emitir Alerta Epidemiológico
              </h3>
              <button
                onClick={() => setModalAberto(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCriarAlerta} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Município Alvo</label>
                <select
                  value={selectedGeocode}
                  onChange={(e) => setSelectedGeocode(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  {municipios.map((m) => (
                    <option key={m.geocode} value={m.geocode}>
                      {m.nome} (IBGE: {m.geocode})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Arbovirose</label>
                  <select
                    value={doenca}
                    onChange={(e) => setDoenca(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="dengue">Dengue</option>
                    <option value="chikungunya">Chikungunya</option>
                    <option value="zika">Zika</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Nível de Gravidade</label>
                  <select
                    value={gravidade}
                    onChange={(e) => setGravidade(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value={1}>1 - Verde (Baixo)</option>
                    <option value={2}>2 - Amarelo (Atenção)</option>
                    <option value={3}>3 - Laranja (Alerta)</option>
                    <option value={4}>4 - Vermelho (Crítico / Surto)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Título do Alerta</label>
                <input
                  type="text"
                  placeholder="Ex: Alerta de aumento abrupto de casos"
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Mensagem Detalhada</label>
                <textarea
                  rows={3}
                  placeholder="Descreva a situação epidemiológica ou ações recomendadas..."
                  value={mensagem}
                  onChange={(e) => setMensagem(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-700">
                <button
                  type="button"
                  onClick={() => setModalAberto(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm font-semibold transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-all shadow-md active:scale-95 disabled:opacity-50"
                >
                  {loading ? 'Emitindo...' : 'Confirmar Emissão'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
