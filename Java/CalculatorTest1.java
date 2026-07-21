class Calculator {
    //1.멤버 변수
    private int number;
    //2. 생성자
    Calculator(){
        //dafault 생성자
    }
    //3. 멤버 메소드
    public int sum(int a, int b) {
        return a + b;
    }
}

public class CalculatorTest1 {
    public static void main(String[] args) {
        int i = 20;
        int result;

        Calculator cal = new Calculator();
        
        result = cal.sum(i, 10);
        System.out.println("함수의 결과는 : " + result);
        //System.out.println("Hello Java~!");
    }
}
