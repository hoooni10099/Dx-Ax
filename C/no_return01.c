#include <stdio.h>

int my_print();

int main()
{
    int result = my_print();
    printf("반환값 : %d\n", result);
    return 0;
}










// void 함수는 반환값이 없는 함수입니다. 
//따라서 반환값이 없는 void 함수에서 return 문을 사용할 때는 
//return 뒤에 아무것도 적지 않습니다. 
//하지만 int my_print() 함수에서는 반환값이 int 타입으로 선언되어 있기 때문에, 
//return 문 뒤에 정수 값을 적어야 합니다. 
//위 코드에서는 my_print() 함수가 777을 반환하도록 되어 있습니다.

//////////////Func/////////////
int my_print() {
    printf("Hello World!\n");
    return 777;
}
