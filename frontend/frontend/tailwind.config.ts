import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#F6F4EF",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#14213D",
          muted: "#4B5768",
          faint: "#7B8598",
        },
        urgent: {
          DEFAULT: "#B3261E",
          hover: "#8F1E17",
          soft: "#F6E4E2",
        },
        warn: {
          DEFAULT: "#C2410C",
          hover: "#9A3412",
          soft: "#FFEDD5",
        },
        calm: {
          DEFAULT: "#2E6E62",
          hover: "#255A50",
          soft: "#E4EEEC",
        },
        line: "#DCD6C8",
        line2: "#C7C0AF",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "10px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(20, 33, 61, 0.06), 0 1px 0 rgba(20, 33, 61, 0.04)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
