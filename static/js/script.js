console.log("Website Scanner Loaded");

// Example alert
function showAlert(msg) {
    alert(msg);
}

// Make sure data exists
const data = data || []; // or replace with actual data source

// Get output container
const output = document.getElementById("output");

data.forEach(item => {
    let div = document.createElement("div");

    let color = "green";
    if (item.severity === "high") color = "red";
    else if (item.severity === "medium") color = "orange";

    div.className = "mini-card " + item.severity; // FIXED class
    div.style.borderColor = color;

    div.innerHTML = `
        <b>Type:</b> ${item.type} <br>
        <b>Severity:</b> ${item.severity} <br>
        ${item.port ? `<b>Port:</b> ${item.port}<br>` : ""}
        ${item.service ? `<b>Service:</b> ${item.service}<br>` : ""}
        ${item.issue ? `<b>Issue:</b> ${item.issue}` : ""}
    `;

    output.appendChild(div);
});

// Filter function
function filterSeverity(level) {
    const cards = document.querySelectorAll(".mini-card");

    cards.forEach(card => {
        if (level === "all") {
            card.style.display = "inline-block";
        } else {
            card.style.display =
                card.classList.contains(level) ? "inline-block" : "none";
        }
    });
}