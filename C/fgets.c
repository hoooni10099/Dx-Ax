#include <stdio.h>

int main()
{
    char str[80];

    printf("문자열 입력 : ");
    fgets(str, sizeof(str), stdin);

    printf("sizeof(80) : %d sizeof(str) : %d\n", sizeof(80), sizeof(str));

    printf("%s\n", str);
    return 0;
}
