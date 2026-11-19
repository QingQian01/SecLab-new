"use strict";Object.defineProperty(exports, "__esModule", {value: true}); function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }
var _daisyui = require('daisyui'); var _daisyui2 = _interopRequireDefault(_daisyui);
var _typography = require('@tailwindcss/typography'); var _typography2 = _interopRequireDefault(_typography);
var _aspectratio = require('@tailwindcss/aspect-ratio'); var _aspectratio2 = _interopRequireDefault(_aspectratio);



exports. default = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
      _daisyui2.default,
      _typography2.default,
      _aspectratio2.default
     
      
  ],
  daisyui: {
    themes: [
      {
        light: {
          "primary": "#2563eb",
          "primary-content": "#eff6ff",
          "secondary": "#0ea5e9",
          "secondary-content": "#f0f9ff",
          "accent": "#38bdf8",
          "accent-content": "#082f49",
          "neutral": "#1e293b",
          "neutral-content": "#f8fafc",
          "base-100": "#ffffff",
          "base-200": "#f8fafc",
          "base-300": "#e2e8f0",
          "base-content": "#0f172a",
          "info": "#2563eb",
          "info-content": "#eff6ff",
          "success": "#059669",
          "success-content": "#ecfdf5",
          "warning": "#d97706",
          "warning-content": "#fffbeb",
          "error": "#dc2626",
          "error-content": "#fef2f2",
        },
      },
      'night',
    ]
  }
} 

 /* v7-1497abf82f060371 */