#include <stdio.h>

int main() {

    char ch = 127;
    unsigned char ch2 = 255;
    unsigned int a;

    printf("%d\n", ch);
    printf("%d\n", ch2);
    
    a = 4294967295;
    printf("%d\n", a);

    a = -1;
    printf("%u\n", a);

    return 0;
}
