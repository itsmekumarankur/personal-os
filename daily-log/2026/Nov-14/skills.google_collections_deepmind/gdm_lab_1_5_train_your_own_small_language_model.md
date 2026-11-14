# Train Your Own Small Language Model: Easy Notes

Source: GDM Lab 1.5, training a transformer on the "Africa Galore" dataset.
Audience: AI architects who want the crux fast.

---

## 1. The One-Line Idea

> A language model looks at the words so far and guesses the next word.
> Training = show it many examples where the answer is known, and nudge its
> weights each time it guesses wrong.

```
   "Abeni, a bright-eyed"  ──►  [ MODEL ]  ──►  "girl"  (probability 0.31)
                                                "boy"   (probability 0.12)
                                                "child" (probability 0.09)
                                                 ...every word in vocab
```

---

## 2. What You Build In This Lab

- Model size: about 3.5 million parameters (Gemma-1B is about 300x bigger).
- Data: short paragraphs, one paragraph = one training example.
- Recipe: same as a giant LLM, only smaller. The lesson is the **pipeline**
  and the **training loop**, not the transformer internals (they are hidden
  inside `training.create_model()`).

---

## 3. The Whole Pipeline At A Glance

```
 ┌──────────┐   ┌─────────┐   ┌──────────┐   ┌───────────────┐
 │ Raw text │──►│ Tokens  │──►│ Token IDs│──►│ Pad/Truncate  │
 └──────────┘   └─────────┘   └──────────┘   └───────┬───────┘
                                                     │
 ┌──────────┐   ┌─────────┐   ┌──────────┐   ┌───────▼───────┐
 │  Prompt  │◄──│  Train  │◄──│  Batch   │◄──│ Input/Target  │
 │  model   │   │ (fit)   │   │ +Shuffle │   │ shift by one  │
 └──────────┘   └─────────┘   └──────────┘   └───────────────┘
```

Remember it as: **Text → Numbers → Same-size matrix → (Question, Answer)
pairs → Shuffled batches → Train → Test.**

---

## 4. Step By Step

### Step 1: Load the data

```
 africa_galore.json ──► pandas ──► array of paragraphs
                                   [ "Abeni, a bright-eyed girl...",
                                     "Jollof rice is ...",
                                     ... ]
```

Each paragraph is one example.

### Step 2: Tokenize, then convert to IDs

`SimpleWordTokenizer` splits on spaces and builds a vocabulary (a dictionary
of word → number). Two special tokens are added:

```
 Vocabulary (sorted)
 ┌─────┬────────┬─────────┬───────┬────────┬───────┐
 │ 0   │ 1      │ 2       │ 3     │  ...   │ last  │
 │PAD  │ Abeni, │ a       │ bright│        │ UNK   │
 └─────┴────────┴─────────┴───────┴────────┴───────┘
   ▲                                            ▲
   filler for equal length               "word never seen before"
```

```
 "Abeni, a bright-eyed girl"
        │ split on spaces
        ▼
 ["Abeni,", "a", "bright-eyed", "girl"]
        │ look up each in vocabulary
        ▼
 [ 1,  2,  57,  203 ]        ◄── models only understand numbers
```

### Step 3: Pad and truncate (make every row the same length)

GPUs work on matrices, and a matrix needs equal-width rows. Paragraphs have
different lengths, so we fix that.

```
 Before                              After  (max_length = 6)
 para A: [5, 8, 2]                   [5, 8, 2, 0, 0, 0]   ◄ padded with PAD(0)
 para B: [7, 1, 9, 4, 6, 3, 2, 8]    [7, 1, 9, 4, 6, 3]   ◄ truncated (cut)
 para C: [4, 4, 4, 4, 4, 4]          [4, 4, 4, 4, 4, 4]   ◄ already right
```

Choosing `max_length`:

```
 too small  ──► you throw away information (truncation)
 too big    ──► you waste compute on useless PAD tokens
 sweet spot ──► near the longest paragraph (or a high percentile)
```

**Coding Activity 1 (find the shortest and longest paragraph):**

```python
longest_paragraph_length  = len(max(encoded_tokens, key=len))
shortest_paragraph_length = len(min(encoded_tokens, key=len))
```

