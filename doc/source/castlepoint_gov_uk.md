# Castle Point Borough Council

Support for schedules provided by [Castle Point Borough Council](https://www.castlepoint.gov.uk), serving the Castle Point district in Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new South East Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        roadID: ROAD_ID
        street_name: STREET_NAME
```

### Configuration Variables

**roadID**  
*(string) (optional)*

**street_name**  
*(string) (optional)*

Either `roadID` or `street_name` is required.

A leading house number is accepted and ignored, so `12 Ash Road` resolves the
same as `Ash Road`.

Some street names occur more than once in the borough — there is a High Street in
both Benfleet and Canvey Island, on different collection rounds. When that
happens the configuration fails with the list of matching streets, each qualified
by its town, and any one of those values can be used verbatim:

```yaml
street_name: "HIGH STREET (CANVEY ISLAND)"
```

To find your `roadID`, go to the [Castle Point my street page](https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1), either enter your street name in the search box or select the first letter of your street, click on the street name, and look for the `roadID` in the URL.

## Note for users outside the UK

`apps.castlepoint.gov.uk` sits behind a firewall that only accepts connections
from UK IP addresses; from anywhere else the connection is dropped without a
reply. A Home Assistant instance hosted outside the UK (including on a
non-UK cloud region or VPN exit) will see this source time out.

## Example

Using a roadID:

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        roadID: "4448"
```

Using a street name:

```yaml
waste_collection_schedule:
    sources:
    - name: castlepoint_gov_uk
      args:
        street_name: "Ash Road"
```
