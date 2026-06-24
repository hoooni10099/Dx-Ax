#include <stdio.h>

int main()
{
    int res;
    char ch;

    while(1) {
        res = scanf("%c", &ch);
        if (res == -1) break;
        printf("%d ", ch);
    }
    printf("\n");
    return 0;
}
