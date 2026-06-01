import pandas as pd

# 创建一个示例DataFrame，包含重复行
df = pd.DataFrame({
    'A': [1, 1, 2, 2, 3, 3, 3],
    'B': ['a', 'a', 'b', 'b', 'c', 'c', 'c'],
    'C': [1, 1, 2, 2, 3, 4, 3]
})

print("原始DataFrame:")
print(df)

# 检测重复数据
duplicates = df.duplicated()
print("\n重复数据检测（标记重复行）:")
print(duplicates)

# 删除重复数据，默认保留第一次出现的行
df_deduplicated = df.drop_duplicates()
print("\n删除重复数据后的DataFrame（保留第一次出现的行）:")
print(df_deduplicated)

# 删除重复数据，保留最后一次出现的行
df_deduplicated_last = df.drop_duplicates(keep='last')
print("\n删除重复数据后的DataFrame（保留最后一次出现的行）:")
print(df_deduplicated_last)