#include <stdio.h>
#define N 10

/* Сортировка вставками */
void insertSort(int arr[], int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}

int fact(int n);

int main(void) {
    int a[N], i, s = 0;
    for (i = 0; i < N; i++) {
        scanf("%d", &a[i]);
    }
    insertSort(a, N);
    switch (a[0]) {
        case 1:
        case 2:
            s += 1;
            break;
        case 3:
            printf("three");
            break;
        default:
            s = -1;
    }
    do {
        s--;
        if (s == 5) break;
    } while (s > 0);
    if (s > 0) {
        printf("%d\n", s);
    } else if (s == 0) {
        printf("zero");
    } else {
        return 1;
    }
    return 0;
}
