# Avfallsapp

This is a waste collection schedule integration for the Avfallsapp API. Avfallsapp is used in multiple municipalities in Sweden.

## Current supported service providers (Cities)
<!--Begin of service section-->
- `soderkoping`: Söderköping
<!--End of service section-->

## Current un-supported service providers (Cities)

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

## Current un-supported generic service providers (Companies?)

Could be possible to add by some minor additions
<!--Begin of service section-->
`avfallsappen`: Avfallsappen
`munipal`: Munipal
`dalavatten`: Dalavatten
`june`: June
`nodava`: Nodava
`nodra`: Nodra
`rambo`: Rambo
`sysav`: Sysav
`upplands-bro`: Upplands Bro
`vafab`: Vafab
<!--End of service section-->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsapp_se
      args:
        service_provider: SERVICE_PROVIDER
        api_key: API Key
```

### Configuration Variables

**service_provider**
*(string) (required)*

<!-- ***streeet_address***
*(string) (optional)* -->

**api_key**
*(string) (optional)*

## Examples

Support for Söderköping's municipality waste collection schedule.

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsapp_se
      args:
        api_key: <your api_key from app>
        service_provider: soderkoping
```

## How to acquire a valid API_KEY

### Using configuration

You can enter an search address in the street address field and click continue. You will see an error at the api_key input filed. But you should be able to select a generated key from the dropdown and continue.

### Using the key from the mobile app

In your mobile phone app, navigate to "Om appen" in the options section and copy the "Enhets-ID"

> **NOTE**: By re-using the same key as in app, the changes you make in your app (adding/removing addresses) directly affects what is fetched by the integration. You could force a reset of key in app by completely re-registrating the app to portal, but then you can no longer access the settings of which addresses that are registered to that key and thereby the integration (unless you restart the integration registration with the new key).

## Disclaimer

This integration is by no means done i cooperation with avfallsapp.se or the cities that uses the portal. It has been reverse-engineered from what is provided by the API and take no responsibillity of miss-use or un-supported use of the API.
