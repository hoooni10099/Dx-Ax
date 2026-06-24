#include <stdio.h>

void strcpy(char dest[], char src[]);

int main()
{
    char str[100];
    char copied[100];

    printf("입력 : ");
    scanf("%s", str);

    strcpy(copied, str);

    printf("출력 : %s\n", copied);

    return 0;
}

void strcpy(char dest[], char src[]) {
    int i = 0;

    while (src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';
}
