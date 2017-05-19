mongoimport --db test --collection biosamples --drop --file ./biosamples.json --jsonArray
mongoimport --db test --collection individuals --drop --file ./individuals.json --jsonArray
mongoimport --db test --collection callsets --drop --file ./callsets.json --jsonArray
mongoimport --db test --collection variants --drop --file ./variants.json --jsonArray