# CSCI 377: Computer Algorithms - Final Project
# Hospital Pharmacy Inventory Optimization and Shortage Prevention System
# Team: Ergi Sula & Thomas Kamel
# John Jay College of Criminal Justice, CUNY
#
# Search Algorithms:
#   1. Binary Search  - O(log n)
#      The list is pre-sorted once at startup using merge sort. After that binary
#      search finds the boundary between below-threshold and in-stock medications
#      by cutting the search space in half each step. At n=10,000 that is at most
#      13 comparisons instead of checking all 10,000 records. Fastest search algorithm.
#
#   2. Linear Scan    - O(n)
#      Goes through every single medication one by one and checks if the quantity
#      is below the reorder point. No setup needed, works on unsorted data, but
#      always visits every record no matter what. Middle performer.
#
#   3. Min-Heap       - O(n log n) build, O(log n) per pop
#      Builds a priority queue where the most critical medication is always at the
#      top. Every push and pop costs O(log n) to maintain the heap structure.
#      Slowest for isolated search but wins the 30-day simulation because it stores
#      a direct reference to each medication for O(1) updates instead of a second scan.
#
# Sorting Algorithms:
#   1. Bubble Sort    - O(n^2)
#      Compares every adjacent pair of medications and swaps them if out of order.
#      Repeats until no swaps happen. Two nested loops give n squared comparisons.
#      Included as the worst case baseline - took over 8 seconds at n=10,000.
#
#   2. Merge Sort     - O(n log n)
#      Splits the list in half recursively until lists of size 1, then merges the
#      sorted halves back together by always picking the smaller element. Always
#      O(n log n) with no bad cases. Also used at startup to pre-sort for binary search.
#
#   3. Quick Sort     - O(n log n) average, O(n^2) worst
#      Picks a pivot element and moves everything smaller to the left and larger to
#      the right, then recursively does the same on each side. Fastest sorting
#      algorithm in our results at every input size due to better cache performance
#      and no extra memory needed unlike merge sort.

import csv
import heapq
import time
import sys

sys.setrecursionlimit(20000)

DATA_FILE = "hospital_pharmacy_inventory.csv"

# global pre-sorted lists built once at startup using merge sort
# binary search reads from these so it never has to sort again
SORTED_BY_URGENCY = []
SORTED_BY_EXPIRY = []


# DATA LOADING

def load_medications(filepath, limit=None):  # 1
    medications = []
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        # read each row and convert numeric fields from string to int/float
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            # store each medication as a dictionary with all relevant fields
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


# PRE-SORT AT STARTUP USING MERGE SORT

def _merge_sort_key(arr, key_func):  # 2
    # base case: a list of 1 is already sorted
    if len(arr) <= 1:
        return
    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]
    # recursively sort each half
    _merge_sort_key(left, key_func)
    _merge_sort_key(right, key_func)
    # merge the two sorted halves back together
    i = j = k = 0
    while i < len(left) and j < len(right):
        # always pick the smaller element from either half
        if key_func(left[i]) <= key_func(right[j]):
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    # copy any remaining elements from left
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    # copy any remaining elements from right
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1


def presort_medications(medications):  # 3
    global SORTED_BY_URGENCY, SORTED_BY_EXPIRY

    # sort by urgency score: quantity minus reorder_point
    # negative score means below reorder point - most urgent comes first
    urgency = [m for m in medications if not m['expired']]
    _merge_sort_key(urgency, lambda m: m['quantity'] - m['reorder_point'])
    SORTED_BY_URGENCY = urgency

    # sort by days until expiry ascending - soonest expiring comes first
    expiry = [m for m in medications if not m['expired'] and m['days_until_expiry'] >= 0]
    _merge_sort_key(expiry, lambda m: m['days_until_expiry'])
    SORTED_BY_EXPIRY = expiry


# SEARCH ALGORITHM 1 - BINARY SEARCH O(log n)

