import requests
import json
from argparse import ArgumentParser


def all_houses_per_street(regionId: int, streetId: str):
    url = "https://gateway.sisms.pl/akun/api/owners/{region}/streetAddresses/list?streetId={formattedSTREET_ID}"
    r = requests.get(url.format(
        region=regionId, formattedSTREET_ID=streetId))

    if r.status_code != 200:
        return
    return r.json()['data']


def all_houses_per_city_no_streets(regionId: int, townId: str):
    url = "https://gateway.sisms.pl/akun/api/owners/{region}/townAddresses/list?townId={formattedTOWN_ID}"
    r = requests.get(url.format(region=regionId, formattedTOWN_ID=townId))

    if r.status_code != 200:
        return

    data = r.json()['data']
    return data


def all_street_per_city(regionId: int, cityId: str):
    url = "https://gateway.sisms.pl/akun/api/owners/{region}/streets/list?townId={formattedTOWN_ID}"
    r = requests.get(url.format(region=regionId, formattedTOWN_ID=cityId))

    if r.status_code != 200:
        return

    data = r.json()['data']
    return data


def dump_regions(region: int):
    url = "https://gateway.sisms.pl/akun/api/owners/{id}/info"
    r = requests.get(url.format(id=region))
    if r.status_code != 200:
        return

    region_name = r.json()["name"]

    url = "https://gateway.sisms.pl/akun/api/owners/{id}/towns/list"
    r = requests.get(url.format(id=region))
    if r.status_code != 200:
        return
    data = r.json()["data"]

    return {'region_name': region_name, 'cities': data}


def fetch_one_city(id: int):
    url = "https://gateway.sisms.pl/akun/api/owners/{id}/info"
    r = requests.get(url.format(id=id))
    if r.status_code != 200:
        return

    data = r.json()
    if "TIMETABLE" not in data["tabs"]:
        return

    return {'id': id, 'region_name': data['name']}


def main():
    parser = ArgumentParser()
    parser.add_argument('--regionmax', type=int, default=300)
    parser.add_argument('--street', type=str, help='formattedId')
    parser.add_argument('--city', type=str, help='formattedId')
    parser.add_argument('--region', type=int)
    parser.add_argument('--dumpregions', action='store_true')
    args = parser.parse_args()

    if args.region and args.street:
        streets_json = all_houses_per_street(
            args.region, args.street)
        if streets_json:
            print(json.dumps(streets_json, indent=2))
        else:
            print("No houeses for region {} and city {}".format(
                args.region, args.city))
        return

    if args.region and args.city:
        streets_json = all_street_per_city(args.region, args.city)
        if streets_json:
            print(json.dumps(streets_json, indent=2))
        else:
            print("No streets for region {} and cityId {}. Dumping house addresses".format(
                args.region, args.city))
            print(json.dumps(all_houses_per_city_no_streets(
                args.region, args.city), indent=2))

        return

    if args.region:
        region_json = (dump_regions(args.region))
        if not region_json:
            print("Region {region} does not exists".format(
                region=args.region))
        else:
            print(json.dumps(region_json, indent=2))
        return

    if args.dumpregions:
        for i in range(args.regionmax):
            data = fetch_one_city(i)
            if data:
                print(json.dumps(data, indent=2))


if __name__ == '__main__':
    main()
