//재귀함수

#include <stdio.h>

void fruit(int count);

int main(void)
{
    fruit(1);

    return 0;
}











//////Func//////
void fruit(int count) {
    printf("%d : apple\n", count);
    if(count == 5) 
        return;
        fruit(count + 1);
    
}
