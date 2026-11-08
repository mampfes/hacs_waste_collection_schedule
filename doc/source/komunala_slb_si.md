# Komunala Slovenska Bistrica

Support for schedules provided by [Komunala Slovenska Bistrica](https://www.komunala-slb.si).

Source for Komunala Slovenska Bistrica.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: komunala_slb_si
      args:
        main_region: MAIN_REGION
        bio_region: BIO_REGION
```

### Configuration Variables

**main_region**  
*(string) (required)*

**bio_region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: komunala_slb_si
      args:
        main_region: '5: BREZJE PRI POLJČANAH, BREZJE PRI SLOVENSKI BISTRICI, ČREŠNJEVEC (h.
          št. 144b), DRUMLAŽNO, FAROVEC, HRASTOVEC POD BOČEM, JEŠOVEC, KOČNO OB LOŽNICI, KRASNA,
          KRIŽEČA VAS, LOŽNICA, MODRAŽE, NOVAKE, PRETREŽ, STUDENICE, TRNOVEC PRI SLOVENSKI
          BISTRICI, VRHLOGA, VRHOLE PRI LAPORJU (razen h. št. 31)'
        bio_region: 'PONEDELJEK: Občina Makole: MAKOLE, MOSTEČNO, PEČKE; Občina Poljčane:
          ČADRAMSKA VAS, KRIŽEČA VAS, LUŠEČKA VAS, NOVAKE, POLJČANE, SPODNJA BREŽNICA, SPODNJE
          POLJČANE, STUDENICE, ZGORNJE POLJČANE'
```

## How to get the source arguments

Select your municipality/area from the schedule list published at https://www.komunala-slb.si/google-koledar.html. If your area does not have a separate organic waste collection (or if it is already included in schedules 16, 17, or 18), select 'Brez odvoza bioloških odpadkov'.
