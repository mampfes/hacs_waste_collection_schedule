import requests

def get_waste_types(hpid, realmid):  
  r = requests.get(
      f"http://slim.cmcitymedia.de/v1/{hpid}/waste/{realmid}/types")
  r.raise_for_status()

  r = r.json()
  items = r["result"][1]["items"]

  return items

def get_waste_districts(hpid, realmid):
  r = requests.get(
      f"http://slim.cmcitymedia.de/v1/{hpid}/waste/{realmid}/districts")
  r.raise_for_status()

  r = r.json()
  items = r["result"][1]["items"]

  return items

def get_waste_realms(hpid):
  r = requests.get(f"http://slim.cmcitymedia.de/v1/{hpid}/waste")
  r.raise_for_status()

  r = r.json()
  realm = r["result"][1]["items"]

  return realm

def get_all_hpid():
  i_from = 0
  i_to = 1000 # currently max hpid found is 447

  founds = []
  for i in range(i_from, i_to):
    r = requests.get(f"http://slim.cmcitymedia.de/v1/{i}/waste")
    if r.status_code == 200:
      r = r.json()
      items = r["result"][1]["items"]
      if len(items) > 0:
        print(f"Found hpid: {i} -> {items}")
        founds.append((i, items))

      if len(items) > 1:
        print("Found more than one, aborting, look what's going on here, because this is not expected.")
        break

  return founds

def gen_all_icons():
  founds = get_all_hpid()

  text = ""
  for hpid, realms in founds:
    for realm in realms:
      text += gen_icons(hpid, realm)

  return text

def gen_icons(hpid, realm):
    realmid = realm["id"]
    types = get_waste_types(hpid, realmid)
    text = "{ \n"
    text += f'"hpid": {hpid},\n'
    text += f'"realm": {realmid},\n'
    text += f'"name": "{realm["name"]}",\n'
    text += '"icons": {\n'
    for t in types:
      text += f'"{t["id"]}": "", # {t["name"]}\n'
    text += '}, \n'
    text += '}, \n'

    return text

def get_all_districts():
  hpids = get_all_hpid()
  districts_by_hpid = {}
  for founds in hpids:
    hpid = founds[0]
    realmid = founds[1][0]["id"]

    districts_by_hpid[hpid] = (founds, get_waste_districts(
        hpid, realmid), get_waste_types(hpid, realmid))

  return districts_by_hpid

def generate_md_file():
  all_districts = get_all_districts()
  # Open file ../../../doc/source/cmcitymedia_de.md and replace content between <!-- cmcitymedia_de --> and <!-- /cmcitymedia_de --> with all_districts
  content_lines = []
  for found, data in all_districts.items():
    content_lines.append(f"### {data[0][1][0]['name']}\n")
    content_lines.append(f"* HPID: {data[0][0]}\n")
    content_lines.append("#### Available Waste Types\n")
    for t in data[2]:
      content_lines.append(f"* {t['name']} \n")
    content_lines.append(" \n")
    content_lines.append("#### Districts (Name -> ID) \n")
    for d in data[1]:
      content_lines.append(f"* {d['name']} -> {d['id']} \n")
    content_lines.append(" \n")

  with open("./doc/source/cmcitymedia_de.md", "r+") as f:
    lines = f.readlines()
    start = lines.index("<!-- cmcitymedia_de -->\n")
    end = lines.index("<!-- /cmcitymedia_de -->\n")
    lines = lines[:start+1] + content_lines + lines[end:]
    f.seek(0)
    f.writelines(lines)
    f.close()


def main():
  i = input("What do you want to do? (1: get all hpid, 2: get waste types, 3: get waste districts, 4: generate icons list, 5: generate all icons lists, 6: generate attributes to md file): ")
  if i == "1":
    get_all_hpid()
  elif i == "2":
    hpid = input("hpid: ")
    realmid = get_waste_realms(hpid)[0]["id"]
    types = get_waste_types(hpid, realmid)
    for t in types:
      print(f"{t['id']}: {t['name']}")
  elif i == "3":
    hpid = input("hpid: ")
    realmid = get_waste_realms(hpid)[0]["id"]
    districts = get_waste_districts(hpid, realmid)
    for d in districts:
      print(f"{d['id']}: {d['name']}")
  elif i == "4":
    hpid = input("hpid: ")
    realm = get_waste_realms(hpid)[0]
    text = gen_icons(hpid, realm)
    print("Copy this into custom_components/waste_collection_schedule/waste_collection_schedule/service/CMCityMedia.py")
    print("")
    print(text)
  elif i == "5":
    print(gen_all_icons())
  elif i == "6":
    generate_md_file()
  else:
    print("Unknown command.")

main()