def binary_search_reorder(medications):  # 4
    # use the pre-sorted urgency list - no sorting needed here
    sorted_meds = SORTED_BY_URGENCY

    # binary search for the boundary between below-threshold and in-stock
    lo, hi = 0, len(sorted_meds)
    while lo < hi:
        mid = (lo + hi) // 2
        score = sorted_meds[mid]['quantity'] - sorted_meds[mid]['reorder_point']
        # negative score means this medication is below reorder point
        if score < 0:
            lo = mid + 1
        else:
            hi = mid
    # lo now points at the first medication that does NOT need restocking
    # everything to the left needs restocking

    result = []
    for med in sorted_meds[:lo]:
        shortfall = med['reorder_point'] - med['quantity']
        result.append((med['drug_name'], med['quantity'],
                       med['reorder_point'], shortfall))
    return result


def binary_search_expiry(medications, threshold=60):  # 5
    # use the pre-sorted expiry list - no sorting needed here
    sorted_meds = SORTED_BY_EXPIRY

    # binary search for where days_until_expiry exceeds the threshold
    lo, hi = 0, len(sorted_meds)
    while lo < hi:
        mid = (lo + hi) // 2
        # if this medication expires within the threshold, move right boundary up
        if sorted_meds[mid]['days_until_expiry'] <= threshold:
            lo = mid + 1
        else:
            hi = mid
    # everything to the left of lo expires within the threshold

    result = []
    for med in sorted_meds[:lo]:
        result.append((med['days_until_expiry'], med['drug_name'],
                       med['quantity'], med['expiration_date']))
    return result


# SEARCH ALGORITHM 2 - LINEAR SCAN O(n)

def linear_scan_reorder(medications):  # 6
    result = []
    # check every single medication one by one
    for med in medications:
        # skip expired medications
        if not med['expired'] and med['quantity'] < med['reorder_point']:
            shortfall = med['reorder_point'] - med['quantity']
            result.append((med['drug_name'], med['quantity'],
                           med['reorder_point'], shortfall))
    # always visits every record - O(n) no matter what
    return result


def linear_scan_expiry(medications, threshold=60):  # 7
    result = []
    # scan every record and collect anything expiring within the threshold
    for med in medications:
        if not med['expired'] and 0 <= med['days_until_expiry'] <= threshold:
            result.append((med['days_until_expiry'], med['drug_name'],
                           med['quantity'], med['expiration_date']))
    # sort results so soonest expiring comes first
    result.sort()
    return result


def linear_scan_simulate(medications, days=30):  # 8
    # copy the list so we don't modify the original
    meds = [m.copy() for m in medications]
    shortages = 0
    expired_waste = 0.0
    reorder_cost = 0.0
    reorder_events = 0

    for _ in range(days):
        for med in meds:
            # subtract daily usage but never go below zero
            if not med['expired']:
                med['quantity'] = max(0, med['quantity'] - med['daily_usage'])
            # count down the expiry timer each day
            med['days_until_expiry'] -= 1
            # if timer hits below zero mark as expired and log financial waste
            if med['days_until_expiry'] < 0 and not med['expired']:
                med['expired'] = True
                expired_waste += med['quantity'] * med['cost_per_unit']

        # find everything below reorder point using linear scan
        reorder_list = linear_scan_reorder(meds)
        for drug_name, _, _, _ in reorder_list:
            shortages += 1
            # second O(n) scan to find and update the medication - this is the naive part
            for med in meds:
                if med['drug_name'] == drug_name:
                    med['quantity'] += med['reorder_qty']
                    reorder_cost += med['reorder_qty'] * med['cost_per_unit']
                    reorder_events += 1
                    break

    return shortages, round(expired_waste, 2), round(reorder_cost, 2), reorder_events


# SEARCH ALGORITHM 3 - MIN-HEAP O(n log n)

def heap_reorder(medications):  # 9
    heap = []
    # push every medication into the heap with urgency as the priority key
    for med in medications:
        if not med['expired']:
            # negative priority = below reorder point, most negative = most urgent
            priority = med['quantity'] - med['reorder_point']
            heapq.heappush(heap, (priority, med['drug_name'],
                                  med['quantity'], med['reorder_point']))

    result = []
    # pop items off in priority order - most urgent first
    while heap:
        priority, name, qty, reorder_pt = heapq.heappop(heap)
        # stop as soon as priority hits zero - remaining items have enough stock
        if priority >= 0:
            break
        result.append((name, qty, reorder_pt, abs(priority)))
    return result


