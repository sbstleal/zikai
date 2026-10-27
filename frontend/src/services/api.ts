import {
  Municipio,
  DashboardResumo,
  AlertaVigilancia,
  SerieEpidemiologica,
  PrevisaoIA,
} from '../types';

const API_BASE = '/api';

export async function fetchMunicipios(): Promise<Municipio[]> {
  const res = await fetch(`${API_BASE}/municipios`);
  if (!res.ok) throw new Error('Falha ao carregar catálogo de municípios');
  return res.json();
}

export async function fetchDashboardResumo(): Promise<DashboardResumo> {
  const res = await fetch(`${API_BASE}/dashboard/resumo`);
  if (!res.ok) throw new Error('Falha ao carregar resumo do dashboard');
  return res.json();
}

export async function fetchAlertas(ativo?: number): Promise<AlertaVigilancia[]> {
  const url = ativo !== undefined ? `${API_BASE}/alertas?ativo=${ativo}` : `${API_BASE}/alertas`;
  const res = await fetch(url);
  if (res.status === 404) return [];
  if (!res.ok) throw new Error('Falha ao carregar alertas');
  return res.json();
}

export async function resolverAlerta(alertaId: number, ativo: number = 0): Promise<AlertaVigilancia> {
  const res = await fetch(`${API_BASE}/alertas/${alertaId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ativo }),
  });
  if (!res.ok) throw new Error('Falha ao atualizar status do alerta');
  return res.json();
}

export async function criarAlerta(dados: {
  municipio_geocode: number;
  doenca: string;
  titulo: string;
  mensagem: string;
  nivel_gravidade: number;
}): Promise<AlertaVigilancia> {
  const res = await fetch(`${API_BASE}/alertas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  if (!res.ok) throw new Error('Falha ao criar novo alerta');
  return res.json();
}

export async function fetchSeries(geocode: number, doenca?: string, limite: number = 52): Promise<SerieEpidemiologica[]> {
  let url = `${API_BASE}/series/${geocode}?limite=${limite}&ordenacao=asc`;
  if (doenca) url += `&doenca=${doenca}`;
  const res = await fetch(url);
  if (res.status === 404) return [];
  if (!res.ok) throw new Error('Falha ao carregar série histórica');
  return res.json();
}

export async function fetchPrevisoes(geocode: number, doenca?: string): Promise<PrevisaoIA[]> {
  let url = `${API_BASE}/previsoes/${geocode}`;
  if (doenca) url += `?doenca=${doenca}`;
  const res = await fetch(url);
  if (res.status === 404) return [];
  if (!res.ok) throw new Error('Falha ao carregar previsões de IA');
  return res.json();
}

export async function fetchMapaGeoJSON(): Promise<any> {
  const res = await fetch(`${API_BASE}/mapa/paraiba.geojson`);
  if (!res.ok) {
    // Fallback para rota antiga se houver
    const fallbackRes = await fetch(`${API_BASE}/mapa/geojson`);
    if (!fallbackRes.ok) throw new Error('Falha ao carregar GeoJSON da Paraíba');
    return fallbackRes.json();
  }
  return res.json();
}
