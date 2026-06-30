#include <stdio.h>
#include <stdlib.h>

int main()
{
    int *pi;
    double *pd;

    // *pi = 10;
    // printf("%d\n", *pi); Segmentation Error
    // 변수는 pi 포인터 변수로 선언했을 뿐, pi는 주소를 값으로 가진다.
    // 10을 주면 pi가 가르키고 있는 공간이 없는데 10을 넣는다?
    // 주소를 줘야 해. -> malloc

    pi = (int *)malloc(sizeof(int)); // Heap 메모리에 4bytes 정수 공간이 만들어짐.
    pd = (double *)malloc(sizeof(double)); //각 변수형에 맞게 캐스팅 필요

    *pi = 10;
    *pd = 3.4;
    printf("%d\n", *pi);
    printf("%.1lf\n", *pd);

    if(pi == NULL) {
        printf("# 정수형 메모리가 부족합니다.\n");
        exit(1);
    }

    if(pd == NULL) {
        printf("# 실수형 메모리가 부족합니다.\n");
        exit(1);
    }

    free(pi);
    free(pd); //댕글링 포인트
    return 0;
}
