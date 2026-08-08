def selection_sort(a):
    n = len(a) # 정렬해야 할 숫자의 개수
    for i in range(n-1):
        min_idx = i # 현재까지 발견한 가장 작은 숫자의 위치
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]

        print(a)


numbers = [5, 2, 4, 1, 3]

selection_sort(numbers)

print('result : ', numbers)
