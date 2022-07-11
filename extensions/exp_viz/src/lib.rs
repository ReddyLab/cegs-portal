mod data_structures;
mod filter;
mod filter_data_structures;
mod load;

use pyo3::prelude::*;

use crate::filter::filter_coverage_data;
use crate::filter_data_structures::{Filter, FilterIntervals, FilteredData};
use crate::load::load_coverage_data;

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
