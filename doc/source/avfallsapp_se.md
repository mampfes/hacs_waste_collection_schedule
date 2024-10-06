# EDPEvent

This is a waste collection schedule integration for the Avfallsapp API. Avfallsapp is used in multiple municipalities in Sweden.

## Current supported service providers
<!--Begin of service section-->
- `soderkoping`: Söderköping
<!--End of service section-->

<!-- `atvidaberg`: Åtvidaberg (not supported but could be added)
`boras`: Borås (not supported but could be added)
`finspang`: Finspång (not supported but could be added)
`gullspang`: Gullspång (not supported but could be added)
`habo`: Habo (not supported but could be added)
`kil`: Kil (not supported but could be added)
`kinda`: Kinda (not supported but could be added)
`knivsta`: Knivsta (not supported but could be added)
`kungsbacka`: Hungsbacka (not supported but could be added)
`molndal`: Mölndal (not supported but could be added)
`motala`: Motala (not supported but could be added)
`sigtuna`: Sigtuna (not supported but could be added)
`soderhamn`: Söderhamn (not supported but could be added)
`ulricehamn`: Ulricehamn (not supported but could be added)
`vallentuna`: Vallentuna (not supported but could be added)
`vanersborg`: Vänerborg (not supported but could be added)

`avfallsappen`:
`munipal`:

`dalavatten`:
`june`:
`nodava`:
`nodra`:
`rambo`:
`sysav`:
`upplands-bro`:
`vafab`:  -->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsappen_se
      args:
        kpi_key: KEY_FROM_MOBILE_APP
        service_provider: SERVICE_PROVIDER
```

### Configuration Variables

***kpi_key***
*(string) (required)*

**street_address**
*(string) (optional, not used at the moment)*

**service_provider**
*(string) (optional)*

## Examples

Support for Söderköping's municipality waste collection schedule.

```yaml
waste_collection_schedule:
  sources:
    - name: edpevent_se
      args:
        api_key: 1564ad55f23454
        service_provider: soderkoping
```

## How to acquire a valid API_KEY

In your mobile phone app, navigate to "Om appen" in the options section and copy the "Enhets-ID"
