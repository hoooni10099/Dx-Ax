abstract class Shape {
    abstract public void draw();
}
class Circle extends Shape {

    @Override
    public void draw() {
        // TODO Auto-generated method stub
        System.out.println("원을 그리다.");
    }
    
}
class Rect extends Shape{

    @Override
    public void draw() {
        // TODO Auto-generated method stub
        
    }
    
}

public class ShapeTest {
    public static void main(String[] args) {
        Circle circle = new Circle();
        circle.draw();
    }
}
