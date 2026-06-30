#include <stdio.h>

int main()
{
    char *pary[5];
    // char *pary[5] = {"dog", "elephant", "horse", "tiger", "lion"};
    // char pary[5][20] = {"dog", "elephant", "horse", "tiger", "lion"};

    pary[0] = "dog"; // 문자열 상수는 포인터 변수(중요!!)
    pary[1] = "elephant";
    pary[2] = "horse";
    pary[3] = "tiger";
    pary[4] = "lion";

    for (int i = 0; i < 5; i++) {
        printf("%s\n", pary[i]);
    }

    return 0;
}
