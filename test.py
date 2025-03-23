ticker = "MMM"
i = 1

ticker_data_simulated = {}

ticker_data_simulated[ticker] = {} 
ticker_data_simulated[ticker][i] = [[1], [2]]
print(ticker_data_simulated)
print("GAP")
ticker_data_simulated[ticker][2] = [[4], [6]]

print(ticker_data_simulated)