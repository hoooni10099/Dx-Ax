#include <stdio.h>

int main()
{
    int score[5];
    int count;

    count = sizeof(score) / sizeof(score[0]);
    
    printf("sizeof(score) : %d\n", sizeof(score));
    printf("sizeof(score[0]) : %d\n", sizeof(score[0]));
    printf("count : %d\n", count);

    return 0;
}
