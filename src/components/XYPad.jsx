import React, { useRef, useEffect, useState } from 'react';

export default function XYPad({ onPosChange }) {
  const canvasRef = useRef(null);
  const [pos, setPos] = useState({ x: 0.5, y: 0.5 });
  const isDragging = useRef(false);

  const updatePosition = (clientX, clientY) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (clientY - rect.top) / rect.height));

    setPos({ x, y });
    if (onPosChange) {
      onPosChange(parseFloat(x.toFixed(3)), parseFloat(y.toFixed(3)));
    }
  };

  const handlePointerDown = (e) => {
    isDragging.current = true;
    e.target.setPointerCapture(e.pointerId);
    updatePosition(e.clientX, e.clientY);
  };

  const handlePointerMove = (e) => {
    if (isDragging.current) {
      updatePosition(e.clientX, e.clientY);
    }
  };

  const handlePointerUp = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Handle high DPI crisp drawing
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const width = canvas.width;
    const height = canvas.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Subtle Grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    
    // Grid lines (3x3)
    ctx.beginPath();
    ctx.moveTo(width / 3, 0); ctx.lineTo(width / 3, height);
    ctx.moveTo((2 * width) / 3, 0); ctx.lineTo((2 * width) / 3, height);
    ctx.moveTo(0, height / 3); ctx.lineTo(width, height / 3);
    ctx.moveTo(0, (2 * height) / 3); ctx.lineTo(width, (2 * height) / 3);
    ctx.stroke();

    // Center Crosshairs
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.beginPath();
    ctx.moveTo(pos.x * width, 0);
    ctx.lineTo(pos.x * width, height);
    ctx.moveTo(0, pos.y * height);
    ctx.lineTo(width, pos.y * height);
    ctx.stroke();

    // Touch Indicator Dot (Grayscale Glow)
    ctx.shadowBlur = 12;
    ctx.shadowColor = '#ffffff';
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(pos.x * width, pos.y * height, 14, 0, Math.PI * 2);
    ctx.fill();

    // Inner Core Dot
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(pos.x * width, pos.y * height, 4, 0, Math.PI * 2);
    ctx.fill();
  }, [pos]);

  return (
    <div className="xypad-wrapper">
      <canvas
        ref={canvasRef}
        className="xypad-canvas"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      />
    </div>
  );
}
