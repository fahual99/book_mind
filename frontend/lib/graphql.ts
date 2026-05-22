/**
 * Lightweight GraphQL client using fetch().
 * Avoids Apollo Client / React version conflicts with Turbopack.
 */

const GRAPHQL_URL = "/graphql";

export async function gqlQuery<T = Record<string, unknown>>(
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });

  if (!res.ok) {
    throw new Error(`GraphQL request failed: ${res.status}`);
  }

  const json = await res.json();

  if (json.errors) {
    console.error("GraphQL errors:", json.errors);
    throw new Error(json.errors[0]?.message || "GraphQL error");
  }

  return json.data as T;
}

export async function gqlMutate<T = Record<string, unknown>>(
  mutation: string,
  variables?: Record<string, unknown>
): Promise<T> {
  return gqlQuery<T>(mutation, variables);
}
