import React, { useEffect, useState, useMemo } from 'react';
import { Municipio } from '../types';
import { MapPin, Navigation, Info } from 'lucide-react';

interface FeatureGeometry {
  type: string;
  coordinates: any;
}

interface GeoFeature {
  type: string;
  properties: {
    codarea: string;
  };
  geometry: FeatureGeometry;
}

interface GeoJSONData {
  type: string;
  features: GeoFeature[];
}

interface ParaibaMapProps {
  municipios: Municipio[];
  selectedGeocode: number;
  onSelectMunicipio: (geocode: number) => void;
}

export const ParaibaMap: React.FC<ParaibaMapProps> = ({
  municipios,
  selectedGeocode,
  onSelectMunicipio,
}) => {
  const [geoData, setGeoData] = useState<GeoJSONData | null>(null);
  const [hoveredMun, setHoveredMun] = useState<Municipio | null>(null);

  // Carregar o GeoJSON real dos 223 municípios da Paraíba
  useEffect(() => {
    fetch('/pb_malha_municipios.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('Falha ao carregar malha de municípios');
        return res.json();
      })
      .then((data: GeoJSONData) => setGeoData(data))
      .catch((err) => console.error('Erro ao buscar GeoJSON:', err));
  }, []);

  // Bounding box exato da Paraíba com margem de respiro
  const bounds = useMemo(() => {
    return {
      minLon: -38.85,
      maxLon: -34.70,
      minLat: -8.38,
      maxLat: -5.95,
    };
  }, []);

  const width = 800;
  const height = 480;

  // Projeção Mercator/Equirretangular adaptada para a Paraíba
  const project = (lon: number, lat: number) => {
    const x = ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * width;
    const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * height;
    return [x, y];
  };

  // Converte anéis de coordenadas GeoJSON em caminho SVG "M x y L x y Z"
  const coordsToSvgPath = (coords: number[][]) => {
    if (!coords || coords.length === 0) return '';
    return coords
      .map((pt, idx) => {
        const [x, y] = project(pt[0], pt[1]);
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ') + ' Z';
  };

  // Mapeamento rápido de geocode para dados do município
  const munMap = useMemo(() => {
    const map = new Map<number, Municipio>();
    municipios.forEach((m) => map.set(m.geocode, m));
    return map;
  }, [municipios]);

  const selectedMun = munMap.get(selectedGeocode);

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-xl backdrop-blur-sm space-y-4">
      {/* Header do Mapa */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Navigation className="w-5 h-5 text-emerald-400" />
            Malha Cartográfica da Paraíba (IBGE)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Passe o mouse para inspecionar e clique sobre qualquer um dos 223 municípios
          </p>
        </div>

        {/* Badge do Município Ativo */}
        {(hoveredMun || selectedMun) && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-emerald-500/40 rounded-lg text-xs shadow-md">
            <MapPin className="w-3.5 h-3.5 text-emerald-400 animate-bounce" />
            <span className="font-bold text-white">
              {(hoveredMun || selectedMun)?.nome}
            </span>
            <span className="text-slate-400">
              • Pop:{' '}
              <strong className="text-emerald-400">
                {(hoveredMun || selectedMun)?.populacao?.toLocaleString('pt-BR') || 'N/A'}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Área do SVG com contornos reais dos polígonos */}
      <div className="relative w-full bg-slate-950/80 rounded-xl border border-slate-800/80 p-2 overflow-hidden flex items-center justify-center min-h-[360px]">
        {!geoData ? (
          <div className="flex flex-col items-center justify-center text-slate-400 gap-2 py-16 animate-pulse">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs">Carregando contornos dos municípios da Paraíba...</span>
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto max-h-[420px] select-none filter drop-shadow-lg"
          >
            {/* Renderização de cada município como um polígono SVG real */}
            {geoData.features.map((feature, i) => {
              const cod = parseInt(feature.properties.codarea, 10);
              const mun = munMap.get(cod);
              const isSelected = cod === selectedGeocode;
              const isHovered = hoveredMun?.geocode === cod;

              const geom = feature.geometry;
              let pathData = '';

              if (geom.type === 'Polygon') {
                pathData = geom.coordinates.map((ring: number[][]) => coordsToSvgPath(ring)).join(' ');
              } else if (geom.type === 'MultiPolygon') {
                pathData = geom.coordinates
                  .map((poly: number[][][]) =>
                    poly.map((ring: number[][]) => coordsToSvgPath(ring)).join(' ')
                  )
                  .join(' ');
              }

              return (
                <path
                  key={cod || i}
                  d={pathData}
                  onClick={() => onSelectMunicipio(cod)}
                  onMouseEnter={() => mun && setHoveredMun(mun)}
                  onMouseLeave={() => setHoveredMun(null)}
                  fill={
                    isSelected
                      ? '#38bdf8' // Azul celeste vívido quando selecionado
                      : isHovered
                      ? '#10b981' // Verde esmeralda quando hovered
                      : '#1e293b' // Slate-800 suave padrão
                  }
                  stroke={
                    isSelected
                      ? '#ffffff'
                      : isHovered
                      ? '#34d399'
                      : '#334155'
                  }
                  strokeWidth={isSelected ? 2 : isHovered ? 1.5 : 0.6}
                  strokeLinejoin="round"
                  className="cursor-pointer transition-colors duration-150 hover:brightness-125"
                >
                  <title>
                    {mun ? `${mun.nome} (IBGE: ${cod}) - População: ${mun.populacao?.toLocaleString('pt-BR') || 'N/A'}` : cod}
                  </title>
                </path>
              );
            })}

            {/* Marcador de destaque com pulso para o município selecionado */}
            {selectedMun && selectedMun.latitude && selectedMun.longitude && (() => {
              const [cx, cy] = project(selectedMun.longitude, selectedMun.latitude);
              return (
                <g className="pointer-events-none">
                  <circle
                    cx={cx}
                    cy={cy}
                    r={5}
                    fill="#38bdf8"
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                  <circle
                    cx={cx}
                    cy={cy}
                    r={14}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    className="animate-ping opacity-60"
                  />
                  <text
                    x={cx}
                    y={cy - 10}
                    textAnchor="middle"
                    fill="#38bdf8"
                    fontSize={11}
                    fontWeight="bold"
                    className="drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
                  >
                    {selectedMun.nome}
                  </text>
                </g>
              );
            })()}
          </svg>
        )}
      </div>

      {/* Legenda e Referências Geográficas */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400 pt-1 border-t border-slate-700/50">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#1e293b] border border-slate-600 inline-block" /> Município Regular
          <span className="w-2.5 h-2.5 rounded-sm bg-[#38bdf8] border border-white inline-block ml-2" /> Município Selecionado
        </span>
        <span className="text-[11px] text-slate-500 flex items-center gap-1">
          <Info className="w-3.5 h-3.5 text-slate-400" />
          Malha Cartográfica Digital Oficial IBGE (223 Municípios)
        </span>
      </div>
    </div>
  );
};
