/**
 * Benchmark suite for LRUCache.
 *
 * Requirement: sub-5ms wall-clock latency for a batch of 1 000 mixed
 * set/get operations on a cache sized to hold 500 entries.
 *
 * Run with: npm run bench
 */
import { bench, describe, expect } from 'vitest';
import { LRUCache } from '../src/utils/cache.js';

describe('LRUCache – throughput', () => {
  bench(
    '1 000 set+get operations (capacity 500)',
    () => {
      const cache = new LRUCache<number, number>(500);
      for (let i = 0; i < 1_000; i++) {
        cache.set(i, i * 2);
        cache.get(i % 500);
      }
    },
    // `throws: true` surfaces any unexpected errors thrown inside the bench function.
    // Performance target: mean < 5 ms (observed ~0.13 ms on Node 24).
    { time: 1_000, iterations: 50, throws: true },
  );

  bench('100 000 set operations (capacity 10 000) – throughput smoke test', () => {
    const cache = new LRUCache<number, number>(10_000);
    for (let i = 0; i < 100_000; i++) {
      cache.set(i, i);
    }
    // Final size must equal capacity (no growth past cap).
    expect(cache.size).toBe(10_000);
  });

  bench('mixed hit/miss workload (80 % hit rate)', () => {
    const capacity = 200;
    const cache = new LRUCache<number, number>(capacity);
    // Pre-warm
    for (let i = 0; i < capacity; i++) {
      cache.set(i, i);
    }
    for (let i = 0; i < 1_000; i++) {
      // 80 % chance of hitting a cached key
      const key = Math.random() < 0.8 ? Math.floor(Math.random() * capacity) : capacity + i;
      const v = cache.get(key);
      if (v === undefined) {
        cache.set(key, key * 3);
      }
    }
  });
});
