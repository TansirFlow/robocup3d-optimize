import re

text=""

pattern = r"\(SLT ([\d\.\s-]+)\)\(nd StaticMesh \(setVisible 1\) \(load models/soccerball.obj\)"

result = re.search(pattern, text)

if result:
    numbers = result.group(1).split()
    print("提取的可变数字：", numbers)
else:
    print("未找到匹配的文本")
