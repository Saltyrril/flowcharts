def insert_sort(arr, n):
    """Сортировка массива вставками"""
    i = 1
    while i < n:
        j = i - 1
        key = arr[i]
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
        i += 1

def bubble(arr, n):
    # Сортировка пузырьком
    n_pairs = n
    has_swapped = True
    while has_swapped:
        n_pairs -= 1
        has_swapped = False
        for i in range(n_pairs):
            if arr[i] > arr[i + 1]:
                swap(arr, i)
                has_swapped = True

def swap(a, i):
    a[i], a[i+1] = a[i+1], a[i]

if __name__ == "__main__":
    data = [5, 2, 9]
    print("start")
    insert_sort(data, len(data))
    for x in data:
        if x > 5:
            continue
        print(x)
