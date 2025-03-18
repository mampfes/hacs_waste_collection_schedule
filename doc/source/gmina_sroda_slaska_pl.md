# Gmina Środa Śląska

Waste collection for Gmina Środa Śląska.

All data  based on source: [https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/](https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/).

Support by [github issues](https://github.com/ksciana/waste_collection/issues).

## Configuration via configuration.yaml
```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location_id: LOCATION_ID
```

### Configuration Variables

**location_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_sroda_slaska_pl
      args:
        location_id: 3
```

## How to get the source arguments

Replace `LOCATION_ID` with following `Id`:

| Id | Location | Details |
| --: | --- | --- |
| 1 | Środa Śląska 1 |  DLA NIERUCHOMOŚCI JEDNORODZINNYCH: Cmentarna, Czereśniowa, Daszyńskiego, Górna, Gruszkowa, Jabłkowa, Kajakowa, Kilińskiego,Konstytucji 3 Maja,Korczaka, Łąkowa,Mleczarska, Morelowa, Parkowa,Partyzantów, Plac Solny, Plac Wolności, Spokojna, Stawowa,Strzelecka,Śliwkowa, Wąska, Wierzbowa,Winogronowa, Wrocławska, Zaciszna,0Baczyńskiego, Basztowa Al., Białoskornicza, Boya-Żeleńskiego,Brodatgeo H., Chwalimierska, Dojazdowa, Flamandzka, Floriańska, Jana ze Środy, Karnasa,Kopernika, Korwina, Kościuszki, Kościelna,  Księżnej Jadwigi, Księżycowa, Łanowa, Mickiewicza, Ogrodowa,Oławska, Piastów Śląskich, Przyszkolna, Rakoszycka, Różana, Skłodowskiej-Curie, skwer Zesłańców Sybiru, Słoneczna, Słowackiego, Szkolna, Śląska, Willowa, Winnicza,Wiśniowa, Żwirki i Wigury |
| 2 | Ogrodnica,  Proszków | |
| 3 | Bukówek, Cesarzowice, Chwalimierz, Ciechów, Ligotka, Michałów,  Pęczków,  Wrocisławice | |
| 4 | Brodno, Jastrzębce, Kobylniki, Lipnica, Lisiny, Odyniec, Rzeczyca, Słup, Szczepanów, Zakrzów | |
| 5 | Środa Śląska 2 |  DLA NIERUCHOMOŚCI JEDNORODZINNYCH: Bluszczowa, Bociania, Chabrowa, Dworcowa, Fiołkowa, Goździkowa,Irysowa, Jastrzębia, Konwaliowa, Krucza,Legnicka, Leśna, Makowa, Miłosza, Mostowa, Nasturcjowa, Ogrodnicka,Orla, Reymonta, Rumiankowa, Sokola, Spółdzielcza, Storczykowa,Świdnicka,  św. Andrzeja, trakt św. Jakuba, Targowa, Tulipanowa, Waniliowa, Wiejska, Wrzosowa, Żurawia,01 Maja, Akacjowa, Do Termatu, Dębowa, Działkowa, Hallera, Jarzębinowa,Jaśminowa, Jesionowa, Kasztanowa,Klonowa, Kolejowa, Lipnicka, Lipowa, Malczycka,Miła, Młynarska, Na Polance, Ogrody Zamkowe, Traugutta, Sikorskiego, Spacerowa, Stacyjna, Topolowa, Żytnia |
| 6 | Gozdawa, Jugowiec Juszczyn, Komorniki, Kryniczno,Kulin, Przedmoście, Święte, Rakoszyce, Wojczyce | |
