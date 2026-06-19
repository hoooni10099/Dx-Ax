#include <stdio.h>
#include <stdlib.h> // rand(), srand() 함수를 사용하기 위해 필요
#include <time.h>   // time() 함수를 사용하기 위해 필요

int main() {
    // 실행할 때마다 진짜 랜덤한 값이 나오도록 시드(Seed) 초기화
    srand((unsigned int)time(NULL)); 

    printf("=== 🏭 생산 프로세스 시작 (총 3회 시도) ===\n\n");

    for (int i = 1; i <= 3; i++) {
        // 30 ~ 50 사이의 랜덤 온도 생성 (50 - 30 + 1 = 21)
        int cen = rand() % 21 + 30; // rand() % (max - min + 1) + min
        
        printf("[%d차 생산 시도] 현재 설정 온도: %d°C\n", i, cen);
        
    }

    printf("\n🏁 3회 생산 시도가 모두 완료되었습니다.\n");
    return 0;
}
