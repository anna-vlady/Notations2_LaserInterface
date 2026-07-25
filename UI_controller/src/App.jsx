import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import { Maximize2 } from 'lucide-react';
import TouchSlider from './components/TouchSlider';

const socket = io('http://localhost:4000', { autoConnect: true });

export default function App() {
  // Laser & Audio States
  const [laserPower, setLaserPower] = useState(false);
  const [patternStrobe, setPatternStrobe] = useState(false);
  const [laserSize, setLaserSize] = useState(0.5);
  const [laserIntensity, setLaserIntensity] = useState(0.7);

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

  // Button 2: Toggle Power Switch (Key: 'P')
  const handleTogglePower = () => {
    const nextState = !laserPower;
    setLaserPower(nextState);
    const stateVal = nextState ? 1.0 : 0.0;
    sendOsc('madmapper', '/madmapper/laser/power', stateVal);
    sendOsc('ableton', '/live/master/mute', nextState ? 0 : 1);
  };

  // Button 1: Momentary Hold Strobe / Engage Button (Keys: 'E' & 'Q')
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

  // Keyboard Event Listeners for 'E', 'Q', and 'P'
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Hold Engage Keys (E / Q)
      if (e.key === 'e' || e.key === 'E' || e.key === 'q' || e.key === 'Q') {
        if (e.repeat) return;
        setPatternStrobe(true);
        sendOsc('madmapper', '/madmapper/laser/strobe', 1.0);
        sendOsc('ableton', '/live/repeat/enable', 1.0);
      }
      // Toggle Power Key (P)
      if ((e.key === 'p' || e.key === 'P') && !e.repeat) {
        handleTogglePower();
      }
    };

    const handleKeyUp = (e) => {
      if (e.key === 'e' || e.key === 'E' || e.key === 'q' || e.key === 'Q') {
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
  }, [laserPower]);

  // SLIDER 1: FREQ (Yellow Knob) -> Laser Size & Ableton Param 1
  const handleSizeChange = (val) => {
    setLaserSize(val);
    sendOsc('madmapper', '/madmapper/laser/size', val);
    sendOsc('ableton', '/live/device/param/1', val);
  };

  // SLIDER 2: LEVEL (Blue Knob) -> Laser Intensity & Ableton Param 2
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
      {/* Top Utility Bar for Kiosk fullscreen testing */}
      <div className="utility-bar">
        <button className="btn-utility" onClick={handleToggleFullscreen}>
          <Maximize2 size={13} />
          <span>FULLSCREEN</span>
        </button>
      </div>

      {/* Main Full-Screen Touch Surface Grid (Strictly 4 Core Inputs) */}
      <main className="touch-surface-grid">
        {/* COLUMN 1: 2 LINEAR SLIDERS */}
        <section className="sliders-panel">
          <div className="sliders-group">
            <TouchSlider 
              label="FREQ" 
              value={laserSize} 
              onChange={handleSizeChange} 
              colorClass="knob-freq"
            />

            <TouchSlider 
              label="LEVEL" 
              value={laserIntensity} 
              onChange={handleIntensityChange} 
              colorClass="knob-level"
            />
          </div>
        </section>

        {/* COLUMN 2: 2 TACTILE BUTTONS DIRECTLY ON SCREEN */}
        <section className="buttons-panel">
          <div className="toggles-stack">
            {/* BUTTON 1: MOMENTARY HOLD ENGAGE BUTTON (TOUCH, 'E' & 'Q' KEYS) */}
            <button 
              className={`toggle-btn ${patternStrobe ? 'on' : ''}`}
              onPointerDown={handleStrobePress}
              onPointerUp={handleStrobeRelease}
              onPointerLeave={handleStrobeRelease}
              onPointerCancel={handleStrobeRelease}
            >
              <div className={`status-led ${patternStrobe ? 'on' : 'off'}`} />
              <span className="button-text">
                {patternStrobe ? 'ENGAGED [E]' : 'HOLD ENGAGE [E]'}
              </span>
            </button>

            {/* BUTTON 2: TAP TOGGLE POWER BUTTON (KEY: 'P') */}
            <button 
              className={`toggle-btn ${laserPower ? 'on' : ''}`}
              onClick={handleTogglePower}
            >
              <div className={`status-led ${laserPower ? 'on' : 'off'}`} />
              <span className="button-text">POWER [P]</span>
            </button>
          </div>
        </section>
      </main>

      {/* TEMPORARY DISPATCH LOG (OSC Telemetry) */}
      <div className="dev-log-container">
        <div style={{ fontSize: '0.68rem', color: '#555', marginBottom: '2px' }}>
          OSC DUAL-DISPATCH TELEMETRY (MADMAPPER:8000 + ABLETON:11000)
        </div>
        {logs.length === 0 ? (
          <div className="dev-log-entry" style={{ color: '#777' }}>Touch controls to test dual OSC packet flow...</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="dev-log-entry">
              [{log.time}] &gt; <strong>[{log.target.toUpperCase()}]</strong> {log.address} {JSON.stringify(log.args)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

