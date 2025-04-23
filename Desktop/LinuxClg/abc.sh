#!/bin/bash

echo "Enter a number - "
read num
if [ "$num" -gt 50 ];
then
  echo "Number is greater than 50"
else
  echo "Number is less than 50"
fi

echo "_____________________________________________________________________"

echo "Enter 1st number - "
read num1
echo "Enter 2nd number - "
read num2
echo "Enter 3rd number - "
read num3
if [ "$num1" -gt "$num2" ] && [ "$num1" -gt "$num3" ]; 
then
  echo "$num1 is the greatest"
elif [ "$num2" -gt "$num1" ] && [ "$num2" -gt "$num3" ];
then
  echo "$num2 is the greatest"
else
  echo "$num3 is the greatest"
fi

echo "_____________________________________________________________________"

echo "Enter a number - "
read x
if [ $((x % 21)) -eq 0 ];
then
  echo "$x is divisible by both 3 and 7"
else
  echo "$x is not divisible by both 3 and 7"
fi

echo "_____________________________________________________________________"

echo "Enter a string - "
read str

if [ -z "$str" ];
then 
  echo "The string is empty"
else
  echo "String is not empty"
fi

echo "_____________________________________________________________________"

echo "Enter a number - "
read a

if [ "$a" -gt 10 ] && [ "$a" -le 99 ];
then 
  echo "$a is 2 digit number"
else
  echo "$a is not a 2 digit number"
fi

