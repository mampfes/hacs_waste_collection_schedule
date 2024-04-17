# Gmina Miękinia

Support for schedules provided by [Gmina Miękinia](https://www.miekinia.pl/odpady/index.php?id=325) Gmina Miękinia, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_miekinia_pl
      args:
        location_id: LOCATION
```

### Configuration Variables

**location_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ekosystem_wroc_pl
      args:
        location_id: 8
```

## How to get the source arguments

Replace LOCATION_ID with following `id`:
| id | Location | Details |
| --- | --- |
| 1 | Wróblowice, Gałów, Źródła, Lutynia - wielorodzinne | |
| 2 | Miękinia, Mrozów, Wilkszyn - wielorodzinne | |
| 3 | Kokorzyce, Żurawiniec, Krępice | |
| 4 | Brzezinka Średzka, Pisarzowice, Miłoszyn, Gosławice, Prężyce | |
| 5 | Lutynia | |
| 6 | Zakrzyce, Gałów, Gałówek, Radakowice, Łowęcice | |
| 7 | Wilkszyn I (wybrane ulice) | Wilkszyn 1 - poza ulicami: Grabowa,Wiśniowa, Wiśniowe Wzgórze, św. Jadwigi, św. Huberta, św. Mikołaja, św. Gerarda, św. Jacka, św. Krzysztofa, św. Piotra, Wiśniowogórska, św. Wacława, Lawendowa, Liliowa, Różana, Nasturcjowa, Jarzębinowa, Konwaliowa, Storczykowa, Parkowa, Sosnowa, Szafranowa, Topolowa, Chrobrego, Wrzosowa |
| 8 | Brzezina, Wilkszyn II (wybrane ulice) | Wilkszyn tylko ulice: Grabowa,Wiśniowa, Wiśniowe Wzgórze, św. Jadwigi, św. Huberta, św. Mikołaja, św. Gerarda, św. Jacka, św. Krzysztofa, św. Piotra, Wiśniowogórska, św. Wacława, Lawendowa, Liliowa, Różana, Nasturcjowa, Jarzębinowa, Konwaliowa, Storczykowa, Parkowa, Sosnowa, Szafranowa, Topolowa, Chrobrego, Wrzosowa |
| 9 | Miękinia | |