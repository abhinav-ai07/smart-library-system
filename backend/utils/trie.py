class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.book_data = [] # Store book dictionaries that end/pass through here if needed, but best to only store exact matching book_data at the end of word.
        
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, title, book_data):
        node = self.root
        for char in title.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.book_data.append(book_data)

    def _dfs(self, node, prefix, results, limit):
        if len(results) >= limit:
            return
        if node.is_end_of_word:
            for book in node.book_data:
                # Store full book info
                results.append(book)
                if len(results) >= limit:
                    return
        
        for char, child_node in node.children.items():
            self._dfs(child_node, prefix + char, results, limit)

    def search_prefix(self, prefix, limit=10):
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._dfs(node, prefix.lower(), results, limit)
        return results

def build_trie(books):
    trie = Trie()
    for book in books:
        trie.insert(book['title'], book)
    return trie
