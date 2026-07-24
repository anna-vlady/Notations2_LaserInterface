import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { Maximize2, Power, Zap } from 'lucide-react';
import TouchSlider from './components/TouchSlider';

const socket = io('http://localhost:4000', { autoConnect: true });

export default function App() {
  // Laser & Audio States
  const [laserPower, setLaserPower] = useState(true);
  const [patternStrobe, setPatternStrobe] = useState(false);
  const [laserSize, setLaserSize] = useState(0.5);
  const [laserIntensity, setLaserIntensity] = useState(0.85);

  // Temporary Dispatch Log
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const handleOscDispatched = (entry) => {
      const formatted = {
        id: Math.random(),
        time: new Date(entry.timestamp).toLocaleTimeString().split(' ')[0],
        target: entry.target,
        address: entry.address,
        args: entry.args
      };
      setLogs((prev) => [formatted, ...prev].slice(0, 20));
    };

    socket.on('osc-dispatched', handleOscDispatched);

    return () => {
      socket.off('osc-dispatched', handleOscDispatched);
    };
  }, []);

  // Dispatch OSC message helper (target: 'madmapper' | 'ableton' | 'both')
  const sendOsc = (target, address, args) => {
    socket.emit('send-osc', { target, address, args });
  };

  // Button 1: Tap Toggle Power Switch
  const handleTogglePower = () => {
    const nextState = !laserPower;
    setLaserPower(nextState);
    const stateVal = nextState ? 1.0 : 0.0;
    sendOsc('madmapper', '/madmapper/laser/power', stateVal);
    sendOsc('ableton', '/live/master/mute', nextState ? 0 : 1);
  };

  // Button 2: Momentary Hold Strobe Button (Press down = ON, Release = OFF)
  const handleStrobePress = (e) => {
    if (e && e.currentTarget && e.pointerId) {
      e.currentTarget.setPointerCapture(e.pointerId);
    }
    setPatternStrobe(true);
    sendOsc('madmapper', '/madmapper/laser/strobe', 1.0);
    sendOsc('ableton', '/live/repeat/enable', 1.0);
  };

  const handleStrobeRelease = () => {
    setPatternStrobe(false);
    sendOsc('madmapper', '/madmapper/laser/strobe', 0.0);
    sendOsc('ableton', '/live/repeat/enable', 0.0);
  };

  // Keyboard 'Q' Key Binding (Press and hold 'Q' to strobe)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'q' || e.key === 'Q') {
        if (e.repeat) return;
        setPatternStrobe(true);
        sendOsc('madmapper', '/madmapper/laser/strobe', 1.0);
        sendOsc('ableton', '/live/repeat/enable', 1.0);
      }
    };

    const handleKeyUp = (e) => {
      if (e.key === 'q' || e.key === 'Q') {
        setPatternStrobe(false);
        sendOsc('madmapper', '/madmapper/laser/strobe', 0.0);
        sendOsc('ableton', '/live/repeat/enable', 0.0);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // SLIDER 1: Controls Laser Size in MadMapper AND Param 1 in Ableton
  const handleSizeChange = (val) => {
    setLaserSize(val);
    sendOsc('madmapper', '/madmapper/laser/size', val);
    sendOsc('ableton', '/live/device/param/1', val);
  };

  // SLIDER 2: Controls Laser Intensity in MadMapper AND Param 2 in Ableton (Symmetrical to Slider 1!)
  const handleIntensityChange = (val) => {
    setLaserIntensity(val);
    sendOsc('madmapper', '/madmapper/laser/intensity', val);
    sendOsc('ableton', '/live/device/param/2', val);
  };

  const handleToggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  return (
    <div className="app-container">
      {/* Temporary Utility Bar for Kiosk testing */}
      <div className="utility-bar">
        <button className="btn-utility" onClick={handleToggleFullscreen}>
          <Maximize2 size={14} />
          <span>FULLSCREEN</span>
        </button>
      </div>

      {/* Main Ultra-Simple Touch Surface Grid */}
      <main className="touch-surface-grid">
        {/* COLUMN 1: 2 ON / OFF BUTTONS */}
        <section className="card-section">
          <div className="section-label">SWITCHES</div>

          <div className="toggles-stack">
            {/* TAP TOGGLE BUTTON */}
            <button 
              className={`toggle-btn ${laserPower ? 'on' : ''}`}
              onClick={handleTogglePower}
            >
              <Power size={26} />
              <span>LASER {laserPower ? 'ON' : 'OFF'}</span>
            </button>

            {/* MOMENTARY HOLD BUTTON (TOUCH & 'Q' KEY) */}
            <button 
              className={`toggle-btn ${patternStrobe ? 'on' : ''}`}
              onPointerDown={handleStrobePress}
              onPointerUp={handleStrobeRelease}
              onPointerLeave={handleStrobeRelease}
              onPointerCancel={handleStrobeRelease}
            >
              <Zap size={26} />
              <span>{patternStrobe ? 'STROBE ACTIVE (Q)' : 'HOLD STROBE [Q]'}</span>
            </button>
          </div>
        </section>

        {/* COLUMN 2: 2 DUAL-ROUTED TOUCH SLIDERS */}
        <section className="card-section">
          <div className="section-label">SLIDERS</div>

          <div className="sliders-group">
            <TouchSlider 
              label="SIZE & SPEED" 
              value={laserSize} 
              onChange={handleSizeChange} 
            />

            <TouchSlider 
              label="INTENSITY" 
              value={laserIntensity} 
              onChange={handleIntensityChange} 
            />
          </div>
        </section>
      </main>

      {/* TEMPORARY DISPATCH LOG (For testing, easy to remove in final) */}
      <div className="dev-log-container">
        <div style={{ fontSize: '0.7rem', color: '#666', marginBottom: '2px' }}>OSC DUAL-DISPATCH TELEMETRY (MADMAPPER + ABLETON)</div>
        {logs.length === 0 ? (
          <div className="dev-log-entry" style={{ color: '#444' }}>Touch controls to test dual OSC packet flow...</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="dev-log-entry">
              [{log.time}] &gt; <strong style={{ color: log.target === 'madmapper' ? '#ffffff' : '#888888' }}>[{log.target.toUpperCase()}]</strong> {log.address} {JSON.stringify(log.args)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
