import java.util.Scanner;

public class ScannerEx {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("정수를 1개 입력하세요 : ");
        int number = sc.nextInt();

        System.out.println("입력받은 정수는 " + number + "입니다.");

    }
}
