package DSA_Practice.Arrays.Medium;

import java.util.Scanner;

public class MinimumSum {
    public static void main(String[] args) {
        Scanner sc=new Scanner(System.in);
        System.out.print("Enter the size of an array: ");
        int size=sc.nextInt();
        int[]arr=new int[size];
        for(int i=0;i<size;i++){
            System.out.print("Enter element"+(i+1)+" -");
            int element=sc.nextInt();
            arr[i]=element;
        }
        System.out.print("Enter the size of subarray- ");
        int subSize=sc.nextInt();
        int sum=0;
        for(int i=0;i<subSize;i++){
            sum+=arr[i];
        }
        int minSum=sum;
        for(int i=subSize;i<arr.length;i++){
            sum=sum-arr[i-subSize]+arr[i];
            minSum=Math.min(minSum, sum);
        }
        System.out.println("minimum sum of subarray of size "+subSize+" is "+minSum);
        sc.close();
    }
}
