#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Hospital Pharmacy Inventory Optimization and Shortage Prevention System
Team: Ergi Sula & Thomas Kamel
Search Algorithms:
  1. Linear Scan — O(n)
  2. Binary Search  — O(log n)  [requires pre-sorted list]
  3. Min-Heap  — O(n log n) build, O(log n) per pop

Sorting Algorithms:
  1. Bubble Sort — O(n^2)
  2. Merge Sort — O(n log n)
  3. Quick Sort  — O(n log n) average, O(n^2) worst
"""

import csv
import heapq
import time

DATA_FILE = "hospital_pharmacy_inventory.csv"


# DATA LOADING 

def load_medications(filepath, limit=None):
    medications = []
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            medications.append({
                'drug_id': row['drug_id'],
                'drug_name': row['drug_name'],
                'category': row['category'],
                'quantity': int(row['quantity']),
                'daily_usage': int(row['daily_usage']),
                'reorder_point': int(row['reorder_point']),
                'reorder_qty': int(row['reorder_quantity']),
                'cost_per_unit': float(row['cost_per_unit']),
                'expiration_date': row['expiration_date'],
                'days_until_expiry': int(row['days_until_expiry']),
                'expired': row['expired'] == 'True',
            })

    return medications


#  SEARCH ALGORITHM 1 — LINEAR SCAN O(n) 

def linear_scan_reorder(medications):
    result = []
    for med in medications:
        if not med['expired'] and med['quantity'] < med['reorder_point']:
            shortfall = med['reorder_point'] - med['quantity']
            result.append((med['drug_name'], med['quantity'],
                           med['reorder_point'], shortfall))

    return result


def linear_scan_expiry(medications, threshold=60):
    result = []
    for med in medications:
        if not med['expired'] and 0 <= med['days_until_expiry'] <= threshold:
            result.append((med['days_until_expiry'], med['drug_name'],
                           med['quantity'], med['expiration_date']))
    result.sort()

    return result


def linear_scan_simulate(medications, days=30):
    meds = [m.copy() for m in medications]
    shortages = 0
    expired_waste = 0.0
    reorder_cost = 0.0
    reorder_events = 0
    # we copy the list so the simulation doesn't modify the original data
    # and set up counters to track all the outcomes we want to measure

    for _ in range(days):
        for med in meds:
            if not med['expired']:
                med['quantity'] = max(0, med['quantity'] - med['daily_usage'])
            med['days_until_expiry'] -= 1
            if med['days_until_expiry'] < 0 and not med['expired']:
                med['expired'] = True
                expired_waste += med['quantity'] * med['cost_per_unit']
        

        reorder_list = linear_scan_reorder(meds)
        for drug_name, _, _, _ in reorder_list:
            shortages += 1
            for med in meds:
                if med['drug_name'] == drug_name:
                    med['quantity'] += med['reorder_qty']
                    reorder_cost += med['reorder_qty'] * med['cost_per_unit']
                    reorder_events += 1
                    break


    return shortages, round(expired_waste, 2), round(reorder_cost, 2), reorder_events


# SEARCH ALGORITHM 2 — BINARY SEARCH O(log n) 

def binary_search_reorder(medications):
    sorted_meds = sorted(
        [m for m in medications if not m['expired']],
        key=lambda m: m['quantity'] - m['reorder_point']
    )
    

    lo, hi = 0, len(sorted_meds)
    while lo < hi:
        mid = (lo + hi) // 2
        score = sorted_meds[mid]['quantity'] - sorted_meds[mid]['reorder_point']
        if score < 0:
            lo = mid + 1
        else:
            hi = mid


    result = []
    for med in sorted_meds[:lo]:
        shortfall = med['reorder_point'] - med['quantity']
        result.append((med['drug_name'], med['quantity'],
                       med['reorder_point'], shortfall))
    # collect all medications to the left of the boundary these are all below reorder point
    return result


def binary_search_expiry(medications, threshold=60):
    valid = [m for m in medications
             if not m['expired'] and m['days_until_expiry'] >= 0]
    sorted_meds = sorted(valid, key=lambda m: m['days_until_expiry'])
    # filter out already-expired medications and sort the rest by days until expiry ascending

    lo, hi = 0, len(sorted_meds)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_meds[mid]['days_until_expiry'] <= threshold:
            lo = mid + 1
        else:
            hi = mid


    result = []
    for med in sorted_meds[:lo]:
        result.append((med['days_until_expiry'], med['drug_name'],
                       med['quantity'], med['expiration_date']))
    # everything to the left of lo expires within the threshold collect and return them
    return result


# SEARCH ALGORITHM 3 — MIN-HEAP O(n log n) 

def heap_reorder(medications):
    heap = []
    for med in medications:
        if not med['expired']:
            priority = med['quantity'] - med['reorder_point']
            heapq.heappush(heap, (priority, med['drug_name'],
                                  med['quantity'], med['reorder_point']))


    result = []
    while heap:
        priority, name, qty, reorder_pt = heapq.heappop(heap)
        if priority >= 0:
            break
        result.append((name, qty, reorder_pt, abs(priority)))

    return result


def heap_expiry(medications, threshold=60):
    heap = []
    for med in medications:
        if not med['expired'] and 0 <= med['days_until_expiry'] <= threshold:
            heapq.heappush(heap, (med['days_until_expiry'], med['drug_name'],
                                  med['quantity'], med['expiration_date']))


    result = []
    while heap:
        result.append(heapq.heappop(heap))
    # pop everything off in order — since it's a min-heap, soonest expiring comes out first
    return result


def heap_simulate(medications, days=30):
    meds = [m.copy() for m in medications]
    shortages = 0
    expired_waste = 0.0
    reorder_cost = 0.0
    reorder_events = 0
    # same setup as linear simulation — copy the list and initialize counters

    for _ in range(days):
        for med in meds:
            if not med['expired']:
                med['quantity'] = max(0, med['quantity'] - med['daily_usage'])
            med['days_until_expiry'] -= 1
            if med['days_until_expiry'] < 0 and not med['expired']:
                med['expired'] = True
                expired_waste += med['quantity'] * med['cost_per_unit']
        # same daily consumption and expiry logic as the linear simulation

        heap = []
        for med in meds:
            if not med['expired']:
                priority = med['quantity'] - med['reorder_point']
                heapq.heappush(heap, (priority, med['drug_id'], med))


        while heap:
            priority, drug_id, med = heapq.heappop(heap)
            if priority >= 0:
                break
            shortages += 1
            med['quantity'] += med['reorder_qty']
            reorder_cost += med['reorder_qty'] * med['cost_per_unit']
            reorder_events += 1


    return shortages, round(expired_waste, 2), round(reorder_cost, 2), reorder_events


#  SORTING ALGORITHM 1 — BUBBLE SORT O(n^2) watch this https://www.youtube.com/watch?v=KLvH6yi5YYU

def bubble_sort(medications, key):
    arr = [m.copy() for m in medications]
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j][key] > arr[j + 1][key]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break

    return arr


#  SORTING ALGORITHM 2 — MERGE SORT O(n log n) also watch this  https://www.youtube.com/watch?v=cVZMah9kEjI

def merge_sort(medications, key):
    arr = [m.copy() for m in medications]
    _merge_sort_helper(arr, key)
    # make a copy of the list then pass it to the recursive helper to sort in place
    return arr


def _merge_sort_helper(arr, key):
    if len(arr) <= 1:
        return
    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]
    _merge_sort_helper(left, key)
    _merge_sort_helper(right, key)


    i = j = k = 0
    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1



#  SORTING ALGORITHM 3 — QUICK SORT O(n log n) avg / O(n^2) worst case 

def quick_sort(medications, key):
    arr = [m.copy() for m in medications]
    _quick_sort_helper(arr, 0, len(arr) - 1, key)
    # make a copy and sort it in place using the recursive helper
    return arr


def _quick_sort_helper(arr, low, high, key):
    if low < high:
        pivot_idx = _partition(arr, low, high, key)
        _quick_sort_helper(arr, low, pivot_idx - 1, key)
        _quick_sort_helper(arr, pivot_idx + 1, high, key)



def _partition(arr, low, high, key):
    pivot = arr[high][key]
    i = low - 1
    for j in range(low, high):
        if arr[j][key] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]

    return i + 1


#  TIMING HELPER 

def time_ns(func, *args):
    times = []
    result = None
    for i in range(3):
        start = time.perf_counter_ns()
        result = func(*args)
        elapsed = time.perf_counter_ns() - start
        if i > 0:
            times.append(elapsed)

    return sum(times) // len(times), result


#  DISPLAY HELPERS 

def print_search_results(title, results):
    linear_ns, linear_r = results[0]
    binary_ns, binary_r = results[1]
    heap_ns, heap_r = results[2]

    times = [("Linear Scan", linear_ns, len(linear_r)),
             ("Binary Search", binary_ns, len(binary_r)),
             ("Min-Heap", heap_ns, len(heap_r))]
    winner_name, winner_time = min(times, key=lambda x: x[1])[:2]

    print(f"\n  ── Results: {title} ──")
    print("  " + "─" * 57)
    print(f"  {'Algorithm':<20} {'Time (nanoseconds)':>20}  {'Found':>8}")
    print("  " + "─" * 57)
    for name, ns, found in times:
        print(f"  {name:<20} {ns:>20,}  {found:>8,}")
    print("  " + "─" * 57)
    fastest = min(t for _, t, _ in times)
    slowest = max(t for _, t, _ in times)
    ratio = slowest / fastest if fastest > 0 else 1
    print(f"  Winner : {winner_name}  (slowest is {ratio:.2f}x slower)")
    print("  " + "─" * 57)
    # print the comparison table and show the speedup ratio between fastest and slowest
    return heap_r


def print_sort_results(title, results, key_label):
    bubble_ns, bubble_r = results[0]
    merge_ns, merge_r = results[1]
    quick_ns, quick_r = results[2]

    times = [("Bubble Sort", bubble_ns),
             ("Merge Sort", merge_ns),
             ("Quick Sort", quick_ns)]
    winner_name, _ = min(times, key=lambda x: x[1])

    print(f"\n  ── Sorting Results: by {key_label} ──")
    print("  " + "─" * 57)
    print(f"  {'Algorithm':<20} {'Time (nanoseconds)':>20}  {'Complexity':>12}")
    print("  " + "─" * 57)
    print(f"  {'Bubble Sort':<20} {bubble_ns:>20,}  {'O(n^2)':>12}")
    print(f"  {'Merge Sort':<20} {merge_ns:>20,}  {'O(n log n)':>12}")
    print(f"  {'Quick Sort':<20} {quick_ns:>20,}  {'O(n log n)':>12}")
    print("  " + "─" * 57)
    fastest = min(bubble_ns, merge_ns, quick_ns)
    slowest = max(bubble_ns, merge_ns, quick_ns)
    ratio = slowest / fastest if fastest > 0 else 1
    print(f"  Winner : {winner_name}  (slowest is {ratio:.2f}x slower)")
    print("  " + "─" * 57)

    return merge_r


def ask_n():
    print("\n  How many medications to load?")
    print("  [1] 100      [2] 500      [3] 1,000")
    print("  [4] 5,000    [5] 10,000   (full dataset)")
    sizes = {1: 100, 2: 500, 3: 1000, 4: 5000, 5: 10000}
    while True:
        try:
            choice = int(input("\n  Enter choice (1-5): ").strip())
            if choice in sizes:
                return sizes[choice]
        except ValueError:
            pass
        print("  Invalid — please enter a number between 1 and 5.")

#  MENU OPTIONS 

def menu_reorder_check():
    n = ask_n()
    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print("  Running all three search algorithms...\n")

    results = [
        time_ns(linear_scan_reorder, meds),
        time_ns(binary_search_reorder, meds),
        time_ns(heap_reorder, meds),
    ]


    heap_result = print_search_results("Medications Below Reorder Point", results)

    if heap_result:
        print(f"\n  Top 10 Most Urgent Reorders (Min-Heap order — worst first):")
        print(f"  {'Medication':<35} {'On Hand':>8} {'Reorder At':>10} {'Shortfall':>10}")
        print("  " + "─" * 67)
        for name, qty, reorder_pt, shortfall in heap_result[:10]:
            print(f"  {name:<35} {qty:>8,} {reorder_pt:>10,} {shortfall:>10,}")
     


def menu_expiry_check():
    n = ask_n()

    print("\n  Expiry warning threshold:")
    print("  [1] 30 days    [2] 60 days    [3] 90 days")
    thresholds = {1: 30, 2: 60, 3: 90}
    while True:
        try:
            choice = int(input("\n  Enter choice (1-3): ").strip())
            if choice in thresholds:
                threshold = thresholds[choice]
                break
        except ValueError:
            pass
        print("  Invalid — please enter 1, 2, or 3.")


    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print("  Running all three search algorithms...\n")

    results = [
        time_ns(linear_scan_expiry, meds, threshold),
        time_ns(binary_search_expiry, meds, threshold),
        time_ns(heap_expiry, meds, threshold),
    ]
    # run all three expiry search algorithms on the same data with the same threshold

    heap_result = print_search_results(
        f"Medications Expiring Within {threshold} Days", results)

    if heap_result:
        print(f"\n  Top 10 Soonest Expiring (Min-Heap order — most urgent first):")
        print(f"  {'Medication':<35} {'Days Left':>10} {'Qty':>8} {'Expires':>12}")
        print("  " + "─" * 69)
        for days, name, qty, exp_date in heap_result[:10]:
            print(f"  {name:<35} {days:>10,} {qty:>8,} {exp_date:>12}")
        # the heap output is already sorted by days_until_expiry so no extra sorting needed


def menu_simulation():
    n = ask_n()
    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print("  Running 30-day simulation with Linear Scan vs Min-Heap...")
    print("  (This may take a moment for large n)\n")

    linear_ns, linear_r = time_ns(linear_scan_simulate, meds, 30)
    heap_ns, heap_r = time_ns(heap_simulate, meds, 30)
 

    l_short, l_waste, l_cost, l_events = linear_r
    h_short, h_waste, h_cost, h_events = heap_r

    winner = "Linear Scan" if linear_ns < heap_ns else "Min-Heap"
    faster = heap_ns / linear_ns if linear_ns < heap_ns else linear_ns / heap_ns

    print(f"  ── 30-Day Simulation Results ({n:,} medications) ──")
    print("  " + "─" * 57)
    print(f"  {'Metric':<28} {'Linear Scan':>13} {'Min-Heap':>13}")
    print("  " + "─" * 57)
    print(f"  {'Shortage Events':<28} {l_short:>13,} {h_short:>13,}")
    print(f"  {'Expired Waste ($)':<28} {l_waste:>13,.2f} {h_waste:>13,.2f}")
    print(f"  {'Total Reorder Cost ($)':<28} {l_cost:>13,.2f} {h_cost:>13,.2f}")
    print(f"  {'Reorder Events':<28} {l_events:>13,} {h_events:>13,}")
    print(f"  {'Time (nanoseconds)':<28} {linear_ns:>13,} {heap_ns:>13,}")
    print("  " + "─" * 57)
    print(f"  Winner : {winner}  ({faster:.2f}x faster)")
    print("  " + "─" * 57)


def menu_sort():
    n = ask_n()

    print("\n  Sort medications by:")
    print("  [1] Expiration date   [2] Name   [3] Price (cost per unit)")
    sort_options = {
        1: ('days_until_expiry', 'Expiration Date'),
        2: ('drug_name', 'Name'),
        3: ('cost_per_unit', 'Price'),
    }
    while True:
        try:
            choice = int(input("\n  Enter choice (1-3): ").strip())
            if choice in sort_options:
                sort_key, key_label = sort_options[choice]
                break
        except ValueError:
            pass
        print("  Invalid — please enter 1, 2, or 3.")

    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print(f"  Sorting by {key_label} using all three algorithms...\n")

    results = [
        time_ns(bubble_sort, meds, sort_key),
        time_ns(merge_sort, meds, sort_key),
        time_ns(quick_sort, meds, sort_key),
    ]

    sorted_meds = print_sort_results("Sort Medications", results, key_label)

    print(f"\n  Top 10 Results sorted by {key_label} (Merge Sort output):")
    print(f"  {'Medication':<35} {key_label:>20}")
    print("  " + "─" * 57)
    for med in sorted_meds[:10]:
        val = med[sort_key]
        if isinstance(val, float):
            print(f"  {med['drug_name']:<35} ${val:>19,.2f}")
        else:
            print(f"  {med['drug_name']:<35} {str(val):>20}")


# MAIN MENU 

def main():

    while True:
        print("\n  What would you like to do?")
        print("  [1] Check medications below reorder point")
        print("  [2] Check medications expiring soon")
        print("  [3] Run 30-day simulation")
        print("  [4] Sort medications")
        print("  [5] Exit")

        choice = input("\n  Enter choice (1-5): ").strip()

        if choice == '1':
            menu_reorder_check()
        elif choice == '2':
            menu_expiry_check()
        elif choice == '3':
            menu_simulation()
        elif choice == '4':
            menu_sort()
        elif choice == '5':
            print("\n  Goodbye!\n")
            break
        else:
            print("  Invalid — please enter 1, 2, 3, 4, or 5.")

        input("\n  Press Enter to return to menu...")


if __name__ == '__main__':
    main()


# In[ ]:




