# Mein-abfallkalender.de

Support for schedules provided by [Mein-Abfallkalender](https://mein-abfallkalender.de). 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mein_abfallkalender
      args:
        city: city_name
        street_id: street_id
        cid: city_id
        user_email: email_Address
        user_id: user_id
        user_pwd: user_pwd
        waste_types: 
          - 1
          - 2
          - 3
```

### Configuration Variables

**city**  
*(string) (required)*

**street_id**  
*(integer) (required)*

**waste_types**  
*(list of integer) (required)*

**cid**
*(integer) (optional)*

**user_email**
*(string) (optional)*

**user_id**
*(string) (optional)*

**user_pwd**
*(string) (optional)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mein_abfallkalender
      args:
        city: bad-vilbel
        street_id: 1126
        user_email: test@test.com
        cid: 4
        waste_types:
          - 21 ## Altpapier
          - 22 ## Biotonne
          - 24 ## Gartenabfälle
          - 23 ## Gelbe Tonne
          - 25 ## Hausmüll
          - 126 ## Schadstoffmobil
          - 26 ## Weihnachtsbäume
```

## How to get the source arguments

First check on [https://mein-abfallkalender.de/persoenlicher-abfallkalender-fuer-buerger.html](https://mein-abfallkalender.de/persoenlicher-abfallkalender-fuer-buerger.html) with your postcode if your city is available. For the city name, use the same one as in the URL shown when redirected from the previous page. Eg: https://hofheim.mein-abfallkalender.de/ - Use: hofheim, https://witzenhausen.mein-abfallkalender.de/ - Use: witzenhausen

The integration requires either an email address or a user/password. 

The CID is only required when using user/password as it is provided by the site when performing the authentication with email.

## Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/mein_abfallkalender.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/mein_abfallkalender.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

It requires the city name extracted in the previous step.

### Hardcore Variant: Extract arguments from website

Another way get the source arguments is to use a (desktop) browser, e.g. Google Chrome:

1. Open your city homepage, e.g. [https://witzenhausen.mein-abfallkalender.de/app/webcal.html](https://witzenhausen.mein-abfallkalender.de/app/webcal.html).
2. Select your street
3. In the `Erinnerung`, choose: `keine Erinnerung`
4. In the `Verwendung`, choose: `Termine im iCalendar-Format herunterladen`
5. Select the checkboxes of the `Abfallarten` you want to add to the calendar.
6. Enter an e-mail twice. You will not receive any confirmation so you can choose whatever you want.
7. Check the box `Ich habe die Datenschutzbestimmung zur Kenntnis genommen`.
8. Press the button `Termine via iCal/WebCal nutzen`.
9. On the next page you have a URL, from there you need to use the following parameters:
  - sid = street_id
  - wids = the list of waste types
  - uid = user_id
  - pwid = user_pwd
  - cid = cid

