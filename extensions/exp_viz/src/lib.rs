mod filter;
mod filter_data_structures;
mod load;
mod merge;

use pyo3::prelude::*;

use crate::filter::{filter_coverage_data, filter_coverage_data_allow_threads};
use crate::filter_data_structures::{PyFilter, PyFilterIntervals, PyFilteredData};
use crate::load::{load_coverage_data, load_coverage_data_allow_threads};
use crate::merge::merge_filtered_data;

/// A Python module implemented in Rust.
#[pymodule]
fn exp_viz(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(load_coverage_data, m)?)?;
    m.add_function(wrap_pyfunction!(load_coverage_data_allow_threads, m)?)?;
    m.add_function(wrap_pyfunction!(filter_coverage_data, m)?)?;
    m.add_function(wrap_pyfunction!(filter_coverage_data_allow_threads, m)?)?;
    m.add_function(wrap_pyfunction!(merge_filtered_data, m)?)?;
    m.add_class::<PyFilter>()?;
    m.add_class::<PyFilterIntervals>()?;
    m.add_class::<PyFilteredData>()?;
    Ok(())
}
