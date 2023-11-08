use pyo3::prelude::*;

use crate::filter_data_structures::*;
use crate::intersect_data_structures::PyIncludedFeatures;
use exp_viz::filter_coverage_data as fcd;
use exp_viz::IncludedFeatures;

#[pyfunction]
pub fn filter_coverage_data(
    filters: &PyFilter,
    data: &PyCoverageData,
    included_features: Option<&PyIncludedFeatures>,
) -> PyResult<PyFilteredData> {
    let filtered_data = if let Some(included_features) = included_features {
        let i_f: IncludedFeatures = included_features.to_included_features();
        fcd(&filters.as_filter(), &data.wraps, Some(&i_f))
    } else {
        fcd(&filters.as_filter(), &data.wraps, None)
    };

    Ok(PyFilteredData { filtered_data })
}

#[pyfunction]
pub fn filter_coverage_data_allow_threads(
    py: Python<'_>,
    filters: &PyFilter,
    data: &PyCoverageData,
    included_features: Option<&PyIncludedFeatures>,
) -> PyResult<PyFilteredData> {
    py.allow_threads(|| filter_coverage_data(filters, data, included_features))
}
