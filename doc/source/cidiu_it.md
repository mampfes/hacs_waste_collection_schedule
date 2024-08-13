# CIDIU S.p.A.

Support for schedules provided by [CIDIU S.p.A.](https://www.cidiu.it/), in the nort-west Turin province in Italy.
The service will scrape the bi-weekly schedule table returned by the getRecollection method from cidiu-processer.php

## How to get the configuration arguments

- Browse to the [waste schedule page](https://cidiu.it/calendario-delle-raccolte)
- Select your town, street name and number from the dropdowns
- Click on "Visualizza il calendario bisettimanale"

If you get a schedule, you can use the same parameters in the configuration

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cidiu_it
      args:
        city: Collegno
        street_name: via Roma
        street_number: '1'

```

### Configuration Variables

**city**  
*(string (required))*

Your city name. All cities/towns/communalities served by CIDIU are listed on the [available service](https://cidiu.it/i-servizi-nel-tuo-comune/) web page.

**street**  
*(string) (required)*

Street name without number, make sure it's the same you tested on the [waste schedule page](https://cidiu.it/calendario-delle-raccolte).

**street_number**  
*(string) (required)*

Street number, make sure it's the same you tested on the [waste schedule page](https://cidiu.it/calendario-delle-raccolte).

## Returned Collections

This source will return the schedule for the next 15 days for each container type.

## Returned collection types

### Indifferenziato

Green bin for general domestic waste.

### Organico

Brown bin for organic waste (food waste and anything biodegradable and compostable).

### Carta

White bin for paper, cardboard, magazines, pamphlets, books, notebooks, paper bags, paper packaging and tetrapaks.

### Vetro e lattine

Green/brown bin for bottles, jars, aluminium drinks cans, metal food cans and canisters, aluminium caps.

### Plastica

Blue bin for water and soft drinks bottles, liquid containers in general, polystyrene, plastic plates and cups, grocery bags.

### Sfalci

Green bin for grass cuts, foliage, and prunings in general


- *Sfalci abbonamento ridotto* will list the bi-weekly schedule collections from March to October
- *Sfalci abbonamento intero* will list the weekly schedule collections from March to October and the monthly schedule from November to February
