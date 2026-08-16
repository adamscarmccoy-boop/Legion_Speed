import time
import sys

def main():
    start = time.time()
    total = 0
    for i in range(10_000_000):
        total += i * i % 256
    end = time.time()
    print(f"Runtime: {end - start:.4f}s")
    print(f"Total: {total}")

if __name__ == "__main__":
    main()