use pyo3::prelude::*;

use crate::intersect_data_structures::PyExperimentFeatureData;
use exp_viz::intersect_coverage_data_features as icdf;

#[pyfunction]
pub fn intersect_coverage_data_features(
    data: Vec<PyExperimentFeatureData>,
) -> PyResult<PyExperimentFeatureData> {
    let intersected_features = icdf(data.into_iter().map(|c| c.to_feature_data()).collect());
    Ok(PyExperimentFeatureData {
        sources: intersected_features.sources,
        targets: intersected_features.targets,
    })
}
