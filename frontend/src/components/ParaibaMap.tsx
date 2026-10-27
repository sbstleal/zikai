import React from 'react';
import { Municipio } from '../types';
import { MapPin, Navigation } from 'lucide-react';

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
  // Bounding box aproximado da Paraíba para projeção SVG
  // Longitude: -38.8 (Oeste) a -34.8 (Leste)
  // Latitude: -8.3 (Sul) a -6.0 (Norte)
  const minLon = -38.8;
  const maxLon = -34.8;
  const minLat = -8.3;
  const maxLat = -6.0;

  const width = 600;
  const height = 350;

  const getSvgCoordinates = (lat: number | null, lon: number | null) => {
    if (!lat || !lon) return null;
    const x = ((lon - minLon) / (maxLon - minLon)) * width;
    // Inverter Y porque latitude cresce para o Norte e coordenadas SVG crescem para baixo
    const y = ((maxLat - lat) / (maxLat - minLat)) * height;
    return { x, y };
  };

  const selectedMun = municipios.find((m) => m.geocode === selectedGeocode);

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-xl backdrop-blur-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Navigation className="w-5 h-5 text-emerald-400" />
            Mapa Espacial dos Municípios (PB)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Clique em qualquer ponto do estado para carregar os dados epidemiológicos e projeções de IA
          </p>
        </div>
        {selectedMun && (
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs font-semibold">
            <MapPin className="w-3.5 h-3.5" />
            {selectedMun.nome} (Pop: {selectedMun.populacao?.toLocaleString('pt-BR')})
          </div>
        )}
      </div>

      <div className="relative w-full bg-slate-950/70 rounded-xl border border-slate-800 p-2 overflow-hidden flex items-center justify-center">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto max-h-[360px]">
          {/* Contorno simplificado ilustrativo da PB de fundo */}
          <path
            d="M 50,120 Q 200,80 400,90 T 580,180 Q 520,290 350,260 T 60,250 Z"
            fill="#1e293b"
            stroke="#334155"
            strokeWidth="2"
            strokeDasharray="4 4"
            className="opacity-40"
          />

          {/* Nós dos Municípios */}
          {municipios.map((m) => {
            const coords = getSvgCoordinates(m.latitude, m.longitude);
            if (!coords) return null;
            const isSelected = m.geocode === selectedGeocode;

            return (
              <g
                key={m.geocode}
                onClick={() => onSelectMunicipio(m.geocode)}
                className="cursor-pointer group"
              >
                <circle
                  cx={coords.x}
                  cy={coords.y}
                  r={isSelected ? 7 : 3.5}
                  fill={isSelected ? '#38bdf8' : '#22c55e'}
                  stroke={isSelected ? '#ffffff' : '#0f172a'}
                  strokeWidth={isSelected ? 2 : 1}
                  className="transition-all duration-200 group-hover:scale-150 group-hover:fill-amber-400"
                />
                {isSelected && (
                  <circle
                    cx={coords.x}
                    cy={coords.y}
                    r={14}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="1.5"
                    className="animate-ping opacity-75"
                  />
                )}
                {/* Rótulo dos principais polos */}
                {(isSelected || ['João Pessoa', 'Campina Grande', 'Patos', 'Sousa', 'Cajazeiras'].includes(m.nome)) && (
                  <text
                    x={coords.x}
                    y={coords.y - 8}
                    textAnchor="middle"
                    fill={isSelected ? '#38bdf8' : '#cbd5e1'}
                    fontSize={isSelected ? 10 : 8}
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    className="pointer-events-none select-none drop-shadow-md"
                  >
                    {m.nome}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
        <span>Sertão / Alto Sertão (Oeste)</span>
        <span className="font-semibold text-slate-300">Georreferenciamento IBGE 2024</span>
        <span>Litoral / João Pessoa (Leste)</span>
      </div>
    </div>
  );
};
