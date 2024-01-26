import re

text = "(nd TRF (SLT 0.125263 -0.99211 -0.0051638 0 0.881711 0.108935 0.459041 0 -0.454857 -0.0620537 0.8884 0 -113.9317 -10.0599792 10.205134 1)(nd StaticMesh (setVisible 1) (load models/rthigh.obj) (sSc 0.07 0.07 0.07)(resetMaterials matNum8 matLeft naowhite)))(nd TRF (SLT 0.125263 -0.99211 -0.0051638 0 0.881711 0.108935 0.459041 0 -0.454857 -0.0620537 0.8884 0 -13.9317 -0.0599792 0.205134 1)(nd StaticMesh (setVisible 1) (load models/rthigh.obj) (sSc 0.07 0.07 0.07)(resetMaterials matNum1 matLeft naowhite)))"

# 匹配括号内的内容
pattern = r"\(nd TRF \(SLT ([\d\.\s-]+)\)\(nd StaticMesh \(setVisible 1\) \(load models/rthigh.obj\) \(sSc 0.07 0.07 0.07\)\(resetMaterials matNum(\d+) matLeft naowhite\)\)\)"
matches = re.findall(pattern, text)

if matches:
    for match in matches:
        all_numbers = []
        numbers = match[0].strip().split(' ')
        all_numbers.extend(numbers)
        pos=all_numbers[12:-1]
        unum = match[1]
        print(f"{unum}号球员坐标({pos[0]},{pos[1]},{pos[2]})")


else:
    print("未找到匹配的内容")
