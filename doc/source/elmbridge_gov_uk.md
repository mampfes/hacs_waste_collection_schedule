# Elmbridge Borough Council

Support for schedules provided by [Elmbridge Borough Council](https://emaps.elmbridge.gov.uk/myElmbridge.aspx?tab=0#Refuse_&_Recycling), serving Elmbridge, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: elmbridge_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

This is required to unambiguously identify the property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: elmbridge
      args:
        uprn: "10013119164"

```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

#### Notes:
The Elmbridge web site does not show a list of collection dates. It describes the day of the week your waste collection(s) happen on, and lists the start date of the weeks this applies to. The format also differs depending on your collection schedule, for example:


```
Refuse and recycling collection days

Your collection day for refuse is Wednesday in the weeks indicated below.

Your collection day for recycling is Wednesday in the weeks indicated below.

Your collection day for garden waste (if you subscribe) is Tuesday in the weeks indicated below.

Recycling and garden waste collections for weeks commencing Monday
10 Oct	-	refuse + garden
17 Oct	-	refuse + recycling
24 Oct	-	refuse + garden
31 Oct	-	refuse + recycling
```

```
Refuse and recycling collection days

Your collection day for refuse and food waste or, recycling and food waste is Tuesday in the weeks indicated below.

Your collection day for garden waste (if you subscribe) is Tuesday in the weeks indicated below.

Recycling and garden waste collections for weeks commencing Monday
10 Oct	-	refuse + food + garden
17 Oct	-	recycling + food
24 Oct	-	refuse + food + garden
31 Oct	-	recycling + food
```

Trying to convert all this into a schedule of  dates for each specific waste collections is a bit fiddly. By way of explanaion of what the the script tries to do:
* It assumes the week-commencing dates are for the current year.
* This'll cause problems in December as upcoming January collections will have been assigned dates in the past.
* Some clunky logic can deal with this:
  * If a date in less than 1 month in the past, it doesn't matter as the collection will have recently occured.
  * If a date is more than 1 month in the past, assume it's an incorrectly assigned date and increments the year by 1.
* Once that's been done, offset the week-commencing dates to match day of the week indicated for each waste collection type. 

There no  indication of how public holidays affect collection schedules, so plenty of scope for things to go wrong!

If you have a better way of doing this, feel free to update all the elmbridge_gov_uk files via a pull request!