use pyo3::prelude::*;

use crate::filter_data_structures::*;
use crate::intersect_data_structures::PyExperimentFeatureData;
use cov_viz_ds::ExperimentFeatureData;
use exp_viz::filter_coverage_data as fcd;

#[pyfunction]
pub fn filter_coverage_data(
    filters: &PyFilter,
    data: &PyCoverageData,
    included_features: Option<&PyExperimentFeatureData>,
) -> PyResult<PyFilteredData> {
    let filtered_data = if let Some(included_features) = included_features {
        let i_f: ExperimentFeatureData = included_features.to_feature_data();
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
    included_features: Option<&PyExperimentFeatureData>,
) -> PyResult<PyFilteredData> {
    py.allow_threads(|| filter_coverage_data(filters, data, included_features))
}
