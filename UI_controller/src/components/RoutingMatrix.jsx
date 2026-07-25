import React from 'react';
import { Sliders, RefreshCw, Terminal, Cpu } from 'lucide-react';

export default function RoutingMatrix({ crossMod, onToggleCrossMod, logs = [] }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '10px' }}>
      <div className="matrix-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={16} color="var(--cyan-primary)" />
          <span className="matrix-label">Ableton Peak $\rightarrow$ Laser Flash</span>
        </div>
        <div 
          className={`switch-toggle ${crossMod ? 'on' : ''}`}
          onClick={() => onToggleCrossMod(!crossMod)}
        >
          <div className="switch-handle" />
        </div>
      </div>

      <div className="matrix-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <RefreshCw size={16} color="var(--magenta-laser)" />
          <span className="matrix-label">Laser XY $\rightarrow$ Audio Filter Modulation</span>
        </div>
        <div className="switch-toggle on">
          <div className="switch-handle" />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
        <Terminal size={14} />
        <span>REAL-TIME OSC DISPATCH LOG</span>
      </div>

      <div className="log-box">
        {logs.length === 0 ? (
          <div className="log-entry" style={{ color: '#475569' }}>Waiting for touch interactions...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className="log-entry">
              [{log.time}] &gt; <strong style={{ color: log.target === 'madmapper' ? 'var(--magenta-laser)' : 'var(--amber-audio)' }}>{log.target.toUpperCase()}</strong> {log.address} {JSON.stringify(log.args)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
