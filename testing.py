from datetime import datetime

test = "2025-03-02"
test2 = "2025/03/02"
test3 = "2025.03.02"
datetime.min
print(datetime.strptime(test, "%Y-%m-%d"))
print((datetime.strptime(test, "%Y-%m-%d") - datetime.min).days)