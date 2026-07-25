import React from 'react';

function SingleFader({ label, value, onChange, color = 'var(--amber-audio)' }) {
  const handlePointerDown = (e) => {
    const track = e.currentTarget;
    track.setPointerCapture(e.pointerId);
    updateFader(e, track);
  };

  const handlePointerMove = (e) => {
    if (e.buttons > 0) {
      updateFader(e, e.currentTarget);
    }
  };

  const updateFader = (e, track) => {
    const rect = track.getBoundingClientRect();
    // 0 at bottom, 1 at top
    const val = Math.max(0, Math.min(1, 1 - (e.clientY - rect.top) / rect.height));
    onChange(parseFloat(val.toFixed(2)));
  };

  return (
    <div className="fader-column">
      <div className="fader-val">{(value * 100).toFixed(0)}</div>
      <div 
        className="fader-track-wrap"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
      >
        <div 
          className="fader-fill" 
          style={{ 
            height: `${value * 100}%`,
            background: color
          }} 
        />
      </div>
      <div className="fader-label">{label}</div>
    </div>
  );
}

export default function FaderBank({ faders, onFaderChange }) {
  return (
    <div className="faders-bank">
      {faders.map((fader) => (
        <SingleFader
          key={fader.id}
          label={fader.label}
          value={fader.value}
          color={fader.color}
          onChange={(val) => onFaderChange(fader.id, val)}
        />
      ))}
    </div>
  );
}
