d
명령 팔레트 tasts -> 작업기본빌드작업구성 gcc 기본 빌드작업으로 표시되어 있습니다.
tasks.json 파일에서
"${fileDirname}/${fileBasenameNoExtension}", "-lsqlite3"

PostgreSQL

Nas - Mariadb -> mp3 나만의 멜론



smart@3ST20:~$ ls -a
.              .bashrc   .dotnet      .profile                   .wget-hsts
..             .cache    .lesshst     .sqlite_history            SQLiteStudio
.bash_history  .config   .local       .vscode-remote-containers  sqlitestudio-3.4.21-linux-x64.tar.xz
.bash_logout   .copilot  .motd_shown  .vscode-server             work
smart@3ST20:~$ cd ~
smart@3ST20:~$ ls -a
.              .bashrc   .dotnet      .profile                   .wget-hsts
..             .cache    .lesshst     .sqlite_history            SQLiteStudio
.bash_history  .config   .local       .vscode-remote-containers  sqlitestudio-3.4.21-linux-x64.tar.xz
.bash_logout   .copilot  .motd_shown  .vscode-server             work
smart@3ST20:~$ nano .sqliterc
smart@3ST20:~$ ls -a
.              .cache    .local           .vscode-remote-containers             work
..             .config   .motd_shown      .vscode-server
.bash_history  .copilot  .profile         .wget-hsts
.bash_logout   .dotnet   .sqlite_history  SQLiteStudio
.bashrc        .lesshst  .sqliterc        sqlitestudio-3.4.21-linux-x64.tar.xz
smart@3ST20:~$ cat .sqliterc
.header on
.mode table
.nullvalue NULL
.timer on
PRAGMA foreign_keys;
smart@3ST20:~$ sqlite3 ~/wokr/dbfiles/lot2.db
-- Loading resources from /home/smart/.sqliterc
SQLite version 3.46.1 2024-08-13 09:16:08
Enter ".help" for usage hints.
sqlite>




ON DELETE CASCADE와 같은 명령어 사용할 때 신중하게 생각하고 사용
이 프로젝트에서 테이블들을 한꺼번에 삭제해도 되는가?
