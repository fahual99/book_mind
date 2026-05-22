/**
 * GraphQL query strings for the Book Recommendation API.
 */

export const GET_BOOKS = `
  query GetBooks(
    $page: Int = 1
    $perPage: Int = 20
    $genre: String
    $search: String
    $sortBy: String = "title"
    $sortOrder: String = "asc"
  ) {
    books(
      page: $page
      perPage: $perPage
      genre: $genre
      search: $search
      sortBy: $sortBy
      sortOrder: $sortOrder
    ) {
      books {
        bookId
        title
        authors
        averageRating
        genres
        imageUrl
        smallImageUrl
        originalPublicationYear
        pages
        ratingsCount
        languageCode
      }
      total
      page
      perPage
      totalPages
    }
  }
`;

export const GET_RECOMMENDATIONS = `
  query GetRecommendations($bookId: Int!, $n: Int = 8, $method: String = "hybrid") {
    recommend(bookId: $bookId, n: $n, method: $method) {
      queryBook {
        bookId
        title
        authors
        averageRating
        genres
        description
        imageUrl
        originalPublicationYear
        pages
        ratingsCount
      }
      recommendations {
        book {
          bookId
          title
          authors
          averageRating
          genres
          imageUrl
          originalPublicationYear
          pages
          ratingsCount
        }
        similarity
        method
      }
      method
    }
  }
`;

export const GET_HOMEPAGE_BOOKS = `
  query GetHomepageBooks {
    homepageBooks {
      bookId
      title
      authors
      averageRating
      genres
      imageUrl
      smallImageUrl
      ratingsCount
    }
  }
`;

export const GET_TRENDING_BOOKS = `
  query GetTrendingBooks {
    trendingBooks {
      bookId
      title
      authors
      averageRating
      genres
      imageUrl
      smallImageUrl
      ratingsCount
    }
  }
`;

export const GET_GENRE_BOOKS = `
  query GetGenreBooks($genre: String!, $limit: Int = 20) {
    genreBooks(genre: $genre, limit: $limit) {
      bookId
      title
      authors
      averageRating
      genres
      imageUrl
      smallImageUrl
      ratingsCount
    }
  }
`;

export const GET_GENRES = `
  query GetGenres {
    genres {
      genre
      count
    }
  }
`;

export const GET_STATS = `
  query GetStats {
    stats {
      totalBooks
      totalAuthors
      totalGenres
      avgRating
      genreDistribution {
        genre
        count
      }
    }
  }
`;

export const GET_USER_FAVORITES = `
  query GetUserFavorites($username: String!) {
    userFavorites(username: $username) {
      bookId
      title
      authors
      averageRating
      genres
      imageUrl
      smallImageUrl
      ratingsCount
      originalPublicationYear
    }
  }
`;

export const GET_USER_RECOMMENDATIONS = `
  query GetUserRecommendations($username: String!, $n: Int = 12, $method: String = "hybrid") {
    userRecommendations(username: $username, n: $n, method: $method) {
      selectedBooks {
        bookId
        title
        authors
        averageRating
        genres
        imageUrl
      }
      recommendations {
        book {
          bookId
          title
          authors
          averageRating
          genres
          imageUrl
          ratingsCount
          originalPublicationYear
        }
        similarity
        method
      }
      profileSummary {
        totalBooks
        topGenres
        avgRating
        avgPages
      }
      method
    }
  }
`;

export const GET_USER_PROFILE = `
  query GetUserProfile($username: String!) {
    userProfile(username: $username) {
      id
      username
      createdAt
      favoritesCount
    }
  }
`;

export const SEARCH_BOOKS = `
  query SearchBooks($query: String!, $n: Int = 20) {
    searchBooks(query: $query, n: $n) {
      bookId
      title
      authors
      averageRating
      genres
      imageUrl
      smallImageUrl
      ratingsCount
      originalPublicationYear
    }
  }
`;
