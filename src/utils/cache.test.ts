import { describe, it, expect, beforeEach } from 'vitest';
import { LRUCache } from './cache.js';

describe('LRUCache', () => {
  let cache: LRUCache<string, number>;

  beforeEach(() => {
    cache = new LRUCache<string, number>(3);
  });

  describe('constructor', () => {
    it('initialises with size 0', () => {
      expect(cache.size).toBe(0);
    });

    it('throws RangeError for capacity < 1', () => {
      expect(() => new LRUCache(0)).toThrow(RangeError);
      expect(() => new LRUCache(-1)).toThrow(RangeError);
    });
  });

  describe('set / get', () => {
    it('stores and retrieves values', () => {
      cache.set('a', 1);
      expect(cache.get('a')).toBe(1);
    });

    it('returns undefined for missing keys', () => {
      expect(cache.get('missing')).toBeUndefined();
    });

    it('updates an existing key in-place', () => {
      cache.set('a', 1);
      cache.set('a', 42);
      expect(cache.get('a')).toBe(42);
      expect(cache.size).toBe(1);
    });

    it('evicts the least-recently-used entry when at capacity', () => {
      cache.set('a', 1);
      cache.set('b', 2);
      cache.set('c', 3);
      // 'a' is LRU — adding 'd' should evict 'a'
      cache.set('d', 4);
      expect(cache.get('a')).toBeUndefined();
      expect(cache.get('b')).toBe(2);
      expect(cache.get('c')).toBe(3);
      expect(cache.get('d')).toBe(4);
    });

    it('promotes a read entry above the LRU candidate', () => {
      cache.set('a', 1);
      cache.set('b', 2);
      cache.set('c', 3);
      // Read 'a' — now 'b' becomes LRU
      cache.get('a');
      cache.set('d', 4);
      expect(cache.get('b')).toBeUndefined();
      expect(cache.get('a')).toBe(1);
    });

    it('set returns `this` for chaining', () => {
      const result = cache.set('a', 1).set('b', 2);
      expect(result).toBe(cache);
      expect(cache.size).toBe(2);
    });
  });

  describe('has', () => {
    it('returns true for existing keys', () => {
      cache.set('a', 1);
      expect(cache.has('a')).toBe(true);
    });

    it('returns false for missing keys', () => {
      expect(cache.has('missing')).toBe(false);
    });

    it('does not change recency', () => {
      cache.set('a', 1);
      cache.set('b', 2);
      cache.set('c', 3);
      // 'a' is LRU; has() should not promote it
      cache.has('a');
      cache.set('d', 4);
      expect(cache.get('a')).toBeUndefined();
    });
  });

  describe('peek', () => {
    it('returns the value without updating recency', () => {
      cache.set('a', 1);
      cache.set('b', 2);
      cache.set('c', 3);
      cache.peek('a');
      cache.set('d', 4);
      // 'a' should have been evicted because peek did not promote it
      expect(cache.get('a')).toBeUndefined();
    });

    it('returns undefined for missing keys', () => {
      expect(cache.peek('x')).toBeUndefined();
    });
  });

  describe('delete', () => {
    it('removes an existing key', () => {
      cache.set('a', 1);
      expect(cache.delete('a')).toBe(true);
      expect(cache.get('a')).toBeUndefined();
      expect(cache.size).toBe(0);
    });

    it('returns false for non-existent keys', () => {
      expect(cache.delete('missing')).toBe(false);
    });
  });

  describe('clear', () => {
    it('removes all entries', () => {
      cache.set('a', 1).set('b', 2).set('c', 3);
      cache.clear();
      expect(cache.size).toBe(0);
      expect(cache.get('a')).toBeUndefined();
    });
  });

  describe('size', () => {
    it('tracks current entry count', () => {
      expect(cache.size).toBe(0);
      cache.set('a', 1);
      expect(cache.size).toBe(1);
      cache.set('b', 2);
      expect(cache.size).toBe(2);
      cache.delete('a');
      expect(cache.size).toBe(1);
    });

    it('does not exceed capacity', () => {
      for (let i = 0; i < 100; i++) {
        cache.set(String(i), i);
      }
      expect(cache.size).toBe(3);
    });
  });

  describe('capacity-1 edge case', () => {
    it('evicts the previous entry on every set when capacity is 1', () => {
      const tiny = new LRUCache<string, number>(1);
      tiny.set('a', 1);
      tiny.set('b', 2);
      expect(tiny.get('a')).toBeUndefined();
      expect(tiny.get('b')).toBe(2);
    });
  });
});
