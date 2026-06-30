#include <stdio.h>

int main()
{
    int ary1[3] = {1, 2, 3};
    int ary2[3] = {4, 5, 6};
    int ary3[3] = {7, 8, 9};
    int *pary[3] = {ary1, ary2, ary3};
    
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%5d", pary[i][j]);
        }
        printf("\n");
    }
    
    return 0;
}
