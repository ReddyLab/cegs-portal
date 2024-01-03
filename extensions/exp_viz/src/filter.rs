use pyo3::prelude::*;

use crate::filter_data_structures::*;
use crate::set_ops::PyExperimentFeatureData;
use exp_viz::filter_coverage_data as fcd;

#[pyfunction]
pub fn filter_coverage_data(
    filters: &PyFilter,
    data: &PyCoverageData,
    included_features: &PyExperimentFeatureData,
) -> PyResult<PyFilteredData> {
    let filtered_data = fcd(&filters.as_filter(), &data.wraps, &included_features.data);

    Ok(PyFilteredData { filtered_data })
}

#[pyfunction]
pub fn filter_coverage_data_allow_threads(
    py: Python<'_>,
    filters: &PyFilter,
    data: &PyCoverageData,
    included_features: &PyExperimentFeatureData,
) -> PyResult<PyFilteredData> {
    py.allow_threads(|| filter_coverage_data(filters, data, included_features))
}
