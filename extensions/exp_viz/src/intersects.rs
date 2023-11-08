use pyo3::prelude::*;

use crate::filter_data_structures::*;
use crate::intersect_data_structures::PyIncludedFeatures;
use exp_viz::intersect_coverage_data_features as icdf;

#[pyfunction]
pub fn intersect_coverage_data_features(data: Vec<PyCoverageData>) -> PyResult<PyIncludedFeatures> {
    let intersected_features = icdf(data.into_iter().map(|c| c.wraps).collect());
    println!("{:?}", intersected_features);
    Ok(PyIncludedFeatures {
        sources: intersected_features.0,
        targets: intersected_features.1,
    })
}
