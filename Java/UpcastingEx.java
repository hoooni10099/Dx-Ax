class Person {
    public String name;
    public String id;

    public Person(String name) {
        this.name = name;
    }

    
}
class Student extends Person {
    public String grade;
    public String department;

    public Student(String name) {
        super(name);
    }

}

public class UpcastingEx {
    public static void main(String[] args) {
        Person p; //레퍼런스
        Student s = new Student("이재문");
        p = s; // 업캐스팅
        Person p2 = new Student("홍길동");
        System.out.println(p.name);
        // p.grade -> 보이지 않으므로 에러, Access 불가

        Student s2 = (Student)p; //다운캐스팅
        s2.grade = "A";
        System.out.println(s2.grade);
    }
}