def heap_expiry(medications, threshold=60):  # 10
    heap = []
    # only push medications that fall within the expiry threshold
    for med in medications:
        if not med['expired'] and 0 <= med['days_until_expiry'] <= threshold:
            heapq.heappush(heap, (med['days_until_expiry'], med['drug_name'],
                                  med['quantity'], med['expiration_date']))

    result = []
    # pop everything off - min-heap gives soonest expiring first automatically
    while heap:
        result.append(heapq.heappop(heap))
    return result


def heap_simulate(medications, days=30):  # 11
    # copy the list so we don't modify the original
    meds = [m.copy() for m in medications]
    shortages = 0
    expired_waste = 0.0
    reorder_cost = 0.0
    reorder_events = 0

    for _ in range(days):
        for med in meds:
            # same daily consumption and expiry logic as linear simulation
            if not med['expired']:
                med['quantity'] = max(0, med['quantity'] - med['daily_usage'])
            med['days_until_expiry'] -= 1
            if med['days_until_expiry'] < 0 and not med['expired']:
                med['expired'] = True
                expired_waste += med['quantity'] * med['cost_per_unit']

        # rebuild the heap each day with updated quantities
        heap = []
        for med in meds:
            if not med['expired']:
                priority = med['quantity'] - med['reorder_point']
                # store a direct reference to the med dict so we can update it in O(1)
                heapq.heappush(heap, (priority, med['drug_id'], med))

        # pop urgent medications and restock directly - no second scan needed
        while heap:
            priority, drug_id, med = heapq.heappop(heap)
            # stop when all remaining medications have enough stock
            if priority >= 0:
                break
            shortages += 1
            # update the record directly through the reference - O(1) update
            med['quantity'] += med['reorder_qty']
            reorder_cost += med['reorder_qty'] * med['cost_per_unit']
            reorder_events += 1

    return shortages, round(expired_waste, 2), round(reorder_cost, 2), reorder_events


# SORTING ALGORITHM 1 - BUBBLE SORT O(n^2)

def bubble_sort(medications, key):  # 12
    # make a copy so we don't modify the original list
    arr = [m.copy() for m in medications]
    n = len(arr)
    for i in range(n):
        swapped = False
        # compare every adjacent pair and swap if out of order
        for j in range(0, n - i - 1):
            if arr[j][key] > arr[j + 1][key]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        # if no swaps happened the list is already sorted - exit early
        if not swapped:
            break
    return arr


# SORTING ALGORITHM 2 - MERGE SORT O(n log n)

def merge_sort(medications, key):  # 13
    # make a copy then pass to the recursive helper
    arr = [m.copy() for m in medications]
    _merge_sort_helper(arr, key)
    return arr


def _merge_sort_helper(arr, key):  # 14
    # base case: list of 1 is already sorted
    if len(arr) <= 1:
        return
    mid = len(arr) // 2
    left = arr[:mid]
    right = arr[mid:]
    # recursively sort each half
    _merge_sort_helper(left, key)
    _merge_sort_helper(right, key)
    # merge step: compare front of each half and pick the smaller one
    i = j = k = 0
    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    # copy leftover elements from whichever half still has items
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1


# SORTING ALGORITHM 3 - QUICK SORT O(n log n) avg / O(n^2) worst

def quick_sort(medications, key):  # 15
    # make a copy and sort it in place using the recursive helper
    arr = [m.copy() for m in medications]
    _quick_sort_helper(arr, 0, len(arr) - 1, key)
    return arr


def _quick_sort_helper(arr, low, high, key):  # 16
    if low < high:
        # partition and get the pivot's final position
        pivot_idx = _partition(arr, low, high, key)
        # recursively sort left and right sides around the pivot
        _quick_sort_helper(arr, low, pivot_idx - 1, key)
        _quick_sort_helper(arr, pivot_idx + 1, high, key)


def _partition(arr, low, high, key):  # 17
    # pick the last element as pivot
    pivot = arr[high][key]
    i = low - 1
    # move everything smaller than pivot to the left
    for j in range(low, high):
        if arr[j][key] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    # place the pivot in its correct final position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


# TIMING HELPER

