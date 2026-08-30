# Gmina Bochnia

Harmonogram wywozu odpadów komunalnych dla Gminy Bochnia (woj. małopolskie), w tym miejscowości Baczków, Damienice, Krzyżanowice, Proszówki i pozostałych sołectw.

Website: [http://bochnia-gmina.pl/p,3,harmonogram-wywozu-odpadow-komunalnych-i-zasady-segregacji](http://bochnia-gmina.pl/p,3,harmonogram-wywozu-odpadow-komunalnych-i-zasady-segregacji)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bochnia_gmina_pl
      args:
        town: "Baczków"
```

### Configuration Variables

**town**  
*(string) (required)* Nazwa miejscowości w gminie Bochnia (np. `Baczków`, `Damienice`, `Krzyżanowice`, `Proszówki`, `Łapczyca`, `Siedlec`, etc.).

## Supported Towns

* Baczków
* Bessów
* Bogucice
* Brzeźnica
* Buczyna
* Cerekiew
* Chełm
* Cikowice
* Damienice
* Dąbrowica
* Gawłów
* Gierczyce
* Gorzków
* Grabina
* Krzyżanowice
* Łapczyca
* Majkowice
* Moszczenica
* Nieprześnia
* Nieszkowice Małe
* Nieszkowice Wielkie
* Ostrów Szlachecki
* Pogwizdów
* Proszówki
* Siedlec
* Słomka
* Stanisławice
* Stradomka
* Wola Nieszkowska
* Zatoka
* Zawada

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bochnia_gmina_pl
      args:
        town: "Baczków"
  fetch_time: "04:00"
  day_switch_time: "10:00"

sensor:
  - platform: waste_collection_schedule
    name: "Następny wywóz odpadów"
    value_template: '{{ value.types|join(", ") }}'
  - platform: waste_collection_schedule
    name: "Dni do wywozu odpadów"
    value_template: '{{ value.daysTo }}'
    unit_of_measurement: 'd'
```
