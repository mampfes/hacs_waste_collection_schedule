# Blisko.App

Support for schedules provided by [Blisko](https://blisko.co/).

Blisko app supports mutliple voivodeships and cities. 


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blisko
      args:
        regionId: 112
        formattedId: "32:11:01:2:0774204:42719:32"
```

### Configuration Variables

**regionId**  
*(string) (required)*

**formattedId**  
*(string)(required)*

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: blisko
      args:
        regionId: 112
        formattedId: "32:11:01:2:0774204:42719:32"
```

## How to get the source arguments

You have to provide: 
* `regionId` - An ID of owner of Blisko instance for your city.
* `formattedId` - An ID of owner of Blisko instance for your city.

### `regionId`


Region ID can be either queried from `Blisko_searcher.py` helper script or find in the list below:

#### Using Blisko_searcher.py 

```
$ python custom_components/waste_collection_schedule/waste_collection_schedule/service/Blisko_searcher.py --dumpregions
```

### From the list

* 39  Gmina Topólka
* 40  Gmina Strzelin
* 42  Gmina Reda
* 44  Gmina Rumia
* 51  Gmina Złoty Stok
* 61  Klient Szablonowy - Karty Usług
* 73  Gmina Wieluń
* 75  Gmina Łęczyce
* 77  Gmina Kolbudy
* 78  Gmina Polanica-Zdrój
* 81  Gmina Wisznia Mała
* 82  Polkowice
* 83  Gmina Cedry Wielkie
* 84  Gmina i Miasto Nowe Skalmierzyce
* 85  Gmina Chojnów
* 86  Gmina Pajęczno
* 87  Gospodarka Odpadami - Pelplin
* 89  Gmina Szczytna
* 99  ZGPD-7
* 100 Gmina Mysłakowice
* 101 Gmina Krotoszyce
* 103 Gmina Sobótka
* 104 Gmina Wołów
* 109 Gospodarka Odpadami - Starogard Gdański
* 111 Gmina Inowrocław
* 112 Gmina Dobra
* 114 Gmina Słupno
* 115 Gmina Mielec
* 116 Gmina Bardo
* 117 Gmina Żmigród
* 119 Gmina Stawiguda
* 120 Gmina Starogard Gdański
* 121 Gmina Nowa Ruda
* 122 Gmina Legnickie Pole
* 123 Gmina Brzeziny
* 124 Gmina Zduńska Wola
* 125 Gmina Międzybórz
* 127 Gmina Osiecznica
* 128 Gmina Słupca
* 136 Gmina Grabów nad Prosną
* 140 Gmina Mokrsko
* 142 Strzelce Krajeńskie
* 144 Gmina i Miasto Dzierzgoń
* 145 Gmina Brzeg Dolny
* 146 Gmina Wiązów
* 149 Przedsiębiorstwo Gospodarki Komunalnej w Wołowie Sp. z o.o.
* 150 Gmina Staszów
* 153 Miasto Wałbrzych
* 154 Miasto Rejowiec Fabryczny
* 158 Gmina Grodzisk Mazowiecki
* 159 Gmina Świecie
* 160 Gmina Kozy
* 161 Gmina Gniew
* 162 Gmina Ostrowiec Świętokrzyski
* 163 Gmina Skarszewy
* 164 Gminne Przedsiębiorstwo Komunalne Sp. z o.o. w Skarszewach
* 165 Gmina Porąbka
* 166 Gmina Zbrosławice
* 167 Gmina Szumowo
* 168 KOMUS
* 169 Miasto i Gmina Łasin
* 170 Zakład Gospodarki Komunalnej Sp. z o.o.
* 171 Gmina Kamionka Wielka
* 172 Gmina Czernichów
* 173 Gmina Świdnica
* 174 Klient Szablonowy - Ekostrażnik
* 175 Gmina Daleszyce
* 177 Gmina Nowy Staw
* 178 Gmina Przeworno
* 179 Gmina Pruszcz
* 181 Gmina Władysławowo
* 182 Gmina Czechowice- Dziedzice
* 183 ABRUKO PLUS 
* 184 Miasto i Gmina Morawica
* 185 Gmina Wilkowice
* 186 Gmina Wojcieszków
* 187 Gmina Gorzyce
* 188 Gmina Miedziana Góra
* 189 Gmina Mogilany 
* 190 Gmina Gościno
* 191 Gmina Ulan-Majorat
* 192 Gmina Wąchock 
* 193 Gmina Wodzisław
* 194 Miasto Malbork
* 195 Gmina Grodków
* 196 Gmina Zaleszany
* 197 Gmina Gać
* 198 Gmina Kluczbork 
* 199 Miasto Inowrocław
* 200 Ekologiczny Związek Gmin Dorzecza Koprzywianki
* 201 Gmina Miejska Kowal
* 202 Gmina Kruszwica
* 203 Gmina Przykładowa
* 204 Gmina Radoszyce
* 205 Gmina Osiek 
* 206 Gmina Pawłowice
* 208 Gmina Gaworzyce
* 209 Gmina Lubrza
* 210 Parafia św. Wojciecha Biskupa i Męczennika w Nidzicy
* 211 Gmina Pyskowice
* 212 Gmina Nowa Słupia
* 213 Stowarzyszenie Centrum Wspierania Organizacji Pozarządowych i Inicjatyw Obywatelskich
* 214 Gmina Sośno
* 215 Gmina Dygowo
* 216 Gmina Bartniczka
* 218 Gmina Jeżewo
* 219 Gmina Olsztynek
* 220 Gmina Krzanowice
* 221 Gmina Wierzchlas
* 222 Gmina Miejska Hrubieszów 
* 223 Miasto Rydułtowy 
* 224 Gmina Gorlice 
* 225 Gmina Sztum 



### `formattedId`

Formatted ID must be queried from using `Blisko_searcher.py`.

1) First figure out the `regionId`.

