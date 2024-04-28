import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx,css,md,mdx,html,json,scss}',
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
  safelist: [... Array.from(Array(11)).map((_v, k) => k).map(v => `grid-cols-${v}`)], // https://stackoverflow.com/questions/71818458/why-wont-tailwind-find-my-dynamic-class
};

export default config;
