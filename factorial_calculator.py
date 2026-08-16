import sys

def factorial(n):
    result = 1
    for i in range(2, n+1):
        result *= i
    return result

if hasattr(sys, 'argv') and len(sys.argv) > 1:
    try:
        num = int(sys.argv[1])
        if num < 0:
            print("Error: Factorial is not defined for negative numbers.")
        else:
            print(f"Factorial of {num} is {factorial(num)}")
    except ValueError:
        print("Error: Please provide a valid integer.")
else:
    print("Usage: python factorial_calculator.py <number>")