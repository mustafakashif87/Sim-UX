/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the SimUX API, e.g. https://simux-api.example.com */
  readonly VITE_SIMUX_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
