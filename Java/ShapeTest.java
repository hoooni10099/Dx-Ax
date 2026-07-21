class Shape {
    public void draw() {
        System.out.println("도형을 그리다.");
    }
}

class Triangle extends Shape {

    @Override
    public void draw() {
        // TODO Auto-generated method stub
        //super.draw();
        System.out.println("삼각형을 그리다.");
    }
    
}

class Rectangle extends Shape {

    @Override
    public void draw() {
        // TODO Auto-generated method stub
        //super.draw();
        System.out.println("사각형을 그리다.");
    }
    
}

class Circle extends Shape {

    @Override
    public void draw() {
        // TODO Auto-generated method stub
        //super.draw();
        System.out.println("원을 그리다.");
    }
    
}

public class ShapeTest {
    public static void main(String[] args) {
        // 시간이 흐르는 객체 놀이터
        Triangle triangle = new Triangle();
        triangle.draw();
        Rectangle rectangle = new Rectangle();
        rectangle.draw();
        Circle circle = new Circle();
        circle.draw();
    }
}
