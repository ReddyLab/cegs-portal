use rustc_hash::FxHashSet;

use cov_viz_ds::{CoverageData, DbID};
use exp_viz::{Filter, FilterIntervals, FilteredBucket, FilteredChromosome, FilteredData};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Wraps the coverage data type so it can be passed to Python
#[pyclass(name = "CoverageData")]
pub struct PyCoverageData {
    pub wraps: CoverageData,
}

#[pyclass(name = "Filter")]
#[derive(Debug)]
pub struct PyFilter {
    #[pyo3(get, set)]
    pub discrete_facets: FxHashSet<DbID>,
    #[pyo3(get, set)]
    pub continuous_intervals: Option<PyFilterIntervals>,
}

#[pymethods]
impl PyFilter {
    #[new]
    pub fn new() -> Self {
        PyFilter {
            discrete_facets: FxHashSet::default(),
            continuous_intervals: None,
        }
    }

    pub fn __str__(&self) -> String {
        format!("Discrete Effects: {:?}", self.discrete_facets)
    }
}

impl PyFilter {
    pub fn as_filter(&self) -> Filter {
        Filter {
            discrete_facets: self.discrete_facets.clone(),
            continuous_intervals: self.continuous_intervals.map(|ci| ci.as_filter_intervals()),
        }
    }
}

#[pyclass(name = "FilterIntervals")]
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct PyFilterIntervals {
    #[pyo3(get, set)]
    pub effect: (f32, f32),
    #[pyo3(get, set)]
    pub sig: (f32, f32),
}

#[pymethods]
impl PyFilterIntervals {
    #[new]
    pub fn new() -> Self {
        PyFilterIntervals {
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

impl PyFilterIntervals {
    fn as_filter_intervals(&self) -> FilterIntervals {
        FilterIntervals {
            effect: self.effect,
            sig: self.sig,
        }
    }

    fn from_filter_intervals(fi: &FilterIntervals) -> PyFilterIntervals {
        PyFilterIntervals {
            effect: fi.effect,
            sig: fi.sig,
        }
    }
}

#[pyclass(name = "FilteredChromosome")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PyFilteredChromosome {
    pub chrom: String,
    pub index: u8,
    pub bucket_size: u32,
    pub target_intervals: Vec<FilteredBucket>,
    pub source_intervals: Vec<FilteredBucket>,
}

impl PyFilteredChromosome {
    fn from_filtered_chromosome(fc: &FilteredChromosome) -> Self {
        PyFilteredChromosome {
            chrom: fc.chrom.clone(),
            index: fc.index,
            bucket_size: fc.bucket_size,
            target_intervals: fc.target_intervals.clone(),
            source_intervals: fc.source_intervals.clone(),
        }
    }
}

#[pyclass(name = "FilteredData")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PyFilteredData {
    #[pyo3(get, set)]
    pub chromosomes: Vec<PyFilteredChromosome>,
    #[pyo3(get, set)]
    pub continuous_intervals: PyFilterIntervals,
    #[pyo3(get, set)]
    pub item_counts: [u64; 3],
}

impl PyFilteredData {
    pub fn from(data: &CoverageData) -> Self {
        PyFilteredData {
            chromosomes: data
                .chromosomes
                .iter()
                .map(|c| PyFilteredChromosome {
                    chrom: c.chrom.clone(),
                    index: c.index,
                    bucket_size: c.bucket_size,
                    target_intervals: Vec::new(),
                    source_intervals: Vec::new(),
                })
                .collect(),
            continuous_intervals: PyFilterIntervals::new(),
            item_counts: [0, 0, 0],
        }
    }

    pub fn from_filtered_data(data: &FilteredData) -> Self {
        PyFilteredData {
            chromosomes: data
                .chromosomes
                .iter()
                .map(|c| PyFilteredChromosome::from_filtered_chromosome(c))
                .collect(),
            continuous_intervals: PyFilterIntervals::from_filter_intervals(
                &data.continuous_intervals,
            ),
            item_counts: data.item_counts,
        }
    }
}

#[pymethods]
impl PyFilteredData {
    pub fn to_json(&self) -> PyResult<String> {
        serde_json::to_string(self).map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }
}
