/**
 * High-performance Least Recently Used (LRU) cache for core task processing.
 *
 * Uses `Map` for O(1) get/set/delete operations. Map maintains insertion order,
 * so the least-recently-used entry is always the first key in the map.
 *
 * Compatible with Node 24+ iterator helpers (e.g. `Map.prototype.keys()`).
 */

export class LRUCache<K, V> {
  private readonly capacity: number;
  /** Ordered map: first entry = LRU, last entry = MRU. */
  private readonly cache: Map<K, V>;

  constructor(capacity: number) {
    if (capacity < 1) {
      throw new RangeError(`LRUCache capacity must be at least 1, got ${capacity}`);
    }
    this.capacity = capacity;
    this.cache = new Map<K, V>();
  }

  /**
   * Retrieve a value and promote it to most-recently-used.
   * Returns `undefined` if the key is not present.
   */
  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value === undefined) return undefined;
    // Re-insert to move to MRU position.
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  /**
   * Insert or update a key-value pair.
   * If the cache is at capacity, the least-recently-used entry is evicted first.
   */
  set(key: K, value: V): this {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      // Evict LRU (first entry in Map insertion order). Map.keys().next() is O(1)
      // in V8 for the first element — no linked-list traversal required.
      const lruKey = this.cache.keys().next().value as K;
      this.cache.delete(lruKey);
    }
    this.cache.set(key, value);
    return this;
  }

  /** Remove a key. Returns `true` if the key existed. */
  delete(key: K): boolean {
    return this.cache.delete(key);
  }

  /** Returns `true` if the key is present (does not update recency). */
  has(key: K): boolean {
    return this.cache.has(key);
  }

  /** Number of entries currently held in the cache. */
  get size(): number {
    return this.cache.size;
  }

  /** Remove all entries. */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Peek at the value for a key without updating recency.
   * Returns `undefined` if the key is not present.
   */
  peek(key: K): V | undefined {
    return this.cache.get(key);
  }
}
