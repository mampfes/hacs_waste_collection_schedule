# Static Source

Support for schedules with static dates or recurrences.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: TYPE
        dates: DATES
        frequency: FREQUENCY
        interval: INTERVAL
        start: START
        until: UNTIL
        count: COUNT
        excludes: EXCLUDES
        weekdays: WEEKDAYS
```

### Configuration Variables

**TYPE**  
*(string) (required)*

The type of this source.

**DATES**  
*(list) (optional)*

A list of dates in format "YYYY-MM-DD" which should be added to the source.
Dates defined in this list will be added in addition to calculated dates from the recurrence and will not be affected by the exclude-list.

**FREQUENCY**  
*(string) (optional)*

Defines the frequency of the recurrence. Must be one of "DAILY", "WEEKLY", "MONTHLY" or "YEARLY".

**INTERVAL**  
*(int) (optional, default: ```1```)*

Defines the interval of the recurrence.

**START**  
*(string) (optional)*

Defines the start of the recurrence in the format "YYYY-MM-DD".
Required if *FREQUENCY* is set.

**UNTIL**  
*(string) (optional)*

Defines the end of the recurrence in the format "YYYY-MM-DD".

**COUNT**  
*(int) (optional)*

Defines the (maximum) number of returned dates. Only used if `until` is not specified. Defaults to 10.

**EXCLUDES**  
*(list) (optional)*

A list of dates in format "YYYY-MM-DD" which should be excluded from the recurrence.

**WEEKDAYS**  
*(weekday | dictionary of weekday and occurrence) (optional)*

Used to define the weekday for weekly or monthly frequencies. A weekday is specified by the following weekday constants: `MO, TU, WE, TH, FR, SA, SU`.

`WEEKDAYS` can be specified in one of the following formats:

1. Single Weekday:

   ```yaml
   weekdays: MO
   ```

2. Dictionary:

   ```yaml
   weekdays: { MO:1, FR:-2 }
   ```

   The additional numerical argument means the nth occurrence of this weekday in the specified frequency (normally only MONTHLY makes sense here). If frequency is set to `MONTHLY`, `MO:1` represents the first Monday of the month. `FR:-2` represents the 2nd last Friday of the month.

## Examples

This example defines a schedule, every 4 weeks starting on Friday, January 14, 2022 until the end of the year.
Two days are removed from the schedule and two days are added instead, which are outside of the recurrence.

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: Altpapier
        frequency: WEEKLY
        interval: 4
        start: '2022-01-14'
        until: '2022-12-31'
        excludes: # Add exception for the recurrence
          - '2022-07-29'
          - '2022-09-23'
        dates: # Manually add dates that are not part of the recurrence
          - '2022-07-28'
          - '2022-09-22'
```

---

Defines a weekly schedule on Wednesday.

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: Altpapier
        frequency: WEEKLY
        weekdays: WE
```

---

Defines a schedule for the 2nd last Thursday of a month.

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: Altpapier
        frequency: MONTHLY
        weekdays: {TH:-1}
```

---

Defines a bi-weekly schedule for starting on the 01-Feb-2023.

```yaml
waste_collection_schedule:
  sources:
    - name: static
      args:
        type: Altpapier
        frequency: WEEKLY
        interval: 2
        start: '2023-02-01'
```
