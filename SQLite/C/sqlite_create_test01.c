#include <stdio.h>
#include <sqlite3.h>

int main()
{
    sqlite3 *db;
    char *errMsg = NULL;

    if (sqlite3_open("/home/smart/work/dbfiles/car.db", &db) != SQLITE_OK) {
        printf("DB 열기 실패\n");
        return 1;
    }

    const char *sql = "CREATE TABLE IF NOT EXISTS car ("
                        "car_num TEXT PRIMARY KEY,"
                        "name TEXT NOT NULL,"
                        "in_time TEXT NOT NULL,"
                        "out_time TEXT NOT NULL"
                        ");";

    if (sqlite3_exec(db, sql, NULL, NULL, &errMsg) != SQLITE_OK) {
        printf("테이블 생성 실패 : %s\n", errMsg);
        sqlite3_free(errMsg);
    }
    else {
        printf("car 테이블 생성 완료\n");
    }

    sqlite3_close(db);

    return 0;
}
