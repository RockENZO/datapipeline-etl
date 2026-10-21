# Demo data

Real open data, cut down for the browser. Not synthetic.

- **Source:** [RockENZO/Knia-data-repo](https://github.com/RockENZO/Knia-data-repo) (`data files/`, Git LFS). The
  datasets originate from City of Sydney open data (stairs, libraries, recreation centres, information kiosks,
  parking, business rate categories, residential waste recovery) and Spatial NSW (building complex points,
  ambulance stations). Check each publisher's licence and attribution terms before reusing them.
- **Extract:** records inside the inner-Sydney viewport (lon 151.14 to 151.28, lat -33.94 to -33.82). The
  originals cover all of NSW and exceed 700 MB. Records without geometry are kept.
- **Trim:** bookkeeping attributes of the building-complex and ambulance layers are dropped, as is the stairs
  `Photo` file name; coordinates are rounded to 6 decimal places and altitude is removed. Values are otherwise unchanged.
- **Rebuild:** `python tools/build_demo_data.py "<Knia-data-repo>/data files"` (run `git lfs pull` there first).

Libraries and the waste-recovery series carry no coordinates in the source, so the map lists them as table-only records.
