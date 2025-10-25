// Jest setup for RiskCopilot and other component tests
import '@testing-library/jest-dom';

// Mock EventSource if not available
if (typeof global.EventSource === 'undefined') {
  global.EventSource = class MockEventSource {
    constructor(url) {
      this.url = url;
      this.readyState = 0;
      this.listeners = {};
      setTimeout(() => {
        this.readyState = 1;
        if (this.onopen) this.onopen({});
      }, 0);
    }

    addEventListener(event, handler) {
      if (!this.listeners[event]) this.listeners[event] = [];
      this.listeners[event].push(handler);
    }

    removeEventListener(event, handler) {
      if (this.listeners[event]) {
        this.listeners[event] = this.listeners[event].filter((h) => h !== handler);
      }
    }

    close() {
      this.readyState = 2;
    }

    _emit(event, data) {
      if (this.listeners[event]) {
        this.listeners[event].forEach((handler) =>
          handler({ data: JSON.stringify(data) })
        );
      }
    }
  };
}

// Mock window.matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Suppress console errors in tests (optional)
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
};
