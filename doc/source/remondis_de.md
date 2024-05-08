# Remondis Abfallkalender

Support for schedules for cities in Germany which are serviced by the company Remondis and apparently also some which aren't serviced by Remondis (at least on the surface).

It uses the API of the Remondis app.

## Cities & Districts

The API seems to offer support for the following cities, though some don't give any results.

<!--Begin of cities section-->
- Albaching
- Altenberge
- Amerang
- Ascheberg
- Attendorn
- Babensham
- Bad Aibling
- Bad Feilnbach
- Bergheim
- Billerbeck
- Brannenburg
- Breckerfeld
- Burscheid
- Coesfeld
- Datteln
- Drolshagen
- Dülmen
- Dülmen Test
- Edling
- Eiselfing
- Engelskirchen
- Ennepetal
- Erftstadt
- Eslohe
- Essen
- Feldkirchen-Westerham
- Finnentrop
- Fliesteden
- Flintsbach
- Frasdorf
- Freudenberg
- Geseke
- Griesstätt
- Großkarolinenfeld
- Halfing
- Havixbeck
- Herdecke
- Herscheid
- Horstmar
- Höslwang
- Isselburg
- Kiefersfelden
- Kirchhundem
- Kolbermoor
- Kreuztal
- Leichlingen
- Lennestadt
- Lüdinghausen
- Neubeuern
- Neuenrade
- Nordkirchen
- Nordwalde
- Nottuln
- Nußdorf
- Oberaudorf
- Odenthal
- Olfen
- Olpe
- Overath
- Pfaffing
- Prutting
- Pulheim
- Ramerberg
- Raubling
- Recklinghausen
- Rhede
- Riedering
- Rohrdorf
- Rosendahl
- Rosenheim
- Rott
- Saerbeck
- Samerberg
- Schechen
- Schmallenberg
- Schonstett
- Schöppingen
- Senden
- Soyen
- Sprockhövel
- Stephanskirchen
- Sundern
- Söchtenau
- Tuntenhausen
- Versmold
- Viersen
- Vogtareuth
- Vreden
- Wasserburg
- Wenden
- Wermelskirchen
- Wesseling
- Wetter
- Wilnsdorf
- Witten
<!--End of cities section-->


## Limitations

The API only delivers a few (~ 3) future collections for each garbage type.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: remondis_de
      args:
        city: Erftstadt
        postalCode: "50374"
        street: Holzdamm
        streetNumber: "10"
      customize:
        - type: Restabfall 2-woechentlich
          alias: Restabfall
          show: false
        - type: Restabfall 4-woechentlich
          alias: Restabfall
          show: true
        - type: Restabfall 6-woechentlich
          alias: Restabfall
          show: false
```

### Known waste types

In some cities you can book different intervals for some garbage types, in those cases you have to only show the intervals suitable. They are named like this for example "Restabfall 6-woechentlich" or "Restabfall 14-taegig".
Since only dates in the near future are listed, more rare events like christmas tree removal once a year might not always be listed, so to be sure you have to check for it regularily to be sure.

<!--Begin of waste_types section-->
- "Abholung Schadstoffe"
- "Altholz"
- "Ast- & Strauchschnitt"
- "Bioabfall"
- "Gelbe Tonne"
- "Gelber Sack"
- "Leichtstofftonne"
- "Metall- & E-Schrott"
- "Papier"
- "Papier Samstags Mobil"
- "Restabfall"
- "Restabfall 1,1 cbm"
- "Restabfall 14-taegig"
- "Restabfall 2-wöchentlich"
- "Restabfall 4-wöchentlich"
- "Restabfall 6-wöchentlich"
- "Restabfall 8-wöchentlich"
- "Schadstoffmobil (Bringsystem)"
- "Schadstoffsammlung"
- "Sperrmüll"
- "Weihnachtsbaum"
<!--End of waste_types section-->

### Configuration Variables

**city**  
*(string) (required)*

**postalCode**  
*(string) (required)*

**street**  
*(string) (required)*

**streetNumber**  
*(string) (required)*

The API is a bit picky with addresses, it only accepts one specific spellign of an address e.g. it sometimes does not recognize "Hauptstraße" and only accepts the shortened "Hauptstr.", though not always.
There is an autocorrection option in the API, which is used, but it only "extends" the given argument, so passing "Hauptst" would be extended to "Hauptstr.".
So you might have to try a bit e.g. by writing only "Hauptstr" instead of "Hauptstraße".
