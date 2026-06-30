#include <stdio.h>

int main()
{
    char* name1 = "Chulsu";
    char * name2 = "Tomi";

    name1 = "Bob";

    printf("%s\n", name1);
    printf("%s\n", name2);

    return 0;
}
