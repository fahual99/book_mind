/**
 * GraphQL mutation strings.
 */

export const TOGGLE_FAVORITE = `
  mutation ToggleFavorite($username: String!, $bookId: Int!) {
    toggleFavorite(username: $username, bookId: $bookId)
  }
`;
