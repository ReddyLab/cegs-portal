mod filter;
mod filter_data_structures;
mod load;
mod merge;
mod set_ops;

use filter_data_structures::PySetOpFeature;
use pyo3::prelude::*;

use crate::filter::{filter_coverage_data, filter_coverage_data_allow_threads};
use crate::filter_data_structures::{PyFilter, PyFilterIntervals, PyFilteredData};
use crate::load::{
    load_coverage_data, load_coverage_data_allow_threads, load_feature_data,
    load_feature_data_allow_threads,
};
use crate::merge::merge_filtered_data;
use crate::set_ops::PyExperimentFeatureData;

/// A Python module implemented in Rust.
#[pymodule]
fn exp_viz(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(load_coverage_data, m)?)?;
    m.add_function(wrap_pyfunction!(load_coverage_data_allow_threads, m)?)?;
    m.add_function(wrap_pyfunction!(load_feature_data, m)?)?;
    m.add_function(wrap_pyfunction!(load_feature_data_allow_threads, m)?)?;
    m.add_function(wrap_pyfunction!(filter_coverage_data, m)?)?;
    m.add_function(wrap_pyfunction!(filter_coverage_data_allow_threads, m)?)?;
    m.add_function(wrap_pyfunction!(merge_filtered_data, m)?)?;
    m.add_class::<PyExperimentFeatureData>()?;
    m.add_class::<PyFilter>()?;
    m.add_class::<PyFilterIntervals>()?;
    m.add_class::<PyFilteredData>()?;
    m.add_class::<PySetOpFeature>()?;
    Ok(())
}
