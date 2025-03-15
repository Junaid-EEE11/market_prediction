function openModal(modalId) {
  document.getElementById(modalId).style.display = "flex";
}
function closeModal(modalId) {
  document.getElementById(modalId).style.display = "none";
}
const signupform = document.getElementById("signup-form");
signupform.addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(signupform);
  const data = {};
  formData.forEach((value, key) => {
    data[key] = value;
  });
  fetch("/customer-register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then(response=>response.json())
.then(data => {
      if (data.success) {window.location.href='/';}
    else {alert(data.msg)};
});
});
const signinform = document.getElementById("signin-form");
signinform.addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(signinform);
  const data = {};
  formData.forEach((value, key) => {
    data[key] = value;
  });
  fetch("/signin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
.then(response=>response.json())
.then(data => {
      if (data.success) {window.location.href='/';}
    else {alert(data.msg)};
});
});
