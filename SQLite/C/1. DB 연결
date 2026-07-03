#include <stdio.h>
#include <sqlite3.h>

int main()
{
    sqlite3 *db;

    if(sqlite3_open("products.db", &db) == SQLITE_OK) {
        printf("DB 연결 성공\n");
        sqlite3_close(db);
    }
    else {
        printf("DB 연결 실패\n");
    }
    
    return 0;
}
