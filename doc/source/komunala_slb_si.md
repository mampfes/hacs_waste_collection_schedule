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
        main_region: "5: BREZJE PRI POLJ\u010CANAH, BREZJE PRI SLOVENSKI BISTRICI, \u010C\
          RE\u0160NJEVEC (h. \u0161t. 144b), DRUMLA\u017DNO, FAROVEC, HRASTOVEC POD BO\u010C\
          EM, JE\u0160OVEC, KO\u010CNO OB LO\u017DNICI, KRASNA, KRI\u017DE\u010CA VAS, LO\u017D\
          NICA, MODRA\u017DE, NOVAKE, PRETRE\u017D, STUDENICE, TRNOVEC PRI SLOVENSKI BISTRICI,\
          \ VRHLOGA, VRHOLE PRI LAPORJU (razen h. \u0161t. 31)"
        bio_region: "PONEDELJEK: Ob\u010Dina Makole: MAKOLE, MOSTE\u010CNO, PE\u010CKE; Ob\u010D\
          ina Polj\u010Dane: \u010CADRAMSKA VAS, KRI\u017DE\u010CA VAS, LU\u0160E\u010CKA\
          \ VAS, NOVAKE, POLJ\u010CANE, SPODNJA BRE\u017DNICA, SPODNJE POLJ\u010CANE, STUDENICE,\
          \ ZGORNJE POLJ\u010CANE"
```

## How to get the source arguments

Select your municipality/area from the schedule list published at https://www.komunala-slb.si/google-koledar.html. If your area does not have a separate organic waste collection (or if it is already included in schedules 16, 17, or 18), select 'Brez odvoza bioloških odpadkov'.
