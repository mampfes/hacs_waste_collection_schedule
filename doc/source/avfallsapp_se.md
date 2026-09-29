# Avfallsapp

This is a waste collection schedule integration for the Avfallsapp API. Avfallsapp is used in multiple municipalities in Sweden.

## Current supported service providers (Cities)
<!--Begin of service section-->
- `soderkoping`: Söderköping
- `motala`: Motala
- `vanersborg`: Vänersborg
- `upplands-bro`: Upplands-Bro
- `sigtuna`: Sigtuna (Sivab)
- `teknikivast`: Teknik i Väst (Arvika/Eda)
- `nodra`: Nodra (Norrköping)
- `atvidaberg`: Åtvidaberg
- `boras`: Borås
- `finspang`: Finspång
- `habo`: Håbo
- `kil`: Kil
- `kinda`: Kinda
- `knivsta`: Knivsta
- `kungsbacka`: Kungsbacka
- `vallentuna`: Vallentuna
- `dalavatten`: Dala Vatten och Avfall
- `vafab`: Vafab Miljö
<!--End of service section-->

## Current un-supported service providers (Cities)

The following providers are known to use Avfallsapp but do not expose the
`/wp-json/nova/v1` API on `<name>.avfallsapp.se` (404), so they cannot be added yet.
<!--Begin of service section-->
`gullspang`: Gullspång
`molndal`: Mölndal
`soderhamn`: Söderhamn
`ulricehamn`: Ulricehamn
<!--End of service section-->

## Current un-supported generic service providers (Companies?)

The API host of these providers is unknown or returns an error.
<!--Begin of service section-->
`avfallsappen`: Avfallsappen
`munipal`: Munipal
`june`: June
`nodava`: Nodava
`rambo`: Rambo
`sysav`: Sysav
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

**token**
*(string) (optional)*

Bearer token required by providers that use token-based authentication (e.g. Vänersborg). Obtain it by inspecting the mobile app's network requests.

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

Support for Vänersborg's municipality waste collection schedule.

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsapp_se
      args:
        service_provider: vanersborg
        api_key: <your device ID from the app>
        token: <your bearer token from the app>
```

Support for Nodra's waste collection schedule in Norrköping.

Nodra does not support registering a new device from the integration, so the device ID has to be taken from the mobile app (see [Using the key from the mobile app](#using-the-key-from-the-mobile-app)).

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsapp_se
      args:
        service_provider: nodra
        api_key: <your device ID from the Nodra app>
```

## How to acquire a valid API_KEY

### Using configuration

You can enter an search address in the street address field and click continue. You will see an error at the api_key input filed. But you should be able to select a generated key from the dropdown and continue.

### Using the key from the mobile app

In your mobile phone app, navigate to "Om appen" in the options section and copy the "Enhets-ID" <!-- codespell:ignore appen -->

> **NOTE**: By reusing the same key as in app, the changes you make in your app (adding/removing addresses) directly affects what is fetched by the integration. You could force a reset of key in app by completely re-registrating the app to portal, but then you can no longer access the settings of which addresses that are registered to that key and thereby the integration (unless you restart the integration registration with the new key).

## Disclaimer

This integration is by no means done i cooperation with avfallsapp.se or the cities that uses the portal. It has been reverse-engineered from what is provided by the API and take no responsibillity of miss-use or un-supported use of the API.
