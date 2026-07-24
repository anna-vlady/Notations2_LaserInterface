import React from 'react';
import { Zap, Circle, Grid, Layers, Eye, ShieldAlert, Sparkles, Activity } from 'lucide-react';

const CUE_PRESETS = [
  { id: 1, name: 'BEAM GRID', icon: Grid, osc: '/madmapper/cue/1' },
  { id: 2, name: 'SCAN WAVE', icon: Activity, osc: '/madmapper/cue/2' },
  { id: 3, name: 'LASER CONE', icon: Layers, osc: '/madmapper/cue/3' },
  { id: 4, name: 'ROTATING 3D', icon: Circle, osc: '/madmapper/cue/4' },
  { id: 5, name: 'STROBE PULSE', icon: Zap, osc: '/madmapper/cue/5' },
  { id: 6, name: 'TUNNEL FX', icon: Eye, osc: '/madmapper/cue/6' },
  { id: 7, name: 'CYBER RAIN', icon: Sparkles, osc: '/madmapper/cue/7' },
  { id: 8, name: 'EMERGENCY', icon: ShieldAlert, osc: '/madmapper/cue/8' },
];

export default function CueGrid({ activeCue, onCueTrigger }) {
  return (
    <div className="cue-grid">
      {CUE_PRESETS.map((cue) => {
        const Icon = cue.icon;
        const isActive = activeCue === cue.id;
        return (
          <button
            key={cue.id}
            className={`cue-btn ${isActive ? 'active' : ''}`}
            onClick={() => onCueTrigger(cue)}
          >
            <Icon size={18} />
            <span>{cue.name}</span>
          </button>
        );
      })}
    </div>
  );
}
