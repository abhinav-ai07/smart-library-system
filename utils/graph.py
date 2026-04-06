class Graph:
    def __init__(self):
        # adjacency list: book_id -> list of similar book_ids
        # we can also map genre -> list of book_ids, then connect them
        self.adj = {}
        self.books_db = {} # book_id -> book_data

    def build_graph(self, books):
        # Reset
        self.adj = {}
        self.books_db = {}
        
        genre_map = {}
        
        for book in books:
            b_id = book['id']
            self.books_db[b_id] = book
            self.adj[b_id] = set()
            genre = book.get('genre', 'General')
            if genre not in genre_map:
                genre_map[genre] = []
            genre_map[genre].append(b_id)
            
        # Create edges to all other books in the same genre
        for genre, b_ids in genre_map.items():
            for i in range(len(b_ids)):
                for j in range(len(b_ids)):
                    if i != j:
                        self.adj[b_ids[i]].add(b_ids[j])

    def get_recommendations(self, target_book_id, limit=5):
        if target_book_id not in self.adj:
            return []
        
        similar_ids = list(self.adj[target_book_id])
        return [self.books_db[bid] for bid in similar_ids[:limit]]
    
    def get_alternative(self, target_book_id):
        ''' Find the best alternative if the target is unavailable '''
        recs = self.get_recommendations(target_book_id, limit=10)
        # return first available alternative
        for rec in recs:
            if rec.get('available', False):
                return rec
        return None
