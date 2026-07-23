class Person {
    // 멤버 변수
    private int weight;
    //public int ~~

    //getter, setter 멤버 메소드
    public void setWeight(int weight) {
        this.weight = weight;
    }

    public int getWeight() {
        return this.weight;
    }

}

class Student extends Person {

}


public class InheritanceEx {
    public static void main(String[] args) {
        Student gildong = new Student();
        // gildong.weight = 70; 가능
        gildong.setWeight(70);
        System.out.println(gildong.getWeight());
    }
}
