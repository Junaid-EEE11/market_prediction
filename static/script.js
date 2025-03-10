function checkOption(selectElement) {
  const otherInput = document.getElementById(
    `otherInput${selectElement.dataset.index}`
  );

  if (selectElement.value === selectElement.dataset.type) {
    otherInput.style.display = "block";
    otherInput.required = true;
    otherInput.setAttribute("name",selectElement.dataset.type);
  } else {
    otherInput.style.display = "none";
    otherInput.required = false;
    otherInput.removeAttribute("name");

  }
  if (selectElement.dataset.index === "1") {
    document.getElementById(`otherInput2`).style.display = "none";
    document.getElementById(`otherInput2`).removeAttribute("name");
    document.getElementById(`otherInput3`).removeAttribute("name");
    document.getElementById(`otherInput3`).style.display = "none";
  }
};


document.addEventListener("DOMContentLoaded", function () {
    const brandSelect = document.getElementById("brand");
    const modelSelect = document.getElementById("model");
    const bodySelect = document.getElementById("body");
    const areaSelect = document.getElementById("area");

    fetch('/get-brands')
        .then(res => res.json())
        .then(data => data.brands.forEach(brand => addOption(brandSelect, brand)))
        .catch(error => console.error("Error fetching brands:", error));

    fetch('/get-area')
        .then(res => res.json())
        .then(data => data.areas.forEach(area => addOption(areaSelect, area)))
        .catch(error => console.error("Error fetching areas:", error));

    brandSelect.addEventListener("change", function () {
        const brand = this.value;
        modelSelect.innerHTML = '<option value="">Select Model</option><option value="model">Other</option>';
        bodySelect.innerHTML = '<option value="">Select Body</option><option value="body">Other</option>';

        if (brand) {
            fetch(`/get-models-body?brand=${brand}`)
                .then(res => res.json())
                .then(data => {
                    data.models.forEach(model => addOption(modelSelect, model));
                    data.body_types.forEach(body => addOption(bodySelect, body));

                })
                .catch(error => console.error("Error fetching models/bodies:", error));
        }
    });
    const form = document.getElementById("car-data-form");
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
                data[key] = value;
            });
        data["fuel-types"] = Array.from(document.querySelectorAll('input[name="fuel-type"]:checked'))
                                 .map(checkbox => checkbox.value);
console.log(data);
        fetch('/submit-entry', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => alert(result.message))
        .catch(error => alert("There was an error submitting the form."));
    });
function addOption(select, value) {
        let option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
};
});
