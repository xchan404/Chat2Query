import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#F8F5EE",
        surface: "#EDE7DC",
        "surface-alt": "#E2DAD0",
        "ink-dark": "#0F1419",
        "ink-muted": "#4F5863",
        "yellow-signal": "#FFD600",
        "yellow-bg": "#FFFBE6",
        "cobalt-signal": "#0047AB",
        "cobalt-bg": "#EFF5FF",
        "purple-signal": "#7C3AED",
        "purple-bg": "#F5F3FF",
        "cyan-signal": "#0284C7",
        "cyan-bg": "#F0F9FF",
        "rust-warn": "#DC2626",
        "rust-bg": "#FEF2F2",
        "emerald-pass": "#16A34A",
        "emerald-bg": "#F0FDF4",
        "code-bg": "#0F172A",
        "code-fg": "#F8FAFC",
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Public Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        hard: "4px 4px 0px #0F1419",
        sm: "2px 2px 0px #0F1419",
        yellow: "4px 4px 0px #FFD600",
        cobalt: "4px 4px 0px #0047AB",
        purple: "4px 4px 0px #7C3AED",
      },
      borderWidth: {
        DEFAULT: "2px",
        thin: "1px",
        med: "2px",
        thick: "3px",
      },
    },
  },
  plugins: [],
};

export default config;
