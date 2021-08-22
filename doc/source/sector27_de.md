http://muellkalender.sector27.de/muellkalender-oer-erkenschwick.html

# sector27.de

Support for schedules provided by [Sector27.de](https://muellkalender.sector27.de). Some Cities use this service, e.g. Datteln,Oer-Erkenschwick and Marl. This source will show you schedules from the actualmonth an 2 month ahead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        licenseKey: VALIDKEY
        cityId: CITYID
        streetId: STREETID
```

### Configuration Variables

**VALIDKEY**<br>
*(string) (required)*

**CITIYID**<br>
*(string) (required)*

**STREETID**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        licenseKey: Dattelnx2345612
        cityId: 9
        streetId: 2162
```

## How to get the source arguments

At this time this can only be done via "hacking". You have to open the website of your service.

e.g. [Oer-Erkenschwick](http://muellkalender.sector27.de/muellkalender-oer-erkenschwick.html)
select your street and press "aktualisieren".  The schedule for your street is shown.
Now start the developer tools in your browser (usually with F12). Press "aktualisieren" again and look in "network" tab wich url is refreshed. There is on that looks like this:

https://muellkalender.sector27.de/web/fetchPickups?callback=callbackFunc&*licenseKey=OSCXXXKREHXXX*&serverStage=development&*cityId=8*&*streetId=1789*&viewdate=1627812000&viewrange=yearRange&_=1629621078660

Take the marked values and you are prepared.


