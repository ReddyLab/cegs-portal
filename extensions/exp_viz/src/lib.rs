mod data_structures;

use std::collections::HashSet;
use std::path::PathBuf;
use std::time::Instant;

use pyo3::exceptions::{PyOSError, PyRuntimeError};
use pyo3::prelude::*;

use serde::{Deserialize, Serialize};

use data_structures::{Bucket, CoverageData, FacetCoverage, FacetRange};

type DbID = i64;

/// Wraps the coverage data type so it can be passed to Python
#[pyclass(name = "CoverageData")]
pub struct PyCoverageData {
    wraps: CoverageData,
}

/// Loads the coverage data from disk
#[pyfunction]
fn load_coverage_data(location: PathBuf) -> PyResult<PyCoverageData> {
    let now = Instant::now();
    let result = match CoverageData::deserialize(&location) {
        Ok(data) => Ok(PyCoverageData { wraps: data }),
        Err(e) => Err(PyOSError::new_err(e.to_string())),
    };
    println!("Time to decode: {}ms", now.elapsed().as_millis());

    result
}

#[pyclass]
pub struct Filter {
    #[pyo3(get, set)]
    discrete_facets: HashSet<DbID>,
    #[pyo3(get, set)]
    continuous_intervals: Option<FilterIntervals>,
}

#[pymethods]
impl Filter {
    #[new]
    pub fn new() -> Self {
        Filter {
            discrete_facets: HashSet::new(),
            continuous_intervals: None,
        }
    }

    pub fn __str__(&self) -> String {
        format!("Discrete Effects: {:?}", self.discrete_facets)
    }
}

#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FilterIntervals {
    #[pyo3(get, set)]
    effect: (f32, f32),
    #[pyo3(get, set)]
    sig: (f32, f32),
}

#[pymethods]
impl FilterIntervals {
    #[new]
    pub fn new() -> Self {
        FilterIntervals {
            effect: (f32::NEG_INFINITY, f32::INFINITY),
            sig: (f32::NEG_INFINITY, f32::INFINITY),
        }
    }

    pub fn __str__(&self) -> String {
        format!(
            "Effect Size: {:?}, Significance: {:?}",
            self.effect, self.sig
        )
    }
}

#[derive(Serialize, Deserialize)]
#[pyclass]
pub struct FilteredBucket {
    pub start: u32,
    pub count: usize,
    pub associated_buckets: Vec<u32>,
}

#[derive(Serialize, Deserialize)]
#[pyclass]
pub struct FilteredChromosome {
    pub chrom: String,
    pub bucket_size: u32,
    pub target_intervals: Vec<FilteredBucket>,
    pub source_intervals: Vec<FilteredBucket>,
}

#[derive(Serialize, Deserialize)]
#[pyclass]
pub struct FilteredData {
    chromosomes: Vec<FilteredChromosome>,
    continuous_intervals: FilterIntervals,
}

impl FilteredData {
    pub fn from(data: &CoverageData) -> Self {
        FilteredData {
            chromosomes: data
                .chromosomes
                .iter()
                .map(|c| FilteredChromosome {
                    chrom: c.chrom.clone(),
                    bucket_size: c.bucket_size,
                    target_intervals: Vec::new(),
                    source_intervals: Vec::new(),
                })
                .collect(),
            continuous_intervals: FilterIntervals::new(),
        }
    }
}

#[pymethods]
impl FilteredData {
    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self).map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }
}

