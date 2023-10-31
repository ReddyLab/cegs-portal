use pyo3::prelude::*;

use crate::filter_data_structures::*;
use exp_viz::{merge_filtered_data as mfd, FilteredData};

#[pyfunction]
pub fn merge_filtered_data(
    result_data: Vec<PyFilteredData>,
    chromosome_list: Vec<String>,
) -> PyResult<PyFilteredData> {
    let filtered_data: Vec<FilteredData> =
        result_data.into_iter().map(|f| f.filtered_data).collect();
    let merged_data = mfd(filtered_data, chromosome_list);

    Ok(PyFilteredData {
        filtered_data: merged_data,
    })
}
