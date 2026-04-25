/**
 * Shared configuration for the SDINT frontend.
 * All components should import API_BASE from here instead of hardcoding URLs.
 */
export const API_BASE = import.meta.env.VITE_API_URL 
  || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');
