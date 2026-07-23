class Point {
    //1. 멤버 변수
    private int x;
    private int y; // private 변수 -> Ctrl + . -> getter, setter


    //2. 생성자
    public Point() {
    }
    public Point(int x) {
        this.x =x;
    }
    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }


    // 3. 멤버 메소드, getter/setter
    public int getX() {
        return x;
    }
    public void setX(int x) {
        this.x = x;
    }
    public int getY() {
        return y;
    }
    public void setY(int y) {
        this.y = y;
    }

    
}
class ColorPoint extends Point {
    
    //멤버 변수
    public String color;


    // 생성자
    public ColorPoint() {
    }
    public ColorPoint(int x, int y) {
        super(x, y);
    }
    public ColorPoint(int x, int y, String color) {
        super(x, y);
        this.color = color;
    }


    // 멤버 메소드
    public String getColor() {
        return color;
    }
    public void setColor(String color) {
        this.color = color;
    }
}

class SuperColorPoint{
    
    //멤버 변수
    private int thick;


    //생성자
    public SuperColorPoint() {        
    }
    public SuperColorPoint(int thick) {
        this.thick = thick;
    }


    // 멤버 메소드
    public int getThick() {
        return thick;
    }
    public void setThick(int thick) {
        this.thick = thick;
    }
}

public class ColorPointTest {
    public static void main(String[] args) {
        ColorPoint cp = new ColorPoint(3, 03, "빨간색");
        SuperColorPoint scp = new SuperColorPoint(3);
        System.out.println("x좌표 : " + cp.getX() + "\ty좌표 : " + cp.getY());
        System.out.println("색상 : "  + cp.getColor());
        System.out.println("두께 : " + scp.getThick());
    }
}
