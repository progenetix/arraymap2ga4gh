# Implementation of the [GA4GH](http://github.com/ga4gh/schemas/) schema based on genome profiles and metadata from [arrayMap](http://arraymap.org)

This repository will contain data and information regarding the [arrayMap](http://arraymap.org) based implementation of a GA4GH schema structure. While it is not expected that GA4GH compliant resources mirror the schema in their internal structure, this project is aimed at showing the principle feasibility of such an approach, mainly to test & drive schema development.

Data & schemas represented here are not kept in a stable/versioned status, but are updated together with or anticipating GA4GH schema changes.

Structure:

* data: JSON dumps of data from the arraymap2ga4gh conversion of arrayMap collections (subsets)
* examples: JSON-nice single/few selected biosamples etc. to show value encodings...

### How to Use the data

The data is in JSON format, and you can use MongoDB for easy import and manipulation

You can find the download and installation instructions of the community version [here](https://www.mongodb.com/download-center#community).

To import a JSON file, you can run the following from command line
```
mongoimport --db test --collection arraymap --drop --file ~/data/individual.json
```

To query from MongoDB shell
```
use test
db.arraymap.find({'attributes.country.values.string_value' : 'United Kingdom'})
db.arraymap.find({'description' : {'$regex' : 'breast'}})
```
