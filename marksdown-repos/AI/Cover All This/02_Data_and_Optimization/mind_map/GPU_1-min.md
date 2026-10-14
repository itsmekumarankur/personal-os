# GPU Basics — 1 min

> **Core rule:** Choose the GPU for the workload—not simply the most powerful or expensive one.

```text
                         GPU FOR LLMs
                              |
        +---------------------+----------------------+
        |                     |                      |
     1. WHY GPU          2. MEMORY                3. SPEED
        |                     |                      |
  Matrix operations       Model weights          Compute capacity
  run in parallel         KV cache               Memory bandwidth
  CPU = general logic     Activations             Interconnect
  GPU = parallel math     Runtime overhead        Precision support
        |                     |                      |
        +---------------------+----------------------+
                              |
                      4. FIT THE MODEL
                              |
                  Model size + precision
                              |
                     Add runtime overhead
                     + KV cache + batching
                              |
                     Does it fit in VRAM?
                       /             \
                     No               Yes
                     |                 |
              Quantize / smaller      Benchmark
              model / multi-GPU       real workload
                                        |
                              TTFT • tokens/sec
                              P95/P99 • cost/request

        +---------------------+----------------------+
        |                     |                      |
   5. PRECISION          6. INFERENCE             7. SCALE
        |                     |                      |
   FP32 = 32-bit          Prefill: process        Tensor parallel:
   FP16/BF16 = 16-bit     prompt                  split layer work
   INT8 = 8-bit            Decode: generate        Data parallel:
   INT4 = 4-bit            tokens one by one       replicate model
        |                     |                      |
   Lower memory,          KV cache grows with      Multi-GPU adds
   possible quality loss  context + concurrency    communication cost
```

## Fast memory calculation

For a **7B-parameter model**, approximate weight storage only:

| Precision | Weight memory |
|---|---:|
| FP32 | ~28 GB |
| FP16/BF16 | ~14 GB |
| INT8 | ~7 GB |
| INT4 | ~3.5 GB |

These figures exclude KV cache, activations, runtime overhead, and other allocations.

## Must-know

- **GPU memory capacity:** Can the model and active requests fit?
- **TTFT:** Time to first token.
- **TPOT:** Time per output token.
- **KV cache:** Reuses attention keys/values, but consumes memory per request.
- **Quantization:** Reduces numerical precision and memory; validate quality after quantizing.


> **Leadership question:** “What workload are we sizing for, and what GPU capacity does it actually require?”
