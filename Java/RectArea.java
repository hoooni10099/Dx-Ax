import java.util.Scanner;

public class RectArea {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("첫번째 정수를 입력하세요 : ");
        int number1 = sc.nextInt();
        
        System.out.print("두번째 정수를 입력하세요 : ");
        int number2 = sc.nextInt();

        System.out.println("입력받은 사각형의 넓이는 " + number1 * number2 + "입니다.");
    }
}
