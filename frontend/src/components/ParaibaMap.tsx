import React, { useEffect, useState, useMemo } from 'react';
import { Municipio } from '../types';
import { MapPin, Navigation, Info, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

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
  const [hoveredGeocode, setHoveredGeocode] = useState<number | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Carregar o GeoJSON oficial dos municípios da Paraíba
  useEffect(() => {
    fetch('/pb_malha_municipios.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('Falha ao carregar malha de municípios');
        return res.json();
      })
      .then((data: GeoJSONData) => setGeoData(data))
      .catch((err) => console.error('Erro ao buscar GeoJSON:', err));
  }, []);

  // Bounding box rigoroso da Paraíba (com margens de respiro)
  // Oeste: -38.80, Leste: -34.75, Sul: -8.35, Norte: -6.00
  const bounds = useMemo(() => ({
    minLon: -38.82,
    maxLon: -34.72,
    minLat: -8.35,
    maxLat: -5.98,
  }), []);

  // Proporções ideais preservando a física geográfica da Paraíba (lat ~ -7°)
  const baseWidth = 820;
  const baseHeight = 475;

  const project = (lon: number, lat: number): [number, number] => {
    const x = ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * baseWidth;
    const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * baseHeight;
    return [x, y];
  };

  const coordsToSvgPath = (coords: number[][]) => {
    if (!coords || coords.length === 0) return '';
    return coords
      .map((pt, idx) => {
        const [x, y] = project(pt[0], pt[1]);
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(' ') + ' Z';
  };

  // Mapeamento rápido geocode -> objeto Municipio
  const munMap = useMemo(() => {
    const map = new Map<number, Municipio>();
    municipios.forEach((m) => map.set(m.geocode, m));
    return map;
  }, [municipios]);

  // Pré-computar os caminhos SVG de cada feature
  const parsedFeatures = useMemo(() => {
    if (!geoData) return [];
    return geoData.features.map((feature) => {
      const cod = parseInt(feature.properties.codarea, 10);
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

      return {
        cod,
        pathData,
        mun: munMap.get(cod),
      };
    });
  }, [geoData, munMap]);

  // Separação em camadas para DOM Order:
  // 1. Polígonos neutros no fundo
  // 2. Polígono Hovered em cima
  // 3. Polígono Selecionado no topo absoluto
  const regularFeatures = useMemo(() => {
    return parsedFeatures.filter((f) => f.cod !== selectedGeocode && f.cod !== hoveredGeocode);
  }, [parsedFeatures, selectedGeocode, hoveredGeocode]);

  const hoveredFeature = useMemo(() => {
    if (!hoveredGeocode || hoveredGeocode === selectedGeocode) return null;
    return parsedFeatures.find((f) => f.cod === hoveredGeocode);
  }, [parsedFeatures, hoveredGeocode, selectedGeocode]);

  const selectedFeature = useMemo(() => {
    return parsedFeatures.find((f) => f.cod === selectedGeocode);
  }, [parsedFeatures, selectedGeocode]);

  // Controles de Navegação (Zoom / Pan)
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.3, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.3, 0.8));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const activeMun = munMap.get(hoveredGeocode || selectedGeocode);

  return (
    <div className="bg-slate-800/70 border border-slate-700/60 rounded-xl p-6 shadow-xl backdrop-blur-sm space-y-4">
      {/* Header do Mapa com Ações e Informações */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Navigation className="w-5 h-5 text-emerald-400" />
            Malha Cartográfica da Paraíba (IBGE)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Passe o mouse com precisão sobre os limites exatos e clique para selecionar
          </p>
        </div>

        {/* Badge do Município Inspecionado */}
        {activeMun && (
          <div className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-900 border border-emerald-500/50 rounded-lg text-xs shadow-md animate-in fade-in">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-bold text-white">{activeMun.nome}</span>
            <span className="text-slate-400">
              • População:{' '}
              <strong className="text-emerald-400">
                {activeMun.populacao ? activeMun.populacao.toLocaleString('pt-BR') : 'N/A'}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Container SVG Interativo */}
      <div
        className="relative w-full bg-slate-950/90 rounded-xl border border-slate-800 overflow-hidden cursor-grab active:cursor-grabbing select-none"
        style={{ height: '380px' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Controles Flutuantes de Zoom / Reset */}
        <div className="absolute top-3 right-3 z-10 flex flex-col gap-1.5 bg-slate-900/80 p-1 rounded-lg border border-slate-700/60 shadow-lg backdrop-blur-sm">
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded transition-all"
            title="Aproximar (Zoom In)"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded transition-all"
            title="Afastar (Zoom Out)"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetView}
            className="p-1.5 hover:bg-slate-800 text-slate-300 hover:text-white rounded transition-all border-t border-slate-800"
            title="Redefinir visualização"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {!geoData ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-2">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs">Carregando polígonos dos municípios...</span>
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${baseWidth} ${baseHeight}`}
            className="w-full h-full pointer-events-auto"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: 'center center',
              transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            }}
          >
            {/* 1ª Camada: Polígonos de Base dos Municípios */}
            <g className="municipios-base" pointerEvents="visiblePainted">
              {regularFeatures.map((f) => (
                <path
                  key={f.cod}
                  d={f.pathData}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectMunicipio(f.cod);
                  }}
                  onMouseEnter={() => setHoveredGeocode(f.cod)}
                  onMouseLeave={() => setHoveredGeocode(null)}
                  fill="#1e293b"
                  stroke="#334155"
                  strokeWidth="0.75"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  className="cursor-pointer transition-colors duration-100 hover:fill-emerald-600/70"
                >
                  <title>
                    {f.mun ? `${f.mun.nome} (Pop: ${f.mun.populacao?.toLocaleString('pt-BR') || 'N/A'})` : f.cod}
                  </title>
                </path>
              ))}
            </g>

            {/* 2ª Camada: Polígono Hovered (Renderizado no Topo para evitar sobreposição de borda) */}
            {hoveredFeature && (
              <path
                d={hoveredFeature.pathData}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectMunicipio(hoveredFeature.cod);
                }}
                onMouseLeave={() => setHoveredGeocode(null)}
                fill="#10b981"
                stroke="#34d399"
                strokeWidth="1.75"
                strokeLinejoin="round"
                strokeLinecap="round"
                vectorEffect="non-scaling-stroke"
                className="cursor-pointer drop-shadow-md"
              />
            )}

            {/* 3ª Camada: Polígono Selecionado (Destaque imediato com contorno e preenchimento) */}
            {selectedFeature && (
              <g key={`selected-${selectedFeature.cod}`}>
                <path
                  d={selectedFeature.pathData}
                  fill="#0284c7"
                  stroke="#38bdf8"
                  strokeWidth="2.5"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />

                {/* Rótulo estático nítido no centróide (sem bola animada nem transição fluida) */}
                {selectedFeature.mun?.latitude && selectedFeature.mun?.longitude && (() => {
                  const [cx, cy] = project(selectedFeature.mun.longitude, selectedFeature.mun.latitude);
                  return (
                    <text
                      x={cx}
                      y={cy}
                      textAnchor="middle"
                      dominantBaseline="central"
                      fill="#ffffff"
                      fontSize={11}
                      fontWeight="800"
                      stroke="#0284c7"
                      strokeWidth="3"
                      paintOrder="stroke fill"
                      className="pointer-events-none select-none"
                    >
                      {selectedFeature.mun.nome}
                    </text>
                  );
                })()}
              </g>
            )}
          </svg>
        )}
      </div>

      {/* Rodapé com Instruções e Legenda */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400 pt-1 border-t border-slate-700/50">
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#1e293b] border border-slate-600 inline-block" /> Regular
          <span className="w-2.5 h-2.5 rounded-sm bg-[#10b981] border border-[#34d399] inline-block ml-1" /> Em Foco
          <span className="w-2.5 h-2.5 rounded-sm bg-[#0284c7] border border-[#38bdf8] inline-block ml-1" /> Selecionado
        </span>
        <span className="text-[11px] text-slate-500 flex items-center gap-1">
          <Info className="w-3.5 h-3.5 text-slate-400" />
          Projeção Cartográfica Equirretangular calibrada • 223 Municípios IBGE
        </span>
      </div>
    </div>
  );
};
