# Gmina Trzebnica

Support for schedules provided by [Gmina Trzebnica](https://trzebnica.pl), Poland.

The data is taken from the API of the "Gmina Trzebnica" municipal app (SkyCMS). You need the region ID of your street or village.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_trzebnica_pl
      args:
        region_id: REGION_ID
```

### Configuration Variables

**region_id**
*(integer) (required)*

The ID of your waste collection region, see the tables below.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_trzebnica_pl
      args:
        region_id: 8
```

## How to get the source argument

Look up your street or village in the tables below and use the matching region ID.

Alternatively, install the "Gmina Trzebnica" app (Google Play / App Store) and look up the region in the app's waste calendar section, or query the region list of the API directly:

```bash
curl -H "x-skycms-key: a90a376c6b19307acf1334b1a3937235" \
     -H "x-skycms-device: waste-collection-schedule" \
     -H "x-skycms-type: web" \
     -H "x-skycms-model: waste-collection-schedule" \
     -H "x-skycms-version: 1.0.0" \
     -H "x-skycms-app-version: 1.0.0" \
     -H "x-skycms-language: pl" \
     "https://api.skycms.com.pl/api/v1/rest/garbage/regions"
```

If you configure an unknown region ID, the integration lists all valid IDs in the error message.

## Supported regions

### Trzebnica city zones

| Region ID | Zone |
|-----------|------|
| 4 | Trzebnica 1: Alpejska, Brzoskwiniowa, Agrestowa, Chmielna, Gliniana, Bolesława Chrobrego, Grabowa, Jarzębinowa, Kolejowa, Kwiatowa, Marii Leszczyńskiej, Łączna, Miodowa, Mostowa, Nektarowa, Na Wzgórzach, Ogrodowa, Owocowa, Parkowa, Przemysłowa, Różana, Sportowa, Św. Jadwigi, Węgrzynowska, Widokowa, Wrocławska, Stefana Żeromskiego, Żołnierzy Września |
| 8 | Trzebnica 2: Zaułek Aleksandry, Borówkowa, Henryka Brodatego, Fryderyka Chopina, Czereśniowa, Grunwaldzka, Harcerka, Władysława Jagiełły, Jagodowa, Kazimierza Wielkiego, Władysława Łokietka, Malinowa, Stanisława Moniuszki, Oleśnicka, Ignacego Paderewskiego, Piastowska, Porzeczkowa, Poziomkowa, Samarytańska, Truskawkowa, Wesoła, Winna, Zielonego Dębu |
| 69 | Trzebnica 3.1: Elizy Orzeszkowej, gen. Grota-Roweckiego, gen. Leopolda Okulickiego, gen. Władysława Sikorskiego, Rotmistrza Witolda Pileckiego, gen. Stanisława Maczka, Baśniowa, Janusza Korczaka, Łąkowa, Nowa, gen. Władysława Andersa, Szarych Szeregów, Słowiańska, 1 Maja |
| 70 | Trzebnica 3.2: 3 Maja, Armii Krajowej, Henryka Pobożnego, Jana Pawła II, Świętojańska, Jana Kilińskiego, Jana Olszewskiego, Krakowska, Wincentego Witosa, Władysława Stanisława Reymonta |
| 28 | Trzebnica 4: Adama Asnyka, gen. Józefa Bema, Władysława Broniewskiego, Chabrowa, Cicha, Marii Dąbrowskiej, Fiołkowa, Jaśminowa, Jędrzejowska, Marii Konopnickiej, Krótka, Adama Mickiewicza, Makowa, Cypriana Kamila Norwida, Pogodna, Prusicka, Siostry Hilgi Brzoski, Juliusza Słowackiego, Teatralna, Wojska Polskiego, Wrzosowa |
| 37 | Trzebnica 5: Akacjowa, Brama Trębaczy, Graniczna, Kosmonautów, Lawendowa, Ledowa, Marcinowska, Młynarska, Morelowa, Obornicka, Orzechowa, Piaskowskiego, Polna, Rynek, Sadowa, Słoneczna, Spokojna, Wałowa, Wiosenna, Wiśniowa, Zielona |
| 71 | Trzebnica 6.1: Henryka Sienkiewicza, Ignacego Daszyńskiego, ks. Dziekana Wawrzyńca Bochenka, Milicka, Piwniczna, Pl. M. J. Piłsudskiego, Solna, Stawowa, Tadeusza Kościuszki |
| 72 | Trzebnica 6.2: Drukarska, Bartosza Głowackiego, pl. Włostowica, Jana Matejki, Kościelna, Leśna, Lipowa, Michała Drzymały, Obrońców Pokoju |

### Sołectwa (villages/districts)

| Region ID | Zone |
|-----------|------|
| 95 | Sołectwa 1: Masłów, Cerekwica, Sulisławice, Świątniki, Węgrzynów, Droszów, Malczów, Marcinowo, Rzepotowice, Nowy Dwór |
| 7 | Sołectwa 2: Brzezie, Biedaszków Wielki, Janiszów, Ujeździec Mały, Ujeździec Wielki, Koniowo, Domanowice |
| 6 | Sołectwa 3: Piersno, Boleścin, Skarszyn, Głuchów Górny, Taczów Mały, Taczów Wielki, Brochocin, Będkowo |
| 3 | Sołectwa 4: Skoroszów, Koczurki, Biedaszków Mały, Komorówko, Komorowo, Szczytkowice |
| 74 | Sołectwa 5: Ligota, Księginice, Kobylice, Jaszyce, Małuszyn |
| 79 | Sołectwa 6: Blizocin, Jaźwiny |
| 84 | Sołectwa 7: Masłowiec, Kuźniczysko |
| 88 | Sołectwa 8: Brzyków |
| 93 | Sołectwa 9: Raszów |

### Wielkogabarytowe (bulky waste)

| Region ID | Zone |
|-----------|------|
| 100 | Wielkogabarytowe: Biedaszków Wielki, Brzezie, Brzyków, Domanowice, Janiszów |
| 101 | Wielkogabarytowe: Cerekwica, Marcinowo, Sulisławice, Świątniki, Węgrzynów |
| 102 | Wielkogabarytowe: Droszów, Malczów, Masłów, Nowy Dwór, Rzepotowice |
| 103 | Wielkogabarytowe: Głuchów Górny, Skarszyn, Taczów Mały, Taczów Wielki |
| 104 | Wielkogabarytowe: Będkowo, Boleścin, Brochocin, Piersno, Raszów |
| 105 | Wielkogabarytowe: Jaszyce, Masłowiec, Skoroszów, Kuźniczysko, Małuszyn |
| 106 | Wielkogabarytowe: Blizocin, Jaźwiny, Szczytkowice |
| 107 | Wielkogabarytowe: Biedaszków Mały, Koczurki, Komorowo, Komorówko |
| 108 | Wielkogabarytowe: Kobylice, Księginice, Ligota |
| 99 | Wielkogabarytowe: Koniowo, Ujeździec Mały, Ujeździec Wielki |

Additional regions may be added to the API in the future.

## Note

Other Polish municipalities that use the SkyCMS platform have their own API key and their own region IDs, so they are not covered by this source. Gmina Miękinia is available as a separate source (`gmina_miekinia_pl`).
