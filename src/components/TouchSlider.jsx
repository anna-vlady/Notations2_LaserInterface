import React, { useRef, useState, useEffect } from 'react';

export default function TouchSlider({ label, value, onChange }) {
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
    // Calculate 0.0 (bottom) to 1.0 (top)
    const rawVal = 1 - (e.clientY - rect.top) / rect.height;
    const clamped = Math.max(0, Math.min(1, rawVal));
    const rounded = parseFloat(clamped.toFixed(3));

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
      // Send final crisp value
      onChange(latestVal.current);
    }
  };

  return (
    <div className="slider-column">
      <div className="slider-value-badge">{(val * 100).toFixed(0)}%</div>
      <div 
        ref={trackRef}
        className="slider-track"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
      >
        <div 
          className="slider-fill" 
          style={{ height: `${val * 100}%` }} 
        />
      </div>
      <div className="slider-title">{label}</div>
    </div>
  );
}
