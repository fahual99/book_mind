"use client";

import { useState, useEffect, useCallback } from "react";
import { gqlQuery } from "./graphql";

/**
 * React hook for GraphQL queries. Replaces useQuery from Apollo.
 */
export function useGraphQL<T = Record<string, unknown>>(
  query: string,
  variables?: Record<string, unknown>,
  options?: { skip?: boolean }
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!options?.skip);
  const [error, setError] = useState<Error | null>(null);

  const varKey = JSON.stringify(variables);
  const skip = options?.skip ?? false;

  useEffect(() => {
    if (skip) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    gqlQuery<T>(query, variables)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, varKey, skip]);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await gqlQuery<T>(query, variables);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, varKey]);

  return { data, loading, error, refetch };
}

/**
 * React hook for lazy GraphQL queries. Replaces useLazyQuery from Apollo.
 */
export function useLazyGraphQL<T = Record<string, unknown>>(query: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(
    async (variables?: Record<string, unknown>) => {
      setLoading(true);
      try {
        const result = await gqlQuery<T>(query, variables);
        setData(result);
        setError(null);
        return result;
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [query]
  );

  return { execute, data, loading, error };
}
