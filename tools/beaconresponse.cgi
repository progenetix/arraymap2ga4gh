#!/usr/bin/perl

# Progenetix & arrayMap site scripts
# © 2000-2017 Michael Baudis: m@baud.is

use strict;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw(param);

use JSON;
use List::Util qw(min max);
use MongoDB;
use MongoDB::MongoClient;
use Data::Dumper;

=pod

Please see the associated beaconresponse.md
=cut

if (! -t STDIN) { print 'Content-type: application/json'."\n\n" }

my $response    =   {
  beaconId      =>  "org.progenetix:progenetix-beacon",
  name          =>  'progenetix-beacon',
  url           =>  'http://progenetix.org/beacon/info/',
  version       =>  'Beacon+ implementation based on a development branch of the beacon-team project: https://github.com/ga4gh/beacon-team/pull/94',
};

my $args        =   {};

$args->{datasetPar}     =   _getDatasetParams();

# GA4GH variant attributes

$args->{varQpar}        =   _getVariantParams();
$args->{varQpar}        =   _normVariantParams($args->{varQpar});
$args->{varQ}           =   _createVariantQuery($args->{varQpar});

$args->{biosQpar}       =   _getBiosampleParams();
$args->{biosQ}          =   _createBiosampleQuery($args->{biosQpar});

# catching input errors #######################################################

# TODO: expand ...
$args->{errorM}         =   _checkParameters($args->{varQpar});

$args->{queryScope}     =   'datasetAlleleResponses';
$args->{queryType}      =   'alleleRequest';
if ($args->{varQpar}->{variant_type} =~ /^D(?:UP)|(?:EL)$/i) {
  $args->{datasetPar}->{varcoll}        =~  s/_alleles_/_cnv_/;
  $args->{datasetPar}->{callsetcoll}    =~  s/_alleles_/_cnv_/;
}

###############################################################################

$response->{datasets}   =   _getDatasetResponses($args);

print JSON::XS->new->pretty( 1 )->allow_blessed->convert_blessed->canonical()->encode($response);

print ."\n";

exit;

###############################################################################
###############################################################################
###############################################################################


################################################################################
# SUBs #########################################################################
################################################################################

sub _getDatasetParams {

  my $qPar      =   {};

  my %defaults  =   (
    varcoll     =>  'variants_alleles',
    callsetcoll =>  'callsets_alleles',
  );

  $qPar->{samplecoll}   =   param('samplecoll');
  if ($qPar->{samplecoll} !~ /^\w{3,64}$/) { $qPar->{samplecoll} = 'biosamples' }

  $qPar->{phenotypes}   =   param('phenotypes');
  if ($qPar->{phenotypes} =~ /^(?:y(?:es)?)|1$/i) { $qPar->{phenotypes} = 1 }

  $qPar->{dataset_id}   =   param('dataset_id');
  if ($qPar->{dataset_id} !~ /^\w{3,64}$/) { $qPar->{dataset_id} = 'arraymap' }

  $qPar->{assembly_id}  =   param('assembly_id');
  if ($qPar->{assembly_id} !~ /^\w{3,64}$/) { $qPar->{assembly_id} = 'GRCh36' }

  foreach (keys %defaults) {

    $qPar->{$_} =   param($_);
    if ($qPar->{$_} !~ /^\w{3,64}$/) { $qPar->{$_} = $defaults{$_} }
    $qPar->{$_} .=   '_'.lc($qPar->{assembly_id});

  }

  $qPar->{dataset_ids}  =   [ param('dataset_ids')];
  if ($qPar->{dataset_ids}->[0] !~ /\w\w\w/) { push(@{$qPar->{dataset_ids}}, $qPar->{dataset_id})}

  return $qPar;

}

################################################################################

sub _getBiosampleParams {

=pod

Atributes not used (yet):

=cut

  my $qPar      =   {};

  foreach (qw(
    id
    bio_characteristics.ontology_terms.term_id
  )) { $qPar->{$_}      =   [ param('biosamples.'.$_) ] }

  return $qPar;

}

