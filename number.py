third_digits = [7, 8, 9]

batch_size = 0
current = 0  # Change this to 100, 200, 300... for the next batch

count = 0
generated = 0

for third in third_digits:
    for middle in range(1000000):
        if count >= current and generated < batch_size:
            print(f"01{third}{middle:06d}07")
            generated += 1

        count += 1

        if generated == batch_size:
            break

    if generated == batch_size:
        break
