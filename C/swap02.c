#include <stdio.h>

void swap(int *x, int *y) {
    int temp;
    temp = *x;
    *x = *y;
    *y = temp;

    printf("(x, y) : %d, %d\n", *x, *y);
}


int main()
{
    int a = 10, b = 20;

    swap(&a, &b);
    printf("(a, b) : %d, %d\n", a, b);

    return 0;
}
