import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { Client, Server as OscServer } from 'node-osc';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// OSC Configuration
const MADMAPPER_HOST = '127.0.0.1';
const MADMAPPER_PORT = 8000;
const ABLETON_HOST = '172.20.10.8';
const ABLETON_PORT = 11000;
const OSC_INCOMING_PORT = 9000;

// OSC Clients
let madmapperClient;
let abletonClient;
let oscIncomingServer;

try {
  madmapperClient = new Client(MADMAPPER_HOST, MADMAPPER_PORT);
  if (madmapperClient._sock) {
    madmapperClient._sock.on('error', (err) => {
      // Ignore transient network errors
    });
  }
  console.log(`[OSC] MadMapper client initialized -> ${MADMAPPER_HOST}:${MADMAPPER_PORT}`);
} catch (e) {
  console.error('[OSC Error] Could not initialize MadMapper client:', e.message);
}

try {
  abletonClient = new Client(ABLETON_HOST, ABLETON_PORT);
  if (abletonClient._sock) {
    abletonClient._sock.on('error', (err) => {
      console.warn(`[Network Notice] Could not reach Ableton at ${ABLETON_HOST}:${ABLETON_PORT} (${err.code})`);
    });
  }
  console.log(`[OSC] Ableton client initialized -> ${ABLETON_HOST}:${ABLETON_PORT}`);
} catch (e) {
  console.error('[OSC Error] Could not initialize Ableton client:', e.message);
}

// OSC Incoming Listener (e.g. from Ableton Audio Peaks or MadMapper feedback)
try {
  oscIncomingServer = new OscServer(OSC_INCOMING_PORT, '0.0.0.0', () => {
    console.log(`[OSC Inbound] Listening for incoming OSC packets on port ${OSC_INCOMING_PORT}`);
  });

  oscIncomingServer.on('message', (msg) => {
    const [address, ...args] = msg;
    io.emit('osc-received', { address, args });
  });
} catch (e) {
  console.error('[OSC Error] Failed to bind incoming OSC server:', e.message);
}

// Active UI Mappings & State
const appState = {
  bpm: 124,
  blackout: false,
  crossModulation: true,
  madmapperConnected: true,
  abletonConnected: true
};

io.on('connection', (socket) => {
  console.log(`[UI Client] Client connected: ${socket.id}`);
  socket.emit('state-sync', appState);

  // General OSC Send dispatcher from UI
  socket.on('send-osc', (data) => {
    const { target, address, args = [] } = data;
    const payload = Array.isArray(args) ? args : [args];

    if (target === 'madmapper' || target === 'both') {
      if (madmapperClient) {
        try {
          madmapperClient.send(address, ...payload);
          console.log(`[OSC -> MadMapper ${MADMAPPER_HOST}:${MADMAPPER_PORT}] ${address} ${JSON.stringify(payload)}`);
        } catch (err) {
          // Catch sync errors
        }
      }
    }

    if (target === 'ableton' || target === 'both') {
      if (abletonClient) {
        try {
          abletonClient.send(address, ...payload, (err) => {
            if (err) {
              // Catch async UDP network unreachable error without crashing
            }
          });
          console.log(`[OSC -> Ableton ${ABLETON_HOST}:${ABLETON_PORT}] ${address} ${JSON.stringify(payload)}`);
        } catch (err) {
          // Catch sync errors
        }
      }
    }

    // Echo back to all UI clients for visual sync
    io.emit('osc-dispatched', { target, address, args: payload, timestamp: Date.now() });
  });

  socket.on('disconnect', () => {
    console.log(`[UI Client] Client disconnected: ${socket.id}`);
  });
});

// Process-level unhandled UDP error guard
process.on('uncaughtException', (err) => {
  if (err.code === 'EHOSTUNREACH' || err.code === 'ENETUNREACH') {
    console.warn(`[Network Warning] Target host ${ABLETON_HOST} unreachable. Check Wi-Fi connection.`);
  } else {
    console.error('[Unhandled Error]', err);
  }
});

const PORT = 4000;
httpServer.listen(PORT, () => {
  console.log(`====================================================`);
  console.log(`🚀 CYBER-CONTROL OSC BRIDGE RUNNING ON PORT ${PORT}`);
  console.log(`📡 Sending MadMapper OSC to: ${MADMAPPER_HOST}:${MADMAPPER_PORT}`);
  console.log(`📡 Sending Ableton OSC to:   ${ABLETON_HOST}:${ABLETON_PORT}`);
  console.log(`====================================================`);
});
