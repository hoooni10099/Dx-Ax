sudo apt install -y openjdk-21-jdk


java -version
javac -version

readlink -f "$(which java)"

/usr/lib/jvm/java-21-openjdk-amd64/bin/java


nano ~/.bashrc

->export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
<내용 추가>

source ~/.bashrc
-> 적용

vs code에서 Java확장 프로그램 설치



보기 - 명령 팔레트 - Create Java Project - Maven - No Archetype - com.example - demo - 경로 설정