################################################################################

sub _getVariantParams {

=pod

Atributes not used (yet):
  variant_set_id
  svlen
  filters_applied
  filters_passed

  cipos
  ciend

=cut

  my $qPar      =   {};

# TODO: Implement alternate_bases as list

  foreach (qw(
    id
    reference_name
    reference_bases
    alternate_bases
    variant_type
    start
    end
    start_min
    start_max
    end_min
    end_max
  )) { $qPar->{$_}      =   param('variants.'.$_) }

  foreach (qw(
  )) { $qPar->{$_}      =   [ sort {$a <=> $b } (param('variants.'.$_)) ] }

  #print Dumper $qPar;

  return $qPar;

}

################################################################################

sub _normVariantParams {

  my $qPar      =   $_[0];


  # creating the intervals for range queries, while checking for right order
  # this also fills in min = max if only one parameter has been for start or
  # end, respectively
  foreach my $side (qw(start end)) {

    my $parKeys =   [ grep{ /^$side(?:_m(?:(?:in)|(?:ax)))?$/ } keys %$qPar ];
    my $parVals =   [ grep{ /^\d+?$/ } @{ $qPar }{ @$parKeys } ];
    $qPar->{$side.'_range'}     =  [ min(@$parVals), max(@$parVals) ];

  }

  $qPar->{reference_name} =~  s/chr?o?//i;

  return $qPar;

}

################################################################################

sub _checkParameters {

  my $qPar      =   $_[0];

  my $args->{errorM};

  if (
    $qPar->{variant_type} =~ /^D(?:UP)|(?:EL)$/
    &&
    (
    $qPar->{start_range}->[0] !~ /^\d+?$/
    ||
    $qPar->{end_range}->[0] !~ /^\d+?$/
    )
  ) {
    $args->{errorM}     .=    '"variants.start" (and also start_min, start_max) or "variants.end" (and also end_min, end_max) did not contain a numeric value. ';
  }

  if ($qPar->{reference_name} !~ /^(?:(?:(?:1|2)?\d)|x|y)$/i) {
    $args->{errorM}     .=    '"variants.reference_name" did not contain a valid value (e.g. "chr17" "8", "X"). ';
  }

  if (
  ($qPar->{variant_type} !~ /^D(?:UP)|(?:EL)$/)
  &&
  ($qPar->{alternate_bases} !~ /^[ATGC]+?$/)
  ) {
    $args->{errorM}     .=    'There was no valid value for either "variants.variant_type" or "variants.alternate_bases". ';
  }

  return $args->{errorM};

}

################################################################################

sub _createBiosampleQuery {

  my $qPar      =   $_[0];
  my @qList;

  foreach my $qKey (keys %{$qPar}) {

    my @thisQlist;

    foreach (grep{ /.../ } @{ $qPar->{$qKey} } ) {

      push(@thisQlist, { $qKey => $_ } );

    }

=pod

Queries with multiple options for the same attribute are treated as logical "OR".

=cut

  if (@thisQlist == 1)    { push(@qList, $thisQlist[0]) }
  elsif (@thisQlist > 1)  { push(@qList, {'$or' => [ @thisQlist ] } ) }

  }

=pod

The construction of the query object depends on the detected parameters:

* if empty list => no change, empty object
* if 1 parameter => direct use
* if several parameters are queried => connection through the MongoDB  "$and" constructor

=cut

  if (@qList == 1)    { return $qList[0] }
  elsif (@qList > 1)  { return { '$and' => \@qList } }
  else                { return {} }

}

################################################################################

