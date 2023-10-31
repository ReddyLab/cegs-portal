use pyo3::exceptions::PyOSError;
use pyo3::prelude::*;
use std::path::PathBuf;

use cov_viz_ds::CoverageData;

use crate::filter_data_structures::PyCoverageData;

/// Loads the coverage data from disk
#[pyfunction]
pub fn load_coverage_data(location: PathBuf) -> PyResult<PyCoverageData> {
    let result = match CoverageData::deserialize(&location) {
        Ok(data) => Ok(PyCoverageData { wraps: data }),
        Err(e) => Err(PyOSError::new_err(e.to_string())),
    };

    result
}

#[pyfunction]
pub fn load_coverage_data_allow_threads(
    py: Python<'_>,
    location: PathBuf,
) -> PyResult<PyCoverageData> {
    py.allow_threads(|| load_coverage_data(location))
}
