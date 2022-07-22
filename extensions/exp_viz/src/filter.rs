use std::time::Instant;

use pyo3::prelude::*;
use rustc_hash::FxHashSet;

use cov_viz_ds::{DbID, FacetCoverage, FacetRange};
use crate::filter_data_structures::*;

fn is_disjoint(a: &Vec<DbID>, b: &Vec<DbID>) -> bool {
    for val_a in a {
        for val_b in b {
            if val_a == val_b {
                return false
            }
        }
    }

    true
}

#[pyfunction]
pub fn filter_coverage_data(filters: &Filter, data: &PyCoverageData) -> PyResult<FilteredData> {
    let now = Instant::now();
    let data = &data.wraps;

    let mut new_data = FilteredData::from(data);

    let skip_disc_facet_check = filters.discrete_facets.is_empty();
    let skip_cont_facet_check = filters.continuous_intervals.is_none();

    let effect_size_interval = match &filters.continuous_intervals {
        Some(c) => FacetRange(c.effect.0, c.effect.1),
        None => data
            .facets
            .iter()
            .find(|f| f.name == "Effect Size")
            .unwrap()
            .range
            .unwrap(),
    };
    let sig_interval = match &filters.continuous_intervals {
        Some(c) => FacetRange(c.sig.0, c.sig.1),
        None => data
            .facets
            .iter()
            .find(|f| f.name == "Significance")
            .unwrap()
            .range
            .unwrap(),
    };

    let mut source_facets: Vec<FxHashSet<DbID>> = Vec::new();
    for facet in data.facets.iter().filter(|f| {
        f.facet_type == "FacetType.DISCRETE"
            && f.coverage
                .as_ref()
                .unwrap()
                .contains(&FacetCoverage::Source)
    }) {
        source_facets.push(FxHashSet::from_iter(
            facet.values.as_ref().unwrap().keys().map(|k| *k),
        ));
    }

    let mut target_facets: Vec<FxHashSet<DbID>> = Vec::new();
    for facet in data.facets.iter().filter(|f| {
        f.facet_type == "FacetType.DISCRETE"
            && f.coverage
                .as_ref()
                .unwrap()
                .contains(&FacetCoverage::Target)
    }) {
        target_facets.push(FxHashSet::from_iter(
            facet.values.as_ref().unwrap().keys().map(|k| *k),
        ));
    }

    let sf_with_selections: Vec<&FxHashSet<DbID>> = source_facets
        .iter()
        .filter(|f| !f.is_disjoint(&filters.discrete_facets))
        .collect();
    let tf_with_selections: Vec<&FxHashSet<DbID>> = target_facets
        .iter()
        .filter(|f| !f.is_disjoint(&filters.discrete_facets))
        .collect();

    let selected_sf: Vec<Vec<DbID>> = sf_with_selections
        .iter()
        .map(|f| (*f & &filters.discrete_facets).into_iter().collect())
        .collect();
    let selected_tf: Vec<Vec<DbID>> = tf_with_selections
        .iter()
        .map(|f| (*f & &filters.discrete_facets).into_iter().collect())
        .collect();

    let mut min_effect = f32::INFINITY;
    let mut max_effect = f32::NEG_INFINITY;

    let mut min_sig = f32::INFINITY;
    let mut max_sig = f32::NEG_INFINITY;

    for (c, chromosome) in data.chromosomes.iter().enumerate() {
        let mut chrom_data = new_data.chromosomes.get_mut(c).unwrap();
        let bucket_list = BucketList::new(&data.chrom_lengths, chromosome.bucket_size as usize);
        if skip_cont_facet_check && sf_with_selections.is_empty() {
            // do no filtering
            chrom_data.source_intervals = chromosome
                .source_intervals
                .iter()
                .map(|i| {
                    let interval = &i.values;
                    FilteredBucket {
                        start: i.start,
                        count: interval.len(),
                        associated_buckets: interval
                            .iter()
                            .fold(FxHashSet::default(), |mut acc, f| {
                                for bucket in &f.associated_buckets {
                                    acc.insert(*bucket);
                                }

                                acc
                            })
                            .iter()
                            .fold(Vec::new(), |mut acc, b| {
                                acc.push(b.0 as u32);
                                acc.push(b.1);

                                acc
                            }),
                    }
                })
                .collect();
        } else {
            for interval in &chromosome.source_intervals {
                let sources = &interval.values;
                let mut new_source_count: usize = 0;
                let mut new_target_buckets = bucket_list.clone();

                for source in sources {
                    let mut new_regeffects = false;
                    for facet in &source.facets {
                        if skip_disc_facet_check
                            || selected_sf.iter().all(|sf| !is_disjoint(&facet.0, sf))
                        {
                            min_effect = facet.1.min(min_effect);
                            max_effect = facet.1.max(max_effect);
                            min_sig = facet.2.min(min_sig);
                            max_sig = facet.2.max(max_sig);

                            if !new_regeffects && (skip_cont_facet_check
                                || (facet.1 >= effect_size_interval.0
                                    && facet.1 <= effect_size_interval.1
                                    && facet.2 >= sig_interval.0
                                    && facet.2 <= sig_interval.1))
                            {
                                new_regeffects = true;
                            }
                        }
                    }
                    if new_regeffects {
                        new_target_buckets.insert_from(&source.associated_buckets);
                        new_source_count += 1;
                    }
                }

                if new_source_count > 0 {
                    chrom_data.source_intervals.push(FilteredBucket {
                        start: interval.start,
                        count: new_source_count,
                        associated_buckets: new_target_buckets.flat_list(),
                    })
                }
            }
        }

        if skip_cont_facet_check && tf_with_selections.is_empty() {
            // do no filtering
            chrom_data.target_intervals = chromosome
                .target_intervals
                .iter()
                .map(|i| {
                    let interval = &i.values;
                    FilteredBucket {
                        start: i.start,
                        count: interval.len(),
                        associated_buckets: interval
                            .iter()
                            .fold(FxHashSet::default(), |mut acc, f| {
                                for bucket in &f.associated_buckets {
                                    acc.insert(*bucket);
                                }

                                acc
                            })
                            .iter()
                            .fold(Vec::new(), |mut acc, b| {
                                acc.push(b.0 as u32);
                                acc.push(b.1);

                                acc
                            }),
                    }
                })
                .collect();
        } else {
            for interval in &chromosome.target_intervals {
                let targets = &interval.values;
                let mut new_target_count: usize = 0;
                let mut new_source_buckets = bucket_list.clone();

                for target in targets {
                    let mut new_regeffects = false;
                    for facet in &target.facets {
                        if skip_disc_facet_check
                            || selected_tf.iter().all(|tf| !is_disjoint(&facet.0, tf))
                        {
                            min_effect = facet.1.min(min_effect);
                            max_effect = facet.1.max(max_effect);
                            min_sig = facet.2.min(min_sig);
                            max_sig = facet.2.max(max_sig);

                            if !new_regeffects && (skip_cont_facet_check
                                || (facet.1 >= effect_size_interval.0
                                    && facet.1 <= effect_size_interval.1
                                    && facet.2 >= sig_interval.0
                                    && facet.2 <= sig_interval.1))
                            {
                                new_regeffects = true;
                            }
                        }
                    }
                    if new_regeffects {
                        new_source_buckets.insert_from(&target.associated_buckets);
                        new_target_count += 1;
                    }
                }

                if new_target_count > 0 {
                    chrom_data.target_intervals.push(FilteredBucket {
                        start: interval.start,
                        count: new_target_count,
                        associated_buckets: new_source_buckets.flat_list(),
                    })
                }
            }
        }
    }

    min_effect = if min_effect == f32::INFINITY {
        effect_size_interval.0
    } else {
        min_effect
    };
    max_effect = if max_effect == f32::NEG_INFINITY {
        effect_size_interval.1
    } else {
        max_effect
    };

    min_sig = if min_sig == f32::INFINITY {
        sig_interval.0
    } else {
        min_sig
    };
    max_sig = if max_sig == f32::NEG_INFINITY {
        sig_interval.1
    } else {
        max_sig
    };

    new_data.continuous_intervals = FilterIntervals {
        effect: (min_effect, max_effect),
        sig: (min_sig, max_sig),
    };

    println!("Time to filter data: {}ms", now.elapsed().as_millis());
    Ok(new_data)
}
