export interface Municipio {
  geocode: number;
  nome: string;
  microrregiao: string | null;
  mesorregiao: string | null;
  populacao: number | null;
  latitude: number | null;
  longitude: number | null;
}

export interface DashboardResumo {
  total_municipios: number;
  total_alertas_ativos: number;
  total_previsoes_ia: number;
  alertas_por_gravidade: Record<string, number>;
}

export interface AlertaVigilancia {
  id: number;
  municipio_geocode: number;
  doenca: string;
  titulo: string;
  mensagem: string;
  nivel_gravidade: number; // 1=Verde, 2=Amarelo, 3=Laranja, 4=Vermelho
  ativo: number; // 1=Ativo, 0=Resolvido
  emitido_em: string;
}

export interface SerieEpidemiologica {
  municipio_geocode: number;
  doenca: string;
  data_inicio_se: string;
  ano: number;
  semana_epidemiologica: number;
  casos_notificados: number;
  casos_estimados: number;
  taxa_reproducao_rt: number | null;
  probabilidade_rt_maior_1: number | null;
  nivel_alerta: number;
  incidencia_100k: number | null;
  temperatura_media: number | null;
  temperatura_minima: number | null;
  temperatura_maxima: number | null;
  umidade_media: number | null;
}

export interface PrevisaoIA {
  municipio_geocode: number;
  doenca: string;
  horizonte_semanas: number;
  ano_alvo: number;
  semana_alvo: number;
  casos_previstos: number;
  intervalo_inferior: number | null;
  intervalo_superior: number | null;
  nivel_risco_previsto: number;
  probabilidade_surto: number | null;
  modelo_utilizado: string;
  gerado_em: string;
}
