init = 830000
y = 40
d = 0.03

sum = 0
sum2 = 14_200_000
cy = 1

for i in range(y):
    sum *= 1.05
    sum2 *= 1.05

    sum += init * cy


    cy *= (1 - d)

print(sum)
print(sum2)