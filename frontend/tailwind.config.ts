import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        studio: {
          bg: "#0a0a0a",
          surface: "#111111",
          border: "#222222",
          muted: "#444444",
          accent: "#c8ff00",       // electric lime — art studio feel
          "accent-dim": "#8ab800",
          text: "#f0f0f0",
          "text-muted": "#888888",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