2) Dump all cities in the region

```
$ python custom_components/waste_collection_schedule/waste_collection_schedule/service/Blisko_searcher.py --region 112
```

3) Dump all streets for the city:

```
$ python custom_components/waste_collection_schedule/waste_collection_schedule/service/Blisko_searcher.py --region 112 --city 32:11:01:2:0774204
```

If there is no streets for given city `Blisko_searcher.py` will dump house numbers. Use its id as `formattedId`. ( `04:11:07:2:0870362::1` for example).



3) Dump all houses number for street:

```
$ python custom_components/waste_collection_schedule/waste_collection_schedule/service/Blisko_searcher.py --region 112 --street 32:11:01:2:0774204:42719
```

4) Find your house number `id`. This is `formattedId` to be used in configuration.

See example:
```
$ python custom_components/waste_collection_schedule/waste_collection_schedule/service/Blisko_searcher.py --region 112 --street 32:11:01:2:0774204:42719

...
': '99'}, {'id': '32:11:01:2:0774204:42719:100', 'kind': 'STREET_ADDRESS', 'number': '100'}, {'id': '32:11:01:2:0774204:42719:101', 'kind': 'STREET_ADDRESS', 'number': '101'}, {'id': '32:11:01:2:0774204:42719:102', 'kind': 'STREET_ADDRESS', 'number': '102'}, {'id': '32:11:01:2:0774204:42719:103', 'kind': 'STREET_ADDRESS', 'number': '103'}, {'id': '32:11:01:2:0774204:42719:104', 'kind': 'STREET_ADDRESS', 'number': '104'}, {'id': '32:11:01:2:0774204:42719:105', 'kind': 'STREET_ADDRESS', 'number': '105'}, {'id': '32:11:01:2:0774204:42719:106', 'kind': 'STREET_ADDRESS', 'number': '106'}, {'id': '32:11:01:2:0774204:42719:107', 'kind': 'STREET_ADDRESS', 'number': '107'}]
```

So for house `107` in `regionId` 112 and with on specific street `formattedId` is `32:11:01:2:0774204:42719:107`.
