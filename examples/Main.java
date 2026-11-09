public class Main {
    /** Факториал */
    static int fact(int n) {
        int r = 1;
        for (int i = 2; i <= n; i++) r *= i;
        return r;
    }
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        try {
            System.out.println(fact(n));
        } catch (Exception e) {
            System.out.println("err");
        } finally {
            System.out.println("done");
        }
    }
}
