# Hospital Pharmacy Inventory System

A command-line system that benchmarks six algorithms applied to hospital pharmacy inventory management. You choose an operation and dataset size, all algorithms run simultaneously, and nanosecond-accurate timing results are shown side by side.

**Search Algorithms:**
- Linear Scan — O(n). Visits every record once. Simple baseline.
- Binary Search — O(log n) search after O(n log n) pre-sort.
- Min-Heap — O(n log n) build, O(log n) per pop. Always surfaces the most urgent medication first.

**Sorting Algorithms:**
- Bubble Sort — O(n²). Included as the worst-case baseline.
- Merge Sort — O(n log n). Stable sort, consistent on all inputs.
- Quick Sort — O(n log n) average. Fastest in practice.

Dataset: 10,000 real hospital medication records loaded from CSV.

---

## Team Members

| Name | Email |
|------|-------|
| Ergi Sula | ergi.sula@student.jjay.cuny.edu |
| Thomas Kamel | thomas.kamel@student.jjay.cuny.edu |

---

## Language & Dependencies

- **Language:** Python 3.x
- **Libraries:** `csv`, `heapq`, `time` — all Python standard library
- **No pip installs required**

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/ergisula/hospital-pharmacy-system.git
cd hospital-pharmacy-system
```

### 2. Make sure both files are in the same folder
```
pharmacy_inventory.py
hospital_pharmacy_inventory.csv
```

### 3. Run
```bash
python3 pharmacy_inventory.py
```

---

## Sample Output

### Option 1 - Reorder Check at n=10,000

```
  What would you like to do?
  [1] Check medications below reorder point
  [2] Check medications expiring soon
  [3] Run 30-day simulation
  [4] Sort medications
  [5] Exit

  Enter choice (1-5): 1

  How many medications to load?
  [1] 100   [2] 500   [3] 1,000   [4] 5,000   [5] 10,000
  Enter choice (1-5): 5

  Loading 10,000 medications...
  Running all three search algorithms...

  ── Results: Medications Below Reorder Point ──
  ─────────────────────────────────────────────────────────
  Algorithm              Time (nanoseconds)         Found
  ─────────────────────────────────────────────────────────
  Linear Scan                     2,221,850         4,377
  Binary Search                   7,213,550         4,377
  Min-Heap                        7,257,850         4,377
  ─────────────────────────────────────────────────────────
  Winner : Linear Scan  (slowest is 3.28x slower)
  ─────────────────────────────────────────────────────────

  Top 10 Most Urgent Reorders (Min-Heap order — worst first):
  Medication                           On Hand Reorder At  Shortfall
  ───────────────────────────────────────────────────────────────────
  Epinephrine 5mg/mL                       145      3,472      3,327
  Vitamin D3 40mg                           75      3,332      3,257
  Rosuvastatin 10mg/mL                      16      3,248      3,232
  Ibuprofen 500mg                           27      3,248      3,221
  Ibuprofen 80mg                           300      3,486      3,186
  Furosemide 40mg                          290      3,472      3,182
  Celecoxib 50mg                           196      3,346      3,150
  Methylprednisolone 500mg                 365      3,500      3,135
  Diazepam 80mg                            101      3,146      3,045
  Rosuvastatin 10mg/mL                      32      3,055      3,023
```

### Option 4 - Sort at n=10,000

```
  Enter choice (1-5): 4

  Sort medications by:
  [1] Expiration date   [2] Name   [3] Price (cost per unit)
  Enter choice (1-3): 1

  Loading 10,000 medications...
  Sorting by Expiration Date using all three algorithms...

  ── Sorting Results: by Expiration Date ──
  ─────────────────────────────────────────────────────────
  Algorithm              Time (nanoseconds)     Complexity
  ─────────────────────────────────────────────────────────
  Bubble Sort                 8,230,423,450         O(n^2)
  Merge Sort                     36,764,800     O(n log n)
  Quick Sort                     26,728,050     O(n log n)
  ─────────────────────────────────────────────────────────
  Winner : Quick Sort  (slowest is 307.03x slower)
  ─────────────────────────────────────────────────────────
```

### Option 3 - 30-Day Simulation at n=500

```
  ── 30-Day Simulation Results (500 medications) ──
  ─────────────────────────────────────────────────────────
  Metric                       Linear Scan        Min-Heap
  ─────────────────────────────────────────────────────────
  Shortage Events                    1,111           1,111
  Expired Waste ($)            639,077.08      639,077.08
  Total Reorder Cost ($)    45,736,058.62   45,736,058.62
  Reorder Events                     1,111           1,111
  Time (nanoseconds)            14,479,550       7,389,350
  ─────────────────────────────────────────────────────────
  Winner : Min-Heap  (1.96x faster)
  ─────────────────────────────────────────────────────────
```

---

## Key Findings

- Linear Scan won the search comparison at every input size tested, including n=10,000. The heap and binary search have larger constant factors in Python that outweigh their asymptotic advantage at this dataset size.
- Bubble Sort is 307x slower than Quick Sort at n=10,000, making the O(n²) vs O(n log n) gap clearly visible.
- Both simulation algorithms produce identical business outcomes. The Min-Heap simulation is nearly 2x faster because it updates stock directly through a dictionary reference instead of doing a second O(n) scan.

---

## File Structure

```
hospital-pharmacy-system/
├── pharmacy_inventory.py
├── hospital_pharmacy_inventory.csv
├── README.md
└── docs/
    └── CSCI377_Project_Report_ErgiSula_ThomasKamel.docx
```
