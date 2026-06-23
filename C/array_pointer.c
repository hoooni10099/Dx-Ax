#include <stdio.h>

int main()
{
    int ary[3];
    int i;

    *(ary + 0) = 10;
    *(ary + 1) = *(ary + 0) + 10;

    printf("세 번째 배열요소에 키보드 입력 : ");
    scanf("%d", ary + 2);

    for (i = 0; i < 3; i++) {
        printf("%d\n", *(ary + i));
    }
    
    return 0;
}
