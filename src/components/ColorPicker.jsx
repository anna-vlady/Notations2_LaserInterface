import React from 'react';

const COLOR_PRESETS = [
  { id: 'cyan', hex: '#00f3ff', name: 'Cyber Cyan' },
  { id: 'magenta', hex: '#ff0055', name: 'Laser Magenta' },
  { id: 'green', hex: '#00ff66', name: 'Toxic Green' },
  { id: 'amber', hex: '#ff9900', name: 'Neon Amber' },
  { id: 'purple', hex: '#a855f7', name: 'UV Purple' },
  { id: 'white', hex: '#ffffff', name: 'Pure White' },
];

export default function ColorPicker({ activeColor, onColorSelect }) {
  return (
    <div className="color-presets">
      {COLOR_PRESETS.map((c) => (
        <button
          key={c.id}
          className={`color-dot ${activeColor === c.hex ? 'active' : ''}`}
          style={{ backgroundColor: c.hex, color: c.hex }}
          title={c.name}
          onClick={() => onColorSelect(c.hex)}
        />
      ))}
    </div>
  );
}
