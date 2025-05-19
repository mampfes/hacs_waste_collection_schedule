# EDPEvent

This is a waste collection schedule integration for the EDPEvent API. EDPEent is used in multiple municipalities in Sweden. The previous SSAM and Uppsala Vatten integrations have been merged into this integration.
This integration now also supports the municipalities of Boden and Skellefteå.

## Current supported service providers
<!--Begin of service section-->
- `boden`: Boden
- `boras`: Borås Energi och Miljö
- `kretslopp-sydost`: Kretslopp Sydost
- `ljungby-kommun`: Ljungby kommun
- `marks-kommun`: Marks kommun
- `nodra`: Nodra
- `roslagsvatten`: Roslagsvatten
- `skelleftea`: Skellefteå
- `ssam`: SSAM Södra Smalånds Avfall & Miljö
- `uppsalavatten`: Uppsala Vatten
<!--End of service section-->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        street_address: STREET_ADDRESS
        service_provider: SERVICE_PROVIDER
        url: URL
```

### Configuration Variables

**street_address**  
*(string) (required)*

**service_provider**  
*(string) (optional)*

***url***  
*(string) (optional)*

### Note on optional parameters

While service_provider and url are optional. At least one of them must be provided. The service provider can be used with the preconfigured cities. The url can be used to configure the integration with a custom city.

## Examples

Support for Boden's municipality waste collection schedule.

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        street_address: KYRKGATAN 24
        service_provider: boden
```

Support for schedules provided by Uppsala Vatten och Avfall AB, serving the municipality of Uppsala.

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        street_address: SADELVÄGEN 1
        service_provider: uppsalavatten
```

Support for schedules provided by [SSAM](https://ssam.se/mitt-ssam/hamtdagar.html), serving the municipality of Lessebo, Tingsryd, Älmhult, Markaryd and Växjö Sweden.

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        street_address: Asteroidvägen 1, Växjö
        service_provider: ssam
```

Support for schedules provided by Skellefteå municipality.

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        street_address: Frögatan 76 -150
        service_provider: skelleftea
```

## How to get the correct address

To find your correct address, search for it on your service providers website:

- [Boden](https://www.boden.se/boende-trafik/avfall-och-aterbruk/avfall-395A)
- [Skellefteå](https://skelleftea.se/invanare/startsida/bygga-bo-och-miljo/avfall-och-atervinning/sophamtning---nar-toms-soporna)
- [SSAM](https://ssam.se/mitt-ssam/hamtdagar.html)
- [Uppsala Vatten](https://www.uppsalavatten.se/sjalvservice/hamtningar-och-berakningar/dag-for-sophamtning-och-slamtomning)
- [Borås](https://www.borasem.se/webb/privat/avfallochatervinning/abonnemangforhushallsavfall/nastatomningsdag.4.5a231a8f188bd840a1327da.html)
- [Roslagsvatten](https://roslagsvatten.se/hamtningsschema)
- [Marks kommun](https://va-renhallning.mark.se/FutureWebBasic/SimpleWastePickup/SimpleWastePickup)