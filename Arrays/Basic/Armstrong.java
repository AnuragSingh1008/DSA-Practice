package DSA_Practice.Arrays.Basic;
import java.util.Scanner;

public class Armstrong {
    

class IsArmstrong{
    public static void main(String[] args) {
        Scanner sc=new Scanner(System.in);
        int num=sc.nextInt();
        int power=0;
        int originalNum=num;
        int sum=0;
        while(num>0){
            num/=10;
            power++;
        }
        int temp=originalNum;
        while (temp>0) {
            int digit=temp%10;
            sum+=Math.pow(digit, power);
            temp/=10;
        }
        if(sum==originalNum){
            System.out.println("true number is armstrong");
        }else{
            System.out.println("false number is not armstrong");
        }
    }
}
}