### Step 4: Input and target, shifted by one (THE core idea)

```
 Full sequence :  Table   Mountain   is    beautiful
                    │        │        │        │
 Input  (drop last):  Table   Mountain   is
 Target (drop first):         Mountain   is    beautiful

 Position:             1         2        3
 Model sees:         "Table"   "Table    "Table Mountain
                               Mountain"   is"
 Must predict:       "Mountain"  "is"     "beautiful"
```

In code:

```python
input_sequences  = padded_sequences[:, :-1]   # everything except last token
target_sequences = padded_sequences[:, 1:]    # everything except first token
```

Why this is powerful:

```
 One paragraph of 300 tokens  ──►  299 training questions at once
 No human labels needed       ──►  the text labels itself
                                   (this is "self-supervised learning")
```

After shifting, both arrays are 1 shorter, so reset:

```python
max_length = input_sequences.shape[1]   # the model must know the TRUE length
```

### Step 5: Shuffle and batch

```
 Original order (grouped by topic)       After shuffle (mixed topics)
 [food][food][food][music][music]  ──►   [music][food][music][food][food]
                                                │
                                                ▼ batch_size = 3
                                       ┌──────────────┐ ┌─────────┐
                                       │ batch 1 (3)  │ │ batch 2 │
                                       └──────────────┘ └─────────┘
```

- **Shuffle**: if a batch is all "food", the weights swing towards food, then
  swing back. This gives unstable learning. Shuffle whole paragraphs only.
  Word order inside a paragraph must stay intact.
- **Batch** (32 here): the model reads 32 paragraphs, averages the error, and
  updates the weights once.

```
 batch size ↑ :  faster, smoother learning, but MORE memory (OOM errors)
 batch size ↓ :  less memory, noisier, slower
```

### Step 6: Build the model

```python
model = training.create_model(
    max_length=max_length,                    # longest context it can read
    vocabulary_size=tokenizer.vocabulary_size,# size of output layer
    learning_rate=1e-4,                       # step size for weight updates
)
```

```
 token IDs ─► [ Transformer (hidden in library) ] ─► scores for EVERY word
 (batch,len)                                         (batch, len, vocab_size)
```

Learning rate in plain words:

```
 too high ──► overshoots, unstable
 too low  ──► very slow
 1e-4     ──► safe default for this lab
```

### Step 7: Train

```python
history = model.fit(x=batches, epochs=200, callbacks=[text_gen_callback])
```

```
 ┌───────────────── ONE EPOCH = one pass over all batches ───────────────┐
 │  batch 1 ─► guess ─► measure error (loss) ─► update weights  (step)   │
 │  batch 2 ─► guess ─► measure error (loss) ─► update weights  (step)   │
 │  ...                                                                  │
 └───────────────────────────────────────────────────────────────────────┘
          repeat for 200 epochs
```

Vocabulary:

| Term | Meaning |
|---|---|
| Step | one batch processed and one weight update |
| Epoch | one full pass over the dataset |
| Loss | how wrong the guesses are (should trend DOWN) |
| Parameters | the model's learned numbers (about 3.5M here) |
| Callback | a hook that prints sample text every 10 epochs |

What you will see:

```
 epoch  10:  "Abeni, the the and of market"      ◄ random words
 epoch  50:  "Abeni, a bright-eyed girl who"     ◄ getting grammatical
 epoch 200:  "Abeni, a bright-eyed girl from ..."◄ coherent-ish
```

Loss curve (small bumps are normal, the trend matters):

```
 loss
  │\
  │ \__
  │    \_    /\
  │      \__/  \___
  │               \______
  └──────────────────────── epochs
```

### Step 8: Evaluate by prompting

Three questions to ask:

```
 A. Does it predict the next token from patterns in training data?
    ──► prompt: "Abeni, a bright-eyed"   (text taken from the dataset)

 B. Is the generated text coherent?
    ──► prompt: "Jide was hungry so she went looking for"

 C. Does a small context change shift the prediction sensibly?
    ──► "hungry ... looking for"  vs  "thirsty ... looking for"
        (expect food-ish words vs drink-ish words)
```

Two ways to pick the next word:

