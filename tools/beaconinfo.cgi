#!/usr/bin/perl

# Progenetix & arrayMap site scripts
# © 2000-2017 Michael Baudis: m@baud.is

use strict;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw(param);

use JSON;
use List::Util qw(sum);
use MongoDB;
use MongoDB::MongoClient;
use Data::Dumper;

=pod

Please see the associated beaconresponse.md
=cut

my $beaconId    =   'progenetix-beacon';
my $url         =   'http://progenetix.org/beacon/info/';
my $altUrl      =   'http://arraymap.org/beacon/info/';
my $logoUrl     =   'http://progenetix.org/p/progenetix.png';
my $actions     =   [];
my $provider    =   [
  'Michael Baudis',
  'Theoretical Cytogenetics and Oncogenomics, Department of Molecular Life Sciences, University of Zurich',
  'http://www.imls.uzh.ch/en/research/baudis.html',
  'http://wiki.progenetix.org/Wiki/BaudisgroupIMLS/MichaelBaudis',
  'Swiss Institute of Bioinformatics - SIB',
  'http://www.sib.swiss/baudis-michael',
];
my $description =   'A forward looking implementation for Beacon+ development, with focus on structural variants and metadata. For more information, please visit https://github.com/progenetix/arraymap2ga4gh/blob/master/tools/beaconresponse.md';


my $dbClient    =   MongoDB::MongoClient->new();
my @dbList      =   grep{ /_ga4gh/ } $dbClient->database_names();

if (! -t STDIN) { print 'Content-type: application/json'."\n\n" }

my $beaconInfo  =   {
  beaconId      =>  $beaconId,
  provider      =>  $provider,
  description   =>  $description,
  url           =>  $url,
  sameAs        =>  $altUrl,
  logo          =>  $logoUrl,
  potentialActions      =>  $actions,
  dataset       =>  [],
};

my %allRefs;

foreach my $db (@dbList) {

  my $datasetId =   $db;
  $datasetId    =~  s/_ga4gh$//i;
  my %datasetRefs;
  my $dbconn    =   $dbClient->get_database( $db );
  my @collList  =   grep{ ! /system/ } $dbconn->collection_names();
  my $collInfos =   [];
  my $varNo     =   0;
#  my $callNo    =   0;

  foreach (@collList) {

    my $docNo   =   $dbconn->get_collection($_)->count;
    push(
      @$collInfos,
      { $_ => { count => $docNo } },
    );

    if ( $_ =~ /^*._(((grch)|(hg))\d\d)$/i ) {
      $allRefs{$1}      =   1;
      $datasetRefs{$1}  =   1;
    }

    if ( $_ =~ /variants/i ) {
      $varNo    += $docNo;
    }

  }

  ##############################################################################

  my $dbCall =   $dbconn->run_command([
                  "distinct"=>  "biosamples",
                  "key"     =>  'bio_characteristics.ontology_terms.term_id',
                  "query"   =>  {},
                ]);

  my $bsOntologyTermIds =   $dbCall->{values};

  ##############################################################################

  push(
    @{ $beaconInfo->{dataset} },
    {
      identifier        => 'org.progenetix:'.$beaconId.':'.$datasetId,
      dataset_id        => $datasetId,
      name              => $datasetId,
      info              => { collections => $collInfos, ontology_terms => $bsOntologyTermIds },
      assemblyId        => [ keys %datasetRefs ],
      variantCount      => $varNo,
#      callCount         => $callNo,
    }
  );

}

$beaconInfo->{supportedRefs}    =   [ keys %allRefs ];



print JSON::XS->new->pretty( 1 )->allow_blessed->convert_blessed->encode($beaconInfo);

print ."\n";

exit;

1;