sub _createVariantQuery {

  my $qPar      =   $_[0];
  my $qObj      =   {};

  if ($qPar->{variant_type} =~ /^D(?:UP)|(?:EL)$/) {

    $qObj       =   {
      '$and'    => [
        { reference_name        =>  $qPar->{reference_name} },
        { variant_type          =>  $qPar->{variant_type} },
        { start =>  { '$gte'  =>  1 * $qPar->{start_range}->[0] } },
        { start =>  { '$lte'  =>  1 * $qPar->{start_range}->[1] } },
        { end   =>  { '$gte'  =>  1 * $qPar->{end_range}->[0] } },
        { end   =>  { '$lte'  =>  1 * $qPar->{end_range}->[1] } },
      ],
    };

  } elsif ($qPar->{alternate_bases} =~ /^[ATGC]+?$/) {

    my @qList   =   (
      { reference_name  =>  $qPar->{reference_name} },
      { alternate_bases =>  $qPar->{alternate_bases} },
      { start =>  1 * $qPar->{start} },
    );

    if ($qPar->{reference_bases} =~ /^[ATCG]+?$/) {
      push(
        @qList,
        { reference_bases =>  $qPar->{reference_bases} },
      );
    }

    $qObj       =   {
      '$and' => \@qList,
    };

  }

  return $qObj;

}

################################################################################


sub _getDatasetResponses {

  my $args      =   shift;
  my $datasets  =   [];

  foreach (@{ $args->{datasetPar}->{dataset_ids} }) {

    push(
      @$datasets,
      _getDataset($args, $_),
    );

  }

  return $datasets;

}

################################################################################

