# OSA Benchmark — Docstring Generation Evaluation Framework

A modular benchmarking framework for evaluating automatic docstring generation tools for Python projects.

---

## Overview

This project provides a unified pipeline to compare different approaches to docstring generation, including:

- 🧠 OSA (iterative LLM-based method)
- 🤖 RepoAgent (agent-based generation)
- ✨ Naive LLM generation (baseline)
- 📝 Original human-written docstrings (ground truth, optional)

The benchmark evaluates both:
- **Coverage** (how many methods are documented)
- **Quality** (how good the docstrings are)

---

## Motivation

Existing tools generate docstrings, but lack:

- Standardized evaluation
- Cross-tool comparison
- Quality + coverage analysis

This benchmark solves these issues with a **scalable and extensible architecture**.

---

## 🧩 Architecture

```
repos/
 ├── osa_project1/
 ├── repoagent_project1/
 ├── original_project1/
```

### Core Modules

- **Discovery** — scans and groups repositories by prefix
- **Extractor** — parses Python code (Tree-sitter)
- **Merger** — aligns methods across tools
- **Generator** — naive LLM docstring generation
- **Judge** — LLM-based evaluation
- **Metrics** — computes evaluation metrics
- **Visualizer** — aggregates results

---

## ⚙️ Pipeline

```
repos → extraction → merge → generation → evaluation → metrics → visualization
```

---

## 📊 Metrics

### 1. Coverage

