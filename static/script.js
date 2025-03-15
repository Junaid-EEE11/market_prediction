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

    const prediction = document.getElementById("predict-btn");
    prediction.addEventListener("click", function (event) {
    event.preventDefault(); // Prevent default form submission

    const formDatas = new FormData(form);
    const data = {};

    // Convert FormData to JSON
    formDatas.forEach((value, key) => {
        data[key] = value;
    });

    // Collect fuel types as an array
    data["fuel-types"] = Array.from(document.querySelectorAll('input[name="fuel-type"]:checked'))
                               .map(checkbox => checkbox.value);


    // Fetch request with correct headers
    fetch('/predict-price', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json()).catch(error => console.error("Error:", error))
    .then(response => {
        const predictSection = document.getElementById("prediction-section");
        const tableBody = document.getElementById("prediction-table-body");

        // Clear previous results
        tableBody.innerHTML = "";

        for (let model in response) {
            let row = `<tr>
                          <td>${model}</td>
                          <td>${response[model].toLocaleString()}</td>
                      </tr>`;
            tableBody.innerHTML += row;
        }

        predictSection.style.display = "block"; // Show results
    })
    .catch(error => console.error("Error:", error));
});

    const logout = document.getElementById("logout-car");
    logout.addEventListener("click", function (event) {
    event.preventDefault(); // Prevent default form submission
    fetch('/signout')
.then(response=>response.json())
.then(data => {
      if (data.success) {window.location.href='/';}
    else {alert(data.msg)};
});
});

});