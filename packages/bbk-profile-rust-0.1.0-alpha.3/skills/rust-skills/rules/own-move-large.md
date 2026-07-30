# own-move-large

> Treat large inline values and indirection as measured representation trade-offs

## Why It Matters

A Rust move is a semantic ownership transfer. The generated machine code may copy bytes, keep the value in place, pass it indirectly, or elide the move entirely. Large inline values can increase stack use or copy cost in some paths, while boxing adds allocation, pointer indirection, and different cache behavior. Choose representation from measured workload, layout, recursion depth, stack constraints, and ownership—not a universal byte threshold.

## Bad

```rust
// Large inline struct; generated move behavior depends on optimization and use
struct GameState {
    board: [[Cell; 100]; 100],  // 10,000 cells
    history: [Move; 1000],       // 1,000 moves
    players: [Player; 4],        // Player data
    // Total: potentially tens of KB
}

fn process_state(state: GameState) -> GameState {
    // A large value may be copied or passed indirectly depending on optimization.
    let mut new_state = state;
    new_state.apply_rules();
    new_state  // Measure the optimized path; do not assume a copy
}

let state = GameState::new();
let state = process_state(state);
```

## Good

```rust
// Indirection can reduce inline size, but adds allocation and pointer chasing
struct GameState {
    board: Box<[[Cell; 100]; 100]>,  // Pointer to heap
    history: Vec<Move>,               // Already heap-allocated
    players: [Player; 4],
}

fn process_state(mut state: GameState) -> GameState {
    // Moving mostly handles and small inline data
    state.apply_rules();
    state  // Cheap move
}

// Or use Box at call site for one-off cases
fn process_large(state: Box<LargeStruct>) -> Box<LargeStruct> {
    // Small handle transfer; allocation and indirection remain trade-offs
    state
}
```

## When to Consider Indirection

Consider `Box`, `Arc`, an arena, or borrowing only when evidence shows one of these concerns:

- the type causes problematic stack growth or recursion depth;
- repeated materialization or copying remains after optimization;
- a large enum variant inflates every value;
- stable address or recursive type structure requires indirection;
- ownership must cross an interface that benefits from an opaque handle.

Before changing representation, measure `size_of`, allocation count, cache behavior, stack use, and the actual optimized call path. Keep inline storage when locality and allocation avoidance are more valuable.

## Stack vs Heap Tradeoffs

```rust
// Inline storage: no heap allocation, but stack/layout and move behavior matter
struct StackHeavy {
    data: [u8; 4096],  // 4KB on stack
}

// Boxed storage: allocation and indirection, with a small inline handle
struct HeapLight {
    data: Box<[u8; 4096]>,  // 8 bytes on stack, 4KB on heap
}

// Measure with size_of
use std::mem::size_of;
assert_eq!(size_of::<StackHeavy>(), 4096);
assert_eq!(size_of::<HeapLight>(), 8);
```

## Alternative: References

When you don't need ownership transfer, use references:

```rust
// Best: no move at all
fn analyze_state(state: &GameState) -> Analysis {
    // Borrows state, no copying
    compute_analysis(state)
}

// Mutable borrow for in-place modification
fn update_state(state: &mut GameState) {
    state.tick();
}
```

## Pattern: Builder Returns Boxed

```rust
impl LargeConfig {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

impl ConfigBuilder {
    // Return boxed only when the API and measured representation justify indirection
    pub fn build(self) -> Box<LargeConfig> {
        Box::new(LargeConfig {
            // ... fields from builder
        })
    }
}
```

## Profile First

Don't prematurely optimize. Use tools to identify if moves are actually a bottleneck:

```rust
// Check type sizes
println!("Size of GameState: {}", std::mem::size_of::<GameState>());

// Profile with cargo flamegraph or perf to find hot memcpys
```

## See Also

- [own-copy-small](./own-copy-small.md) - Cheap types should be Copy
- [mem-box-large-variant](./mem-box-large-variant.md) - Boxing enum variants
- [perf-profile-first](./perf-profile-first.md) - Measure before optimizing