```
Coverage = documented_methods / total_methods
```
![Coverage](https://latex.codecogs.com/svg.image?Coverage=\frac{N_{documented}}{N_{total}})

---

### 2. BERTScore

Semantic similarity to ground truth:

```
BERTScore = avg(similarity(predicted, reference))
```
![BERTScore](https://latex.codecogs.com/svg.image?BERTScore=\frac{1}{N}\sum_{i=1}^{N}sim(pred_i,ref_i))

---

### 3. Pairwise Comparison

```
P(A > B) = wins(A) / (wins(A) + wins(B))
```
![Pairwise](https://latex.codecogs.com/svg.image?P(A>B)=\frac{wins(A)}{wins(A)+wins(B)})
---

### 4. LLM Judge

Evaluates:

- correctness
- completeness
- clarity
- hallucination

```
Score = average(criteria)
```
![Score](https://latex.codecogs.com/svg.image?Score=\frac{1}{4}\sum_{i=1}^{4}metric_i)
---

## 🚀 Features

- ✅ Multi-tool comparison (dynamic)
- ✅ Async LLM evaluation
- ✅ Caching (LLM + Judge + Pairwise)
- ✅ Extensible metrics system
- ✅ Works without ground truth
- ✅ Scales to large repos

---

## ⚡ Async Execution

Uses `asyncio` for:

- Parallel LLM calls
- Batch processing
- Pairwise comparisons (O(n²))

---

## 💾 Caching

Avoids repeated LLM calls:

- LLM generation cache
- Judge evaluation cache
- Pairwise comparison cache

Cache keys depend on:
- method code
- docstring
- prompt

---

## 🧪 Usage

### 1. Prepare repositories

```
repos/
 ├── osa_repo1/
 ├── repoagent_repo1/
 ├── original_repo1/
```

You can omit `original_` if unavailable.

---

### 2. Run benchmark

```bash
python run_benchmark.py
```

---

### 3. Output

- JSON with metrics
- Aggregated results in terminal
- Logs in terminal

---

## Project Structure

```
benchmark/
 ├── pipeline.py
 ├── benchmark.py
 ├── extractor.py
 ├── merger.py
 ├── judge.py
 ├── llm.py
 ├── cache.py
 ├── visualizer.py
 └── metrics/
      ├── base.py
      ├── coverage.py
      ├── bert.py
      └── pairwise.py
```

---

## 🧠 Key Insights

### Coverage

- **Naive generation achieves perfect coverage (1.0)** across all evaluated repositories, as expected due to the absence of structural constraints.
- **RepoAgent also demonstrates near-complete coverage (0.996)**, indicating strong ability to insert docstrings across the codebase.
- **OSA achieves high coverage (0.95)**, slightly below RepoAgent but significantly higher than original documentation.
- **Original docstrings lag behind (0.67)**, confirming that real-world codebases are often under-documented.

Overall, automated approaches significantly outperform human-written documentation in terms of coverage.

---

### Pairwise Comparison (Quality Ranking)

#### [requests repo](https://github.com/psf/requests)

- **OSA strongly outperforms original docstrings** (~0.89 win rate)
- **OSA dominates RepoAgent** (~0.97 win rate)
- **Naive generation outperforms almost everything**:
  - vs OSA → ~0.86
  - vs RepoAgent → ~0.99
  - vs Original → 1.00

#### [mas-lab repo](https://github.com/Tendo1904/mas-lab)

- **Naive remains dominant**:
  - vs RepoAgent → ~0.96
  - vs OSA → ~0.92
- **RepoAgent outperforms OSA (~0.62)**, unlike in `requests`
- **OSA performs weakest in pairwise comparisons** on this dataset

Pairwise results reveal that:
- Rankings are **dataset-dependent**
- **Naive LLM generation consistently ranks highest**
- OSA is strong vs original, but not always vs other automated tools

---

### Semantic Similarity (BERTScore)

- **BERTScore ≈ 0.85 (requests by OSA)** indicates high semantic similarity between generated and original docstrings
- Suggests that:
  - Generated docstrings preserve core meaning
  - Differences are more structural than semantic

---

### LLM Judge Scores

| Tool        | Overall Score |
|------------|-------------|
| Naive      | **5.00**     |
| RepoAgent  | 4.98         |
| OSA        | 4.94         |
| Original   | 4.86         |

- All methods receive **very high scores (≥4.8)**
- **Naive achieves perfect score**, followed closely by RepoAgent
- Differences between methods are **minimal in absolute terms**

This suggests:
- LLM judge is **not highly discriminative at top quality levels**
- Most generated docstrings are **syntactically and stylistically strong**

---

### Score Distribution

- **Naive: 100% of samples scored 5**
- **RepoAgent: almost all 5, very few 4**
- **OSA: mostly 5, some 4 and rare 3**
- **Original: wider spread (2–5)**

Key observation:
- Automated methods produce **highly consistent outputs**
- Human-written docstrings show **greater variability in quality**

---

### Important Observations

- **Naive LLM generation performs surprisingly well**, often outperforming more complex methods
- **RepoAgent achieves strong quality but relies heavily on coverage**
- **OSA provides a balanced approach**, improving over original documentation while maintaining structure awareness
- **Original docstrings are inconsistent**, both in coverage and quality

---

### Interpretation Caveats

- LLM-based evaluation may introduce **bias toward well-formed text**
- Pairwise comparison uses **intersection of coverage**, favoring tools with lower coverage in some cases
- High scores across all methods indicate possible **ceiling effect** in evaluation

---

### Final Takeaways

- ✔ Coverage and quality must be evaluated jointly  
- ✔ Naive LLM is a **strong baseline and hard to beat**  
- ✔ OSA improves over real-world documentation significantly  
- ✔ RepoAgent is competitive but inconsistent across datasets  
- ✔ Human-written docstrings are not a reliable gold standard  

---

### Practical Insight

> In many cases, a simple LLM prompt can produce documentation that is competitive with — or even superior to — both automated pipelines and human-written docstrings.

This highlights the importance of:
- better evaluation strategies  
- more robust quality metrics  
- deeper context-aware generation methods  
---

## Limitations

- LLM judge bias toward fluent text
- Pairwise uses intersection (coverage bias)
- JSON parsing from LLM can be unstable

---

## Extending

### ➕ Add new tool

Just add a repo:

```
repos/mytool_project1/
```

---

### ➕ Add new metric

```python
class MyMetric:
    def compute(self, samples):
        return ...
```

---

## Conclusion

This benchmark provides:

- A unified evaluation framework
- Flexible architecture
- Research-grade metrics

Suitable for both:
- academic research
- practical tool comparison

---

## Author

Artem Protopopov, ITMO University, 2nd year Masters of Industrial AI, J4251