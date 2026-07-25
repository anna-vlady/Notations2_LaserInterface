import React, { useRef, useState, useEffect } from 'react';

export default function TouchSlider({ label, value, onChange, colorClass }) {
  const [val, setVal] = useState(value);
  const trackRef = useRef(null);
  const isDragging = useRef(false);
  const rafId = useRef(null);
  const latestVal = useRef(value);

  // Sync internal state if external value changes
  useEffect(() => {
    if (!isDragging.current) {
      setVal(value);
      latestVal.current = value;
    }
  }, [value]);

  const updateFromPointer = (e) => {
    const track = trackRef.current;
    if (!track) return;
    const rect = track.getBoundingClientRect();
    
    const knobRadius = 27; // Half of 54px circular knob height
    const minCenterY = knobRadius;
    const maxCenterY = rect.height - knobRadius;

    const relativeY = e.clientY - rect.top;
    const clampedY = Math.max(minCenterY, Math.min(maxCenterY, relativeY));
    
    // Calculate 0.0 (bottom) to 1.0 (top)
    const travelRange = maxCenterY - minCenterY;
    const rawVal = travelRange > 0 ? 1 - (clampedY - minCenterY) / travelRange : 0.5;
    const rounded = parseFloat(Math.max(0, Math.min(1, rawVal)).toFixed(3));

    setVal(rounded);
    latestVal.current = rounded;

    // Schedule 60fps throttled OSC callback via rAF
    if (!rafId.current) {
      rafId.current = requestAnimationFrame(() => {
        onChange(latestVal.current);
        rafId.current = null;
      });
    }
  };

  const handlePointerDown = (e) => {
    isDragging.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
    updateFromPointer(e);
  };

  const handlePointerMove = (e) => {
    if (isDragging.current) {
      updateFromPointer(e);
    }
  };

  const handlePointerUp = (e) => {
    if (isDragging.current) {
      isDragging.current = false;
      onChange(latestVal.current);
    }
  };

  return (
    <div className="slider-unit">
      <div 
        ref={trackRef}
        className="track-recess"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        <div className="track-line" />
        <div 
          className={`circular-knob ${colorClass || ''}`} 
          style={{ top: `calc(27px + ${(1 - val)} * (100% - 54px))` }} 
        />
      </div>
      <div className="label-tag">
        {label} <span className="value-display">{(val * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}


