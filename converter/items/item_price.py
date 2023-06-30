
import xml.etree.ElementTree as ET
import os, json
from ..common_lib import cmdize, nvl, id_generator, extract_int


itemData = {}

def loadItemPrices(xml: str):
    tree = ET.parse(xml)
    root = tree.getroot()
    magics = {}
    armors = {}
    weapons = {}
    for child in root:
        if child.tag.lower() == 'item':
            try:
                name=child.find('name').text
                accessor=cmdize(name)
                costString = child.find("cost").text
                cost = extract_int(costString)
                denomination = "gp"
                if " sp" in costString:
                    cost /= 10.0
                elif " cp" in costString:
                    cost /= 100.0
                itemData[accessor] = cost

                if "mundane" in child.attrib and child.find("type").text == "Armor":
                    armors[accessor] = cost

                if "mundane" in child.attrib and child.find("type").text == "Weapon":
                    weapons[accessor] = cost

                # apply +X
                if "mundane" not in child.attrib:
                    magics[accessor] = child
                    continue
                if child.find("type").text == "Weapon":
                    itemData[accessor+"-+1"] = max(cost*10, 50)
                    itemData[accessor+"-+2"] = max(cost*100, 150)
                    itemData[accessor+"-+3"] = max(cost*350, 300)
                    itemData[accessor+"-+4"] = max(cost*600, 1000)
                    itemData[accessor+"-+5"] = max(cost*1000, 2500)
                elif child.find("type").text == "Armor" and name.endswith("Shield"):
                    itemData[accessor+"-+1"] = max(cost*150, 1000)
                    itemData[accessor+"-+2"] = max(cost*500, 5000)
                    itemData[accessor+"-+3"] = max(cost*1000, 10000)
                elif child.find("type").text == "Armor":
                    itemData[accessor+"-+1"] = max(cost*10, 100)
                    itemData[accessor+"-+2"] = max(cost*50, 5000)
                    itemData[accessor+"-+3"] = max(cost*100, 20000)
            except: pass
    for item in magics.values():
        try:
            itemName = cmdize(item.find('name').text)
            itemType = item.find("type").text
            itemSubtype = cmdize(item.find("subtype").text)
            if itemType == "Armor":
                if itemSubtype in armors:
                    continue
                for armor, price in armors.items():
                    combinedName = armor+"-"+itemName
                    for cn in [combinedName, combinedName.replace("armor-armor","armor")]:
                        itemData[cn] = price + itemData[itemName]
            if itemType == "Weapon":
                if itemSubtype in weapons:
                    continue
                for weapon, price in weapons.items():
                    combinedName = weapon+"-"+itemName
                    for cn in [combinedName, combinedName.replace("-weapon",""), combinedName.replace("weapon-","")]:
                        itemData[cn] = price + itemData[itemName]
        except: pass
    return itemData

def updatePrice(folder, updatedPrices):
    for dp, _, filenames in os.walk(folder):
        for fname in filenames:
            path = os.path.join(dp,fname)
            with open(path, "r", encoding="utf-8") as iFp:
                item = json.load(iFp)
            itemname = cmdize(item["name"])
            if itemname in updatedPrices:
                try:
                    value = updatedPrices[itemname]
                    price = {
                        "value": int(value),
                        "denomination": "gp"
                    }
                    if value < 0.1:
                        price = {
                            "value": int(value*100),
                            "denomination": "cp"
                        }
                    elif value < 1:
                        price = {
                            "value": int(value*10),
                            "denomination": "sp"
                        }
                    item["system"]["price"] = price
                    with open(path, "w", encoding="utf-8") as iFp:
                        json.dump(item, iFp, indent=2)
                        iFp.write("\n")
                except:
                    print("FAIL:", item["name"])

if __name__ == "__main__":
    up = loadItemPrices(os.path.join("..","dm-helper-data","dnd-5e","items.xml"))
    updatePrice(os.path.join("packs","src","items"), up)
