def filter_and_sort_words(words: set, min_len: int, max_len: int) -> list[str]:
    """
    Deduplicates, filters by length, and sorts the words alphabetically.
    """
    filtered = {
        word for word in words 
        if min_len <= len(word) <= max_len
    }
    return sorted(list(filtered))
