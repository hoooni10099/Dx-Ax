class Person1 {
    public String name;
    public Person1(String name) {
        this.name = name;
    }
}

class Student1 extends Person1 {
    public Student1(String name) {
        super(name);
    }
}


public class UpDown {
    public static void main(String[] args) {
        //업캐스팅
        Person1 person = new Student1("홍길동");
        System.out.println(person.name);
    }
}
