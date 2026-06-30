#include <stdio.h>

int main()
{
    char product[3][20] = {
        "Motor", "Sensor", "PLC"
    };

    for (int i = 0; i < 3; i++) {
        printf("%s\n", product[i]);
    }
    return 0;
}
