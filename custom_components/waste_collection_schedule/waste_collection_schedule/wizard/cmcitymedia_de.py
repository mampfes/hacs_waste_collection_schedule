import requests
import ssl

class TLSAdapter(requests.adapters.HTTPAdapter):

    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


def get_waste_types(hpid, realmid):
  session = requests.session()
  session.mount('https://', TLSAdapter())
  
  r = session.get(f"https://sslslim.cmcitymedia.de/v1/{hpid}/waste/{realmid}/types")
  r.raise_for_status()

  r = r.json()
  items = r["result"][1]["items"]

  return items

def get_waste_districts(hpid, realmid):
  session = requests.session()
  session.mount('https://', TLSAdapter())
  
  r = session.get(f"https://sslslim.cmcitymedia.de/v1/{hpid}/waste/{realmid}/districts")
  r.raise_for_status()

  r = r.json()
  items = r["result"][1]["items"]

  return items

def get_waste_realms(hpid):
  session = requests.session()
  session.mount('https://', TLSAdapter())
  
  r = session.get(f"https://sslslim.cmcitymedia.de/v1/{hpid}/waste")
  r.raise_for_status()

  r = r.json()
  realm = r["result"][1]["items"]

  return realm

def get_all_hpid():
  i_from = 0
  i_to = 1000 # currently max i found is 

  founds = []

  session = requests.session()
  session.mount('https://', TLSAdapter())

  for i in range(i_from, i_to):
    r = session.get(f"https://sslslim.cmcitymedia.de/v1/{i}/waste")
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


def main():
  i = input("What do you want to do? (0: wizard, 1: get all hpid, 2: get waste types, 3: get waste districts, 4: generate icons list, 5: generate all icons lists): ")
  if i == "1":
    print(get_all_hpid())
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
  elif i == "0":
    print("Wizard:")
    print("Did you find your hpid? (y/n) (look at custom_components/waste_collection_schedule/waste_collection_schedule/service/CMCityMedia.py)")
    i = input()
    if i == "y":
      print("Great, input your hpid:")
    else:
      print("Ok, let's try to find it. This can take a while.")
      get_all_hpid()
      print("Did you know your hpid? (y/n)")
      i = input()
      if i == "n":
        print("Ok, aborting. Then this script does not work for you.")
        return
    
    hpid = input("hpid: ")
    realmid = get_waste_realms(hpid)[0]["id"]
    districts = get_waste_districts(hpid, realmid)
    print("Found districts:")
    for i, district in enumerate(districts):
      print(f"{i}: {district['name']}")
    print("Which one do you want to use? You also can use none, if you want all districts then type n.")
    i = input()
    if i == "n":
      print("Ok, put this in your configuration.yaml:")
      print(f"""
waste_collection_schedule:
    sources:
    - name: cmcitymedia_de
      args:
        hpid: {hpid}
        realmid: {realmid}
""")
    else:
      district = districts[int(i)]
      if district is None:
        print("This is not a valid district.")
        return
      print("Ok, put this in your configuration.yaml:")
      print(f"""
waste_collection_schedule:
    sources:
    - name: cmcitymedia_de
      args:
        hpid: {hpid}
        realmid: {realmid}
        district: {district['id']}
""")
  else:
    print("Unknown command.")

main()