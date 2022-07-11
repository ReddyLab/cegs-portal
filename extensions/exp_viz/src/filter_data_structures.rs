use std::collections::HashSet;

use crate::data_structures::{CoverageData, DbID};
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
    pub discrete_facets: HashSet<DbID>,
    #[pyo3(get, set)]
    pub continuous_intervals: Option<FilterIntervals>,
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
