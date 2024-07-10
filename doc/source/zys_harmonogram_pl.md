# ZYS HARMONOGRAM (Mod by SEMATpl - semat.pl - based on sepan_remondis_pl)

Support for schedules provided by [ZYS HARMONOGRAM](https://zys-harmonogram.smok.net.pl/) for commune:
-Kleszczewo
  CITY/VILLAGE:
  * BUGAJ
  * BYLIN
  * GOWARZEWO
  * KLESZCZEWO
  * KOMORNIKI
  * KREROWO
  * KRZYŻOWNIKI
  * LIPOWIEC
  * MARKOWICE
  * NAGRADOWICE
  * POKLATKI
  * SZEWCE
  * TANIBÓRZ
  * TULCE
  * ZIMIN
  * ŚRÓDKA
-Kostrzyn
  CITY/VILLAGE:
  * ANTONIN
  * BRZEŹNO
  * BUSZKÓWIEC
  * CHORZAŁKI
  * CZERLEJNKO
  * CZERLEJNO
  * DRZĄZGOWO
  * GLINKA DUCHOWNA
  * GLINKA SZLACHECKA
  * GUŁTOWY
  * GWIAZDOWO
  * IWNO
  * JAGODNO
  * KLONY
  * KOSTRZYN
  * LEŚNA GROBLA
  * LIBARTOWO
  * RUJSCA
  * SANNIKI
  * SIEDLEC
  * SIEDLECZEK
  * SIEKIERKI MAŁE
  * SIEKIERKI WIELKIE
  * SKAŁOWO
  * SOKOLNIKI DRZĄZGOWSKIE
  * SOKOLNIKI KLONOWSKIE
  * STRUMIANY
  * TARNOWO
  * TRZEK
  * WIKTOROWO
  * WRÓBLEWO
  * WĘGIERSKIE
  * ŁUGOWINY


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zys_harmonogram_pl
      args:
        city: Komorniki
        street_name: Komorniki
        commune_name: Komorniki
        street_number: 93/1
```

### Configuration Variables

**city**  
*(string) (required)*

**street_address**  
*(string) (required)*

**commune_name**  
*(string) (required)* 
valid value: kleszczewo or kostrzyn

**street_number**  
*(string)(required)*

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zys_harmonogram_pl
      args:
        city: Komorniki
        street_name: Komorniki
        street_number: 93/1
        commune_name: Kleszczewo
      calendar_title: Komorniki 93/1
```

## How to get the source arguments

You have to provide name of the city or village from the list above, then the name of the street and the house number (e.g. 1 or 7/3).
You have to provide commune name - Kleszczewo or Kostrzyn.

You can check whether your address is served by the ZYS supplier on the [ZYS HARMONOGRAM] website: 
- for Kleszczewo commune: https://zys-harmonogram.smok.net.pl/kleszczewo/2024/
- for Kostrzyn commune: https://zys-harmonogram.smok.net.pl/kostrzyn/2024/