```
 Model output probabilities:   jollof 0.40 | water 0.25 | home 0.20 | ...

 GREEDY  : always pick the top one  ──► "jollof"
           deterministic, safe, but repetitive

 RANDOM  : roll a weighted die      ──► "jollof" 40%, "water" 25%, ...
           varied and creative, but sometimes wrong
```

Real LLM knobs (temperature, top-k, top-p) are the same trade-off.

Unseen words:

```
 "Jide drinks kombucha"  ──►  ["Jide", "drinks", <UNK>]
                                                  ▲
                              word not in vocab, ALL its information is lost
```

---

## 5. Why This Matters

```
 ┌──────────────────────────────────────────────────────────────┐
 │ 1. Every LLM follows this same recipe. Only these differ:    │
 │      tokenizer (subword, not word), data size, model size,   │
 │      hardware.                                               │
 │ 2. Data prep decides quality. Padding/shift/shuffle bugs     │
 │    silently ruin training, with no crash.                    │
 │ 3. A small model is the right place to learn and break things│
 │ 4. It sets up evaluation, scaling, fine-tuning and cost.     │
 └──────────────────────────────────────────────────────────────┘
```

---

## 6. Architect-Level Observations (beyond the lab)

```
 ┌────────────────────┬───────────────────────────────────────────────┐
 │ Topic              │ Point                                         │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ Word tokenizer     │ Large vocab and <UNK> loses info. Production  │
 │                    │ uses subword (BPE / SentencePiece).           │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ PAD in the loss    │ If PAD counts in the loss, the model wastes   │
 │                    │ effort predicting padding. Good setups mask   │
 │                    │ it. The lab does not show it, so check inside │
 │                    │ the library.                                  │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ No validation set  │ 200 epochs on tiny data = memorization. Real  │
 │                    │ work holds out 5-10% and tracks val-loss.     │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ Causal mask        │ Position t must not see tokens after t. That  │
 │                    │ makes the shift-by-one trick valid. Without   │
 │                    │ it the model could cheat by reading the       │
 │                    │ answer.                                       │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ Context limit      │ Model only knows max_length positions. That   │
 │                    │ is the "context window" of real LLMs.         │
 ├────────────────────┼───────────────────────────────────────────────┤
 │ Cost levers        │ Padding waste, batch size (memory vs speed),  │
 │                    │ epochs (quality vs time vs overfitting).      │
 └────────────────────┴───────────────────────────────────────────────┘
```

Why the model can predict at every position at once (causal mask):

```
 Position 1 sees:  [T]
 Position 2 sees:  [T  M]
 Position 3 sees:  [T  M  i]       ◄ nobody sees the future
 (lower-triangle attention)
```

---

## 7. Take-Home Summary

```
 TEXT ──► NUMBERS ──► SAME-SIZE MATRIX ──► (INPUT, SHIFTED TARGET)
                                                    │
                                                    ▼
           guess next token ─► measure error ─► adjust weights
                          (repeat over shuffled batches)
```

- Quality = data + tokenizer + model size + training length.
- Here all four are small, so the output is grammatical but not always
  meaningful. That is expected, not a bug.

---

## 8. Quick Cheat Sheet

| Concept | One-liner |
|---|---|
| Token | a chunk of text (here, a word) |
| Vocabulary | dictionary: token ↔ ID |
| `<PAD>` | filler to equalize lengths |
| `<UNK>` | stand-in for unseen words |
| `max_length` | target sequence length (pad up, cut down) |
| Input / Target | same sequence, target shifted left by 1 |
| Shuffle | randomize paragraph order, never the words inside |
| Batch | group of paragraphs per weight update |
| Epoch | one pass over all data |
| Loss | error score, should decrease |
| Learning rate | size of each weight update |
| Greedy vs random | top pick vs weighted sample |
| Parameters | the learned numbers, about 3.5M here |

---

## 9. Self-Check Questions

1. Why must all sequences in a batch have the same length?
2. Why is the target the input shifted left by one?
3. What goes wrong if you do not shuffle?
4. What happens if `max_length` is too small? Too large?
5. Why does a word-level tokenizer struggle with new words?
6. Why would you add a validation split in real work?
7. What does the causal mask prevent?
