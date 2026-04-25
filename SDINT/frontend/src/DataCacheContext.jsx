import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';

/* eslint-disable react-refresh/only-export-components */

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

const DataCacheContext = createContext();

export function useDataCache() {
  return useContext(DataCacheContext);
}

export function DataCacheProvider({ children }) {
  // Centralized cache for all page data
  const [cache, setCache] = useState({});

  const refreshInBackground = useCallback(async (key, url, method, body) => {
    try {
      let res;
      if (method === 'POST') {
        res = await axios.post(url, body);
      } else {
        res = await axios.get(url);
      }
      setCache(prev => ({ ...prev, [key]: res.data }));
    } catch {
      // Silently fail on background refresh
    }
  }, []);

  // Generic fetch-with-cache: returns cached data instantly if available,
  // fetches in background to refresh, and updates cache when done.
  const fetchWithCache = useCallback(async (key, url, options = {}) => {
    const { forceRefresh = false, method = 'GET', body = null } = options;

    // If we have cached data and not forcing refresh, return it immediately
    if (cache[key] && !forceRefresh) {
      // Still refresh in background (stale-while-revalidate pattern)
      refreshInBackground(key, url, method, body);
      return cache[key];
    }

    // First fetch or forced refresh
    try {
      let res;
      if (method === 'POST') {
        res = await axios.post(url, body);
      } else {
        res = await axios.get(url);
      }
      const data = res.data;
      setCache(prev => ({ ...prev, [key]: data }));
      return data;
    } catch (e) {
      // Return cached data on error if available
      if (cache[key]) return cache[key];
      throw e;
    }
  }, [cache, refreshInBackground]);

  // Direct cache getter (for checking if data exists without fetching)
  const getCached = useCallback((key) => cache[key] || null, [cache]);

  // Direct cache setter (for manual updates)
  const setCached = useCallback((key, data) => {
    setCache(prev => ({ ...prev, [key]: data }));
  }, []);

  // Invalidate a specific key
  const invalidate = useCallback((key) => {
    setCache(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const value = { fetchWithCache, getCached, setCached, invalidate, API_BASE };

  return (
    <DataCacheContext.Provider value={value}>
      {children}
    </DataCacheContext.Provider>
  );
}
