#!/bin/bash

# Print system info (lscpu)
echo "System Information (lscpu):"
lscpu

# Perform basic math calculations
echo "Basic Math Calculations:"
a=5
b=3
sum=$((a + b))
diff=$((a - b))
prod=$((a * b))
quot=$((a / b))
echo "Sum: $sum"
echo "Difference: $diff"
echo "Product: $prod"
echo "Quotient: $quot"

# Store output of lscpu and math calculations in files
lscpu > system_info.txt
echo "Sum: $sum" > math_results.txt
echo "Difference: $diff" >> math_results.txt
echo "Product: $prod" >> math_results.txt
echo "Quotient: $quot" >> math_results.txt
