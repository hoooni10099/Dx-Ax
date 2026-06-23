#include <stdio.h>

int main()
{
    int a = 10, b = 20;
    int *pa = &a;

    printf("변수 a 값 : %d\n", a);
    printf("변수 a 값 : %d\n", *pa);

    pa = &b;
    printf("\n변수 a 값 : %d\n", b);
    printf("변수 b 값 : %d\n", *pa);

    pa = &a;
    *pa = 30;
    printf("\n변수 a 값 : %d\n", *pa);
    printf("변수 a 값 : %d\n", a);

    return 0;
}
