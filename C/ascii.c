#include <stdio.h>

void print_big();
void print_small();
void print_number();

int main()
{
    print_big();
    print_small();
    print_number();

    return 0;
}

void print_big() {
    char big = 'A';
    for(int i = 0; i < 26; i++) {
        printf("%3c", big);
        big++;
    }
    printf("\n");
}

void print_small() {
    char small = 'a';
    for(int i = 0; i < 26; i++) {
        printf("%3c", small);
        small++;
    }
    printf("\n");
}

void print_number() {
    int num = 0; //char ch = '0';
    for(int i = 0; i < 9; i++) {
        printf("%3d", num);
        num++;
    }
    printf("\n");
}
