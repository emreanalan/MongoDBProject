import re
import pandas as pd

with open("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Labeling/testSet1.txt", "r", encoding="utf-8") as f:
    content = f.read()

groups = []
current_group = []
group_id = 1

for line in content.splitlines():
    shop_match = re.search(r"Shop (\d+)", line)
    if shop_match:
        current_group.append(shop_match.group(1))

    if "🧱 Ortak Manufacturerlar" in line:
        groups.append({
            "GroupID": group_id,
            "Shops": "; ".join(current_group)
        })
        current_group = []
        group_id += 1



df = pd.DataFrame(groups)
df.to_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Labeling/collusion_groupsTest1.csv", index=False, encoding="utf-8")
print("CSV dosyası oluşturuldu: collusion_groups_shops_only.csv")


import pandas as pd

# Dosya yolu (gerekirse güncelle)
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Labeling/collusion_groupsTest1.csv")

# COLLUSION_GROUPS sözlüğü
with open("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Labeling/collusion_groups_dictTest1.py", "w", encoding="utf-8") as f:
    f.write("COLLUSION_GROUPS = {\n")
    for _, row in df.iterrows():
        group_id = int(row["GroupID"])
        shops = [int(shop.strip()) for shop in row["Shops"].split(";")]
        f.write(f"    {group_id}: {shops},\n")
    f.write("}\n")

print("collusion_groups_dict.py dosyası oluşturuldu.")