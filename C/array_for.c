#include <stdio.h>

int main()
{
    int score[5];
    int i;
    int total = 0;

    for (i = 0; i < 5; i++) {
        scanf("%d", &score[i]);
    }

    for (i = 0; i < 5; i++) {
        total += score[i];
    }
    printf("total : %d\n", total);
    
    double avg = total / 5.0;

    for (i = 0; i < 5; i++) {
        printf("%d ", score[i]);
    }
    printf("\n");

    printf("Average: %.1f\n", avg);

    return 0;
}
