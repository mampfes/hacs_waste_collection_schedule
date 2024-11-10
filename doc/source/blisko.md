# Poznań

Support for schedules provided by [Blisko](https://blisko.co/).

Blisko app supports mutliple voivodeships and cities. 
Each voivodeships has its own `ownerId` - an ID that Blisko assigns to a city/voivodeships. 

Unfortunately there is no easy was to figure out necessary arguments; those can be figured out by:
* Inspecting via Web Developer tools a web page that your local government provides with waste collection schedule. For instance my local government host the schedule [here](https://dobraszczecinska.pl/wiadomosc/gospodarka-odpadami-w-gminie-dobra).
* If there is no web page available one can use [MITM proxy](https://mitmproxy.org/) and eavesdropping Blisko App communication with the server. 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blisko
      args:
        ownerId: 112
        cityId: 0774204
        streetId: 42719
        houseId: 32
```

### Configuration Variables

**ownerId**  
*(string) (required)*

**cityId**  
*(string)(required)*

**streetId**  
*(string)(required)*

**houseId**  
*(string)(required)*

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: blisko
      args:
        ownerId: 112
        cityId: 0774204
        streetId: 42719
        houseId: 32
```

## How to get the source arguments

You have to provide: 
* `ownerId` - An ID of owner of Blisko instance for your city.
* `cityId` - An ID of owner of Blisko instance for your city.
* `streetId` - An ID of owner of Blisko instance for your city.
* `houseId` - An ID of owner of Blisko instance for your city.
You can check if your address is covered by SepanRemondis provider at page [poznan.pl](https://www.poznan.pl/mim/odpady/harmonogramy.html)
