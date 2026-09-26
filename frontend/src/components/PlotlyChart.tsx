import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

interface PlotlyChartProps {
  spec: any;
  height?: number;
}

const MONOCHROME_COLORS = ['#ffffff', '#a3a3a3', '#737373', '#e5e5e5', '#525252', '#d4d4d4', '#262626'];

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ spec, height = 400 }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !spec) return;

    // Apply monochrome palette to traces
    const rawData = JSON.parse(JSON.stringify(spec.data || []));
    const data = rawData.map((trace: any, idx: number) => {
      const color = MONOCHROME_COLORS[idx % MONOCHROME_COLORS.length];
      if (trace.marker) {
        if (Array.isArray(trace.marker.color)) {
          // Grayscale gradient array
          trace.marker.color = trace.marker.color.map((_: any, i: number) => 
            MONOCHROME_COLORS[i % (MONOCHROME_COLORS.length - 1)]
          );
        } else {
          trace.marker.color = color;
        }
        trace.marker.line = { color: '#ffffff', width: 0.5 };
      } else {
        trace.marker = { color: color };
      }

      if (trace.line) {
        trace.line.color = color;
      }
      return trace;
    });

    const layout = {
      ...(spec.layout || {}),
      autosize: true,
      height: height,
      margin: { t: 40, r: 30, l: 50, b: 50 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#e5e5e5', family: 'Inter, system-ui, sans-serif' },
      xaxis: {
        ...(spec.layout?.xaxis || {}),
        gridcolor: '#262626',
        zerolinecolor: '#404040',
        tickfont: { color: '#a3a3a3' },
        titlefont: { color: '#e5e5e5' }
      },
      yaxis: {
        ...(spec.layout?.yaxis || {}),
        gridcolor: '#262626',
        zerolinecolor: '#404040',
        tickfont: { color: '#a3a3a3' },
        titlefont: { color: '#e5e5e5' }
      }
    };
    const config = { responsive: true, displayModeBar: false };

    Plotly.newPlot(containerRef.current, data, layout, config);

    const handleResize = () => {
      if (containerRef.current) {
        Plotly.Plots.resize(containerRef.current);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [spec, height]);

  return <div ref={containerRef} className="w-full rounded-xl overflow-hidden bg-black/40 border border-neutral-800" />;
};

