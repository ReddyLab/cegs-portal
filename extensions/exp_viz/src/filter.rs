use pyo3::prelude::*;

use crate::filter_data_structures::*;
use exp_viz::filter_coverage_data as fcd;

#[pyfunction]
pub fn filter_coverage_data(filters: &PyFilter, data: &PyCoverageData) -> PyResult<PyFilteredData> {
    let filtered_data = fcd(&filters.as_filter(), &data.wraps);
    Ok(PyFilteredData::from_filtered_data(&filtered_data))
}

#[pyfunction]
pub fn filter_coverage_data_allow_threads(
    py: Python<'_>,
    filters: &PyFilter,
    data: &PyCoverageData,
) -> PyResult<PyFilteredData> {
    py.allow_threads(|| filter_coverage_data(filters, data))
}
