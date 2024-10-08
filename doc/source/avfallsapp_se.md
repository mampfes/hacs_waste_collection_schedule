# Avfallsapp

This is a waste collection schedule integration for the Avfallsapp API. Avfallsapp is used in multiple municipalities in Sweden.

## Current supported service providers
<!--Begin of service section-->
- `soderkoping`: Söderköping
<!--End of service section-->

## Current un-supported service providers

Should be possible to add by some minor additions
<!--Begin of service section-->
`atvidaberg`: Åtvidaberg
`boras`: Borås
`finspang`: Finspång
`gullspang`: Gullspång
`habo`: Habo
`kil`: Kil
`kinda`: Kinda
`knivsta`: Knivsta
`kungsbacka`: Hungsbacka
`molndal`: Mölndal
`motala`: Motala
`sigtuna`: Sigtuna
`soderhamn`: Söderhamn
`ulricehamn`: Ulricehamn
`vallentuna`: Vallentuna
`vanersborg`: Vänerborg
<!--End of service section-->

<!--
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
    - name: avfallsapp_se
      args:
        kpi_key: KEY_FROM_MOBILE_APP
        service_provider: SERVICE_PROVIDER
```

### Configuration Variables

***kpi_key***
*(string) (required)*

**service_provider**
*(string) (required)*

## Examples

Support for Söderköping's municipality waste collection schedule.

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsapp_se
      args:
        api_key: 1564ad55f23454
        service_provider: soderkoping
```

## How to acquire a valid API_KEY

In your mobile phone app, navigate to "Om appen" in the options section and copy the "Enhets-ID"