sub _getDataset {

  my $args      =   shift;
  my $dataset   =   shift;
  my $counts    =   {};
  my $dbCall;             # recyclable
  my $db        =   $dataset.'_ga4gh';
  my $dbconn    =   MongoDB::MongoClient->new()->get_database( $db );

=pod

  The ids of biosamples matching (designated) metadata criteria are retrieved. This can be, as in the first example, biosamples with an "characteristic" containing a specific ontology term.

=cut

  # getting the number of all biosamples in the collection
  $dbCall         =   $dbconn->run_command({"count" => $args->{datasetPar}->{samplecoll}});

  $counts->{bs_all}       =   $dbCall->{n};

  # getting and  counting the ids of all biosamples which match the biosample query
  $dbCall         =   $dbconn->run_command([
                        "distinct"  =>  $args->{datasetPar}->{samplecoll},
                        "key"       =>  'id',
                        "query"     =>  $args->{biosQ},
                      ]);
  my $biosampleIds        =   $dbCall->{values};
  $counts->{bs_matched}   =   scalar(@{ $biosampleIds });

  ###############################################################################

  # counting all variants in the variant collection
  $dbCall         =   $dbconn->run_command({"count" => $args->{datasetPar}->{varcoll}});
  $counts->{var_all}      =   $dbCall->{n};

  # counting all callsets with any variant
  $dbCall =   $dbconn->run_command([
                "distinct"=>  $args->{datasetPar}->{varcoll},
                "key"     =>  'calls.call_set_id',
                "query"   =>  {},
              ]);
  $counts->{cs_all}       =   scalar(@{ $dbCall->{values} });

  # getting and  counting all callset ids with matching variants
  $dbCall =   $dbconn->run_command([
                "distinct"=>  $args->{datasetPar}->{varcoll},
                "key"     =>  'calls.call_set_id',
                "query"   =>  $args->{varQ},
              ]);
  my $callsetIds          =   $dbCall->{values};
  $counts->{cs_matched}   =   scalar(@{ $callsetIds });

  ###############################################################################

  # getting and counting all biosample ids from those callsets,
  # which are both fulfilling the biosample metadata query and are listed
  # in the matched callsets

  my $bsQvarQmatchedQ     =   {};
  my @bsQvarQlist         =   ();
  my $csBiosampleIds      =   [];

  if (grep{ /.../ } keys %{ $args->{biosQ} } ) {
    push(@bsQvarQlist, { biosample_id => { '$in' => $biosampleIds } } );
  }
  if (grep{ /.../ } keys %{ $args->{varQ} } ) {
    push(@bsQvarQlist, { id => { '$in' => $callsetIds } } );
  }

  if (@bsQvarQlist > 1) {
    $bsQvarQmatchedQ      =   { '$and' => [ @bsQvarQlist ] };
  } elsif (@bsQvarQlist == 1) {
    $bsQvarQmatchedQ      =   @bsQvarQlist[0];
  }

  # sanity check; if biosample query but no ids => no match

  if (
    (grep{ /.../ } keys %{ $args->{biosQ} } )
    &&
    ($counts->{bs_matched} < 1)
  ) {

    $csBiosampleIds       =   [];

  } else {

    $dbCall       =   $dbconn->run_command([
                        "distinct"=>  $args->{datasetPar}->{callsetcoll},
                        "key"     =>  'biosample_id',
                        "query"   =>  $bsQvarQmatchedQ,
                      ]);
    $csBiosampleIds       =   $dbCall->{values};

  }

  $counts->{bs_var_matched}       =   scalar(@{ $csBiosampleIds });

  $counts->{frequency}    =   'NA';
  if ($counts->{bs_all} > 0) {
    $counts->{frequency}  =   sprintf "%.4f",  $counts->{bs_var_matched} / $counts->{bs_all};
  }

  ################################################################################

  $dbCall =   $dbconn->run_command([
                "distinct"=>  $args->{datasetPar}->{samplecoll},
                "key"     =>  'bio_characteristics.ontology_terms.term_id',
                "query"   =>  { id =>  { '$in' => $csBiosampleIds } },
              ]);

  my $bsOntologyTermIds   =   $dbCall->{values};

  ################################################################################

  my $bsPhenotypeResponse =   [];

  if ($args->{datasetPar}->{phenotypes} > 0) {

    foreach my $ontoTerm (@$bsOntologyTermIds) {

      $dbCall     =   $dbconn->run_command([
                        "distinct"=>  $args->{datasetPar}->{samplecoll},
                        "key"     =>  'id',
                        "query"   =>  { 'bio_characteristics.ontology_terms.term_id' => $ontoTerm },
                      ]);
      my $ontoNo  =   scalar(@{ $dbCall->{values} });

      $dbCall   =   $dbconn->run_command([
                      "distinct"=>  $args->{datasetPar}->{samplecoll},
                      "key"     =>  'id',
                      "query"   =>  { '$and' => [
                                      { 'bio_characteristics.ontology_terms.term_id' => $ontoTerm },
                                      { id =>  { '$in' => $csBiosampleIds } },
                                    ] },
                    ]);
      my $ontoObs =   scalar(@{ $dbCall->{values} });

      push(
        @$bsPhenotypeResponse,
        {
          term_id           =>   $ontoTerm,
          count             =>   $ontoNo,
          observations      =>   $ontoObs,
        }
      );

  }}

  ################################################################################

  # TODO: The response has to be extended and also to be adapted to the "Dataset" option.
  return   {
    dataset     =>  $dataset,
    $args->{queryType}          =>  $args->{varQ},
    _debug_query_string         =>  $ENV{QUERY_STRING},
    info        =>  {
      ontology_ids      => $bsOntologyTermIds,
      phenotype_response=> $bsPhenotypeResponse,
      description       =>  'The query was against database "'.$db.'", variant collection "'.$args->{datasetPar}->{varcoll}.'". '.$counts->{cs_matched}.' / '.$counts->{cs_all}.' matched callsets for '.$counts->{var_all}.' variants. Out of '.$counts->{bs_all}.' biosamples in the database, '.$counts->{bs_matched}.' matched the biosample query; of those, '.$counts->{bs_var_matched}.' had the variant.',
    },
    biosampleRequest    =>  $args->{biosQ},
    $args->{queryScope} =>  1 * $counts->{bs_var_matched},
    frequency   =>  1 * $counts->{frequency},
    callCount   =>  $counts->{cs_matched},
    sampleCount =>  1 * $counts->{bs_var_matched},
    error       =>  $args->{errorM},
  };

}

1;
