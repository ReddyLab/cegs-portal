use rustc_hash::FxHashSet;

use cov_viz_ds::{CoverageData, DbID};
use exp_viz::{Filter, FilterIntervals, FilteredChromosome, FilteredData, SetOpFeature};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Wraps the coverage data type so it can be passed to Python
#[pyclass(name = "CoverageData")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PyCoverageData {
    pub wraps: CoverageData,
}

#[pymethods]
impl PyCoverageData {
    pub fn __str__(&self) -> String {
        format!("significant_observations: {}\nnonsignificant_observations: {}\nbucket_size: {}\nchromosomes: {}", self.wraps.significant_observations.len(), self.wraps.nonsignificant_observations.len(), self.wraps.bucket_size, self.wraps.chromosomes.len())
    }
}

#[pyclass(name = "SetOpFeature")]
#[derive(Clone, Debug)]
pub enum PySetOpFeature {
    Source,
    Target,
    SourceTarget,
}

impl PySetOpFeature {
    pub fn as_set_op_feature(&self) -> SetOpFeature {
        match self {
            PySetOpFeature::Source => SetOpFeature::Source,
            PySetOpFeature::Target => SetOpFeature::Target,
            PySetOpFeature::SourceTarget => SetOpFeature::SourceTarget,
        }
    }
}

#[pyclass(name = "Filter")]
#[derive(Debug)]
pub struct PyFilter {
    #[pyo3(get, set)]
    pub chrom: Option<u8>,
    #[pyo3(get, set)]
    pub categorical_facets: FxHashSet<DbID>,
    #[pyo3(get, set)]
    pub numeric_intervals: Option<PyFilterIntervals>,
    #[pyo3(get, set)]
    pub set_op_feature: Option<PySetOpFeature>,
}

#[pymethods]
impl PyFilter {
    #[new]
    pub fn new() -> Self {
        PyFilter {
            chrom: None,
            categorical_facets: FxHashSet::default(),
            numeric_intervals: None,
            set_op_feature: None,
        }
    }

    pub fn __str__(&self) -> String {
        format!("Categorical Effects: {:?}", self.categorical_facets)
    }
}

impl PyFilter {
    pub fn as_filter(&self) -> Filter {
        Filter {
            chrom: self.chrom,
            categorical_facets: self.categorical_facets.clone(),
            numeric_intervals: self.numeric_intervals.map(|ci| ci.as_filter_intervals()),
            set_op_feature: self.set_op_feature.as_ref().map(|x| x.as_set_op_feature()),
        }
    }
}

#[pyclass(name = "FilterIntervals")]
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct PyFilterIntervals {
    #[pyo3(get, set)]
    pub effect: (f32, f32),
    #[pyo3(get, set)]
    pub sig: (f64, f64),
}

#[pymethods]
impl PyFilterIntervals {
    #[new]
    pub fn new() -> Self {
        PyFilterIntervals {
            effect: (f32::NEG_INFINITY, f32::INFINITY),
            sig: (f64::NEG_INFINITY, f64::INFINITY),
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
}

#[derive(Debug, Serialize)]
pub struct FilteredJsonData {
    pub chromosomes: Vec<FilteredChromosome>,
    pub bucket_size: u32,
    pub numeric_intervals: FilterIntervals,
    pub reo_count: u64,
    pub source_count: u64,
    pub target_count: u64,
}

impl FilteredJsonData {
    fn from(from: &FilteredData) -> Self {
        FilteredJsonData {
            chromosomes: from.chromosomes.clone(),
            bucket_size: from.bucket_size,
            numeric_intervals: from.numeric_intervals,
            reo_count: from.reo_count,
            source_count: from.sources.len(),
            target_count: from.targets.len(),
        }
    }
}

#[pyclass(name = "FilteredData")]
#[derive(Clone, Debug)]
pub struct PyFilteredData {
    pub filtered_data: FilteredData,
}

#[pymethods]
impl PyFilteredData {
    pub fn to_json(&self) -> PyResult<String> {
        let json_data = FilteredJsonData::from(&self.filtered_data);
        serde_json::to_string(&json_data).map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }
}