def time_ns(func, *args):  # 18
    times = []
    result = None
    # run 3 times, discard first run as warm-up
    for i in range(3):
        start = time.perf_counter_ns()
        result = func(*args)
        elapsed = time.perf_counter_ns() - start
        # skip the first run - OS cache effects make it slower
        if i > 0:
            times.append(elapsed)
    # return average of the two remaining runs
    return sum(times) // len(times), result


# DISPLAY HELPERS

def print_search_results(title, results):  # 19
    binary_ns, binary_r = results[0]
    linear_ns, linear_r = results[1]
    heap_ns, heap_r = results[2]

    # build list of (name, time, count) for easy iteration
    times = [("Binary Search", binary_ns, len(binary_r)),
             ("Linear Scan", linear_ns, len(linear_r)),
             ("Min-Heap", heap_ns, len(heap_r))]

    # find the winner by smallest nanosecond count
    winner_name, winner_time = min(times, key=lambda x: x[1])[:2]

    print(f"\n  -- Results: {title} --")
    print("  " + "-" * 57)
    print(f"  {'Algorithm':<20} {'Time (nanoseconds)':>20}  {'Found':>8}")
    print("  " + "-" * 57)
    for name, ns, found in times:
        print(f"  {name:<20} {ns:>20,}  {found:>8,}")
    print("  " + "-" * 57)
    # calculate how much slower the slowest algorithm was vs the fastest
    fastest = min(t for _, t, _ in times)
    slowest = max(t for _, t, _ in times)
    ratio = slowest / fastest if fastest > 0 else 1
    print(f"  Winner : {winner_name}  (slowest is {ratio:.2f}x slower)")
    print("  " + "-" * 57)
    # return heap result since it comes out in urgency order already
    return heap_r


def print_sort_results(title, results, key_label):  # 20
    bubble_ns, bubble_r = results[0]
    merge_ns, merge_r = results[1]
    quick_ns, quick_r = results[2]

    times = [("Bubble Sort", bubble_ns),
             ("Merge Sort", merge_ns),
             ("Quick Sort", quick_ns)]
    winner_name, _ = min(times, key=lambda x: x[1])

    print(f"\n  -- Sorting Results: by {key_label} --")
    print("  " + "-" * 57)
    print(f"  {'Algorithm':<20} {'Time (nanoseconds)':>20}  {'Complexity':>12}")
    print("  " + "-" * 57)
    # show complexity next to each algorithm so theory vs practice is visible
    print(f"  {'Bubble Sort':<20} {bubble_ns:>20,}  {'O(n^2)':>12}")
    print(f"  {'Merge Sort':<20} {merge_ns:>20,}  {'O(n log n)':>12}")
    print(f"  {'Quick Sort':<20} {quick_ns:>20,}  {'O(n log n)':>12}")
    print("  " + "-" * 57)
    fastest = min(bubble_ns, merge_ns, quick_ns)
    slowest = max(bubble_ns, merge_ns, quick_ns)
    ratio = slowest / fastest if fastest > 0 else 1
    print(f"  Winner : {winner_name}  (slowest is {ratio:.2f}x slower)")
    print("  " + "-" * 57)
    # return merge sort result since it is stable
    return merge_r


def ask_n():  # 21
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
        # keep asking until a valid number is entered
        print("  Invalid - please enter a number between 1 and 5.")


# MENU OPTIONS

def menu_reorder_check():  # 22
    n = ask_n()
    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    # pre-sort once so binary search can run in O(log n)
    presort_medications(meds)
    print("  Running all three search algorithms...\n")

    # run all three and collect timing + results
    results = [
        time_ns(binary_search_reorder, meds),
        time_ns(linear_scan_reorder, meds),
        time_ns(heap_reorder, meds),
    ]

    heap_result = print_search_results("Medications Below Reorder Point", results)

    # show top 10 from heap since it returns results in urgency order
    if heap_result:
        print(f"\n  Top 10 Most Urgent Reorders (Min-Heap order - worst first):")
        print(f"  {'Medication':<35} {'On Hand':>8} {'Reorder At':>10} {'Shortfall':>10}")
        print("  " + "-" * 67)
        for name, qty, reorder_pt, shortfall in heap_result[:10]:
            print(f"  {name:<35} {qty:>8,} {reorder_pt:>10,} {shortfall:>10,}")