#[pyfunction]
fn filter_coverage_data(filters: &Filter, data: &PyCoverageData) -> PyResult<FilteredData> {
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

    let mut source_facets: Vec<HashSet<DbID>> = Vec::new();
    for facet in data.facets.iter().filter(|f| {
        f.facet_type == "FacetType.DISCRETE"
            && f.coverage
                .as_ref()
                .unwrap()
                .contains(&FacetCoverage::Source)
    }) {
        source_facets.push(HashSet::from_iter(
            facet.values.as_ref().unwrap().keys().map(|k| *k),
        ));
    }

    let mut target_facets: Vec<HashSet<DbID>> = Vec::new();
    for facet in data.facets.iter().filter(|f| {
        f.facet_type == "FacetType.DISCRETE"
            && f.coverage
                .as_ref()
                .unwrap()
                .contains(&FacetCoverage::Target)
    }) {
        target_facets.push(HashSet::from_iter(
            facet.values.as_ref().unwrap().keys().map(|k| *k),
        ));
    }

    let sf_with_selections: Vec<&HashSet<DbID>> = source_facets
        .iter()
        .filter(|f| !f.is_disjoint(&filters.discrete_facets))
        .collect();
    let tf_with_selections: Vec<&HashSet<DbID>> = target_facets
        .iter()
        .filter(|f| !f.is_disjoint(&filters.discrete_facets))
        .collect();

    let selected_sf: Vec<HashSet<DbID>> = sf_with_selections
        .iter()
        .map(|f| *f & &filters.discrete_facets)
        .collect();
    let selected_tf: Vec<HashSet<DbID>> = tf_with_selections
        .iter()
        .map(|f| *f & &filters.discrete_facets)
        .collect();

    let mut min_effect = f32::INFINITY;
    let mut max_effect = f32::NEG_INFINITY;

    let mut min_sig = f32::INFINITY;
    let mut max_sig = f32::NEG_INFINITY;

    for (c, chromosome) in data.chromosomes.iter().enumerate() {
        let mut chrom_data = new_data.chromosomes.get_mut(c).unwrap();
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
                            .values()
                            .fold(HashSet::new(), |mut acc, f| {
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
                let mut new_target_buckets: HashSet<Bucket> = HashSet::new();

                for source in sources.values() {
                    let mut new_regeffects: u32 = 0;
                    for facet in &source.facets {
                        if skip_disc_facet_check
                            || selected_sf.len()
                                == selected_sf
                                    .iter()
                                    .filter(|sf| !sf.is_disjoint(&facet.0))
                                    .count()
                        {
                            min_effect = facet.1.min(min_effect);
                            max_effect = facet.1.max(max_effect);
                            min_sig = facet.2.min(min_sig);
                            max_sig = facet.2.max(max_sig);

                            if skip_cont_facet_check
                                || (facet.1 >= effect_size_interval.0
                                    && facet.1 <= effect_size_interval.1
                                    && facet.2 >= sig_interval.0
                                    && facet.2 <= sig_interval.1)
                            {
                                new_regeffects += 1;
                                new_target_buckets.extend(source.associated_buckets.iter());
                            }
                        }
                    }
                    if new_regeffects > 0 {
                        new_source_count += 1;
                    }
                }

                if new_source_count > 0 {
                    chrom_data.source_intervals.push(FilteredBucket {
                        start: interval.start,
                        count: new_source_count,
                        associated_buckets: new_target_buckets.iter().fold(
                            Vec::new(),
                            |mut acc, b| {
                                acc.push(b.0 as u32);
                                acc.push(b.1);

                                acc
                            },
                        ),
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
                            .values()
                            .fold(HashSet::new(), |mut acc, f| {
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
                let mut new_source_buckets: HashSet<Bucket> = HashSet::new();

                for target in targets.values() {
                    let mut new_regeffects: u32 = 0;
                    for facet in &target.facets {
                        if skip_disc_facet_check
                            || selected_tf.len()
                                == selected_tf
                                    .iter()
                                    .filter(|tf| !tf.is_disjoint(&facet.0))
                                    .count()
                        {
                            min_effect = facet.1.min(min_effect);
                            max_effect = facet.1.max(max_effect);
                            min_sig = facet.2.min(min_sig);
                            max_sig = facet.2.max(max_sig);

                            if skip_cont_facet_check
                                || (facet.1 >= effect_size_interval.0
                                    && facet.1 <= effect_size_interval.1
                                    && facet.2 >= sig_interval.0
                                    && facet.2 <= sig_interval.1)
                            {
                                new_regeffects += 1;
                                new_source_buckets.extend(target.associated_buckets.iter());
                            }
                        }
                    }
                    if new_regeffects > 0 {
                        new_target_count += 1;
                    }
                }

                if new_target_count > 0 {
                    chrom_data.target_intervals.push(FilteredBucket {
                        start: interval.start,
                        count: new_target_count,
                        associated_buckets: new_source_buckets.iter().fold(
                            Vec::new(),
                            |mut acc, b| {
                                acc.push(b.0 as u32);
                                acc.push(b.1);

                                acc
                            },
                        ),
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

/// A Python module implemented in Rust.
#[pymodule]
fn exp_viz(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(load_coverage_data, m)?)?;
    m.add_function(wrap_pyfunction!(filter_coverage_data, m)?)?;
    m.add_class::<Filter>()?;
    m.add_class::<FilterIntervals>()?;
    m.add_class::<FilteredData>()?;
    Ok(())
}
