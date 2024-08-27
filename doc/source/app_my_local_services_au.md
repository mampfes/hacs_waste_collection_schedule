# App Backend of My Local Services

Support for schedules provided by [App Backend of My Local Services](https://www.localcouncils.sa.gov.au), serving App Backend of My Local Services, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: app_my_local_services_au
      args:
        lat: LATITUDE
        lon: LONGITUDE
        
```

### Configuration Variables

**lat**  
*(String) (required)*

**lon**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: app_my_local_services_au
      args:
        lat: -34.916506399999996
        lon: 138.8820226
        
```

## Supported Councils

The Website says that the following councils are supported, but we did not test all of them. If you find that your council is not supported, please open an issue.

- City of Adelaide
- Adelaide Hills Council
- Adelaide Plains Council
- Alexandrina Council
- Berri Barmera Council
- Campbelltown City Council
- City of Burnside
- City of Charles Sturt
- City of Mount Gambier
- City of Mitcham
- City of Norwood Payneham and St Peters
- City of Onkaparinga
- City of Port Adelaide Enfield
- City of Prospect
- City of Salisbury
- City of West Torrens
- City of Whyalla
- Clare and Gilbert Valleys Council
- Coorong District Council
- District Council of Barunga West
- District Council of Cleve
- Council of Copper Coast
- District Council of Ceduna
- District Council of Elliston
- District Council of Loxton Waikerie
- District Council of Mount Barker
- District Council of Mount Remarkable
- District Council of Robe
- District Council of Streaky Bay
- Light Regional Council
- Mid Murray Council
- Naracoorte Lucindale Council
- Northern Areas Council
- Port Augusta City Council
- Port Pirie Regional Council
- Regional Council of Goyder
- Renmark Paringa Council
- Rural City of Murray Bridge
- Southern Mallee District Council
- The Flinders Ranges Council
- Town of Walkerville
- Wakefield Regional Council
- Yankalilla District Council
- Yorke Peninsula Council

## How to get the source argument

Find the latitude and longitude of your address using [Google Maps](https://www.google.com/maps) or any other maps service. It should be as accurate as possible(many decimal places) to get the correct schedule.
