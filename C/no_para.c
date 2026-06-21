#include <stdio.h>

double get_num(void);

int main()
{
    double result = get_num();

    printf("반환값 : %lf\n", result);

    return 0;
}












/////////////Func/////////////
double get_num(void) {
    double num;

    printf("양수 입력 : ");
    scanf("%lf", &num);

    return num;
}
