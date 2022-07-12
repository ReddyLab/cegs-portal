use rustc_hash::FxHashSet;

use crate::data_structures::{Bucket, CoverageData, DbID};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Wraps the coverage data type so it can be passed to Python
#[pyclass(name = "CoverageData")]
pub struct PyCoverageData {
    pub wraps: CoverageData,
}

#[pyclass]
pub struct Filter {
    #[pyo3(get, set)]
    pub discrete_facets: FxHashSet<DbID>,
    #[pyo3(get, set)]
    pub continuous_intervals: Option<FilterIntervals>,
}

#[pymethods]
impl Filter {
    #[new]
    pub fn new() -> Self {
        Filter {
            discrete_facets: FxHashSet::default(),
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
    pub effect: (f32, f32),
    #[pyo3(get, set)]
    pub sig: (f32, f32),
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
pub struct FilteredBucket {
    pub start: u32,
    pub count: usize,
    pub associated_buckets: Vec<u32>,
}

#[derive(Serialize, Deserialize)]
pub struct FilteredChromosome {
    pub chrom: String,
    pub bucket_size: u32,
    pub target_intervals: Vec<FilteredBucket>,
    pub source_intervals: Vec<FilteredBucket>,
}

#[derive(Serialize, Deserialize)]
#[pyclass]
pub struct FilteredData {
    pub chromosomes: Vec<FilteredChromosome>,
    pub continuous_intervals: FilterIntervals,
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

#[derive(Clone)]
pub struct BucketList {
    pub buckets: Vec<Vec<u32>>,
}

impl BucketList {
    pub fn new(chroms: &Vec<usize>, bucket_size: usize) -> Self {
        BucketList {
            buckets: chroms
                .iter()
                .map(|c| vec![0; (c / bucket_size) + 1])
                .collect(),
        }
    }

    pub fn insert(&mut self, chrom: usize, bucket: usize) {
        self.buckets[chrom][bucket] = 1;
    }

    pub fn insert_from<'a, I>(&mut self, from: I)
    where
        I: IntoIterator<Item = &'a Bucket>,
    {
        for bucket in from {
            self.insert(bucket.0, bucket.1 as usize);
        }
    }

    pub fn flat_list(&self) -> Vec<u32> {
        let mut new_list: Vec<u32> = Vec::new();
        for (i, chrom) in self.buckets.iter().enumerate() {
            for (j, bucket) in chrom.iter().enumerate() {
                if *bucket == 1 {
                    new_list.push(i as u32);
                    new_list.push(j as u32);
                }
            }
        }
        new_list
    }
}