def menu_expiry_check():  # 23
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
        print("  Invalid - please enter 1, 2, or 3.")

    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    # pre-sort so binary search only needs O(log n)
    presort_medications(meds)
    print("  Running all three search algorithms...\n")

    results = [
        time_ns(binary_search_expiry, meds, threshold),
        time_ns(linear_scan_expiry, meds, threshold),
        time_ns(heap_expiry, meds, threshold),
    ]

    heap_result = print_search_results(
        f"Medications Expiring Within {threshold} Days", results)

    # heap output is already in urgency order - soonest expiring first
    if heap_result:
        print(f"\n  Top 10 Soonest Expiring (Min-Heap order - most urgent first):")
        print(f"  {'Medication':<35} {'Days Left':>10} {'Qty':>8} {'Expires':>12}")
        print("  " + "-" * 69)
        for days, name, qty, exp_date in heap_result[:10]:
            print(f"  {name:<35} {days:>10,} {qty:>8,} {exp_date:>12}")


def menu_simulation():  # 24
    n = ask_n()
    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print("  Running 30-day simulation with Linear Scan vs Min-Heap...")
    print("  (This may take a moment for large n)\n")

    # time the full 30 day run for each strategy
    linear_ns, linear_r = time_ns(linear_scan_simulate, meds, 30)
    heap_ns, heap_r = time_ns(heap_simulate, meds, 30)

    l_short, l_waste, l_cost, l_events = linear_r
    h_short, h_waste, h_cost, h_events = heap_r

    winner = "Linear Scan" if linear_ns < heap_ns else "Min-Heap"
    faster = heap_ns / linear_ns if linear_ns < heap_ns else linear_ns / heap_ns

    print(f"  -- 30-Day Simulation Results ({n:,} medications) --")
    print("  " + "-" * 57)
    print(f"  {'Metric':<28} {'Linear Scan':>13} {'Min-Heap':>13}")
    print("  " + "-" * 57)
    print(f"  {'Shortage Events':<28} {l_short:>13,} {h_short:>13,}")
    print(f"  {'Expired Waste ($)':<28} {l_waste:>13,.2f} {h_waste:>13,.2f}")
    print(f"  {'Total Reorder Cost ($)':<28} {l_cost:>13,.2f} {h_cost:>13,.2f}")
    print(f"  {'Reorder Events':<28} {l_events:>13,} {h_events:>13,}")
    print(f"  {'Time (nanoseconds)':<28} {linear_ns:>13,} {heap_ns:>13,}")
    print("  " + "-" * 57)
    print(f"  Winner : {winner}  ({faster:.2f}x faster)")
    print("  " + "-" * 57)


def menu_sort():  # 25
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
        print("  Invalid - please enter 1, 2, or 3.")

    print(f"\n  Loading {n:,} medications...")
    meds = load_medications(DATA_FILE, limit=n)
    print(f"  Sorting by {key_label} using all three algorithms...\n")

    # run all three sorting algorithms on the same data
    results = [
        time_ns(bubble_sort, meds, sort_key),
        time_ns(merge_sort, meds, sort_key),
        time_ns(quick_sort, meds, sort_key),
    ]

    sorted_meds = print_sort_results("Sort Medications", results, key_label)

    # show top 10 from merge sort since it is stable
    print(f"\n  Top 10 Results sorted by {key_label} (Merge Sort output):")
    print(f"  {'Medication':<35} {key_label:>20}")
    print("  " + "-" * 57)
    for med in sorted_meds[:10]:
        val = med[sort_key]
        # format floats as price with dollar sign, everything else as string
        if isinstance(val, float):
            print(f"  {med['drug_name']:<35} ${val:>19,.2f}")
        else:
            print(f"  {med['drug_name']:<35} {str(val):>20}")


# MAIN MENU

def main():  # 26
    while True:
        print("\n  What would you like to do?")
        print("  [1] Check medications below reorder point")
        print("  [2] Check medications expiring soon")
        print("  [3] Run 30-day simulation")
        print("  [4] Sort medications")
        print("  [5] Exit")

        choice = input("\n  Enter choice (1-5): ").strip()

        # route to the correct menu function based on choice
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
            print("  Invalid - please enter 1, 2, 3, 4, or 5.")

        input("\n  Press Enter to return to menu...")


if __name__ == '__main__':
    main()
