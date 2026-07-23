class Person {
    public Person() {
        System.out.println("Person 생성자 실행");
    }
}

class Student extends Person {
    public Student() {
        System.out.println("Student 생성자 실행");
    }
}

class StudentWorker extends Student {
    public StudentWorker() {
        System.out.println("StudentWorker 생성자 실행");
    }
}


public class PersonTest {
    public static void main(String[] args) {
        Person person = new Person();
        System.out.println();
        Student student = new Student();
        System.out.println();
        StudentWorker studentWorker = new StudentWorker();
    }
}
