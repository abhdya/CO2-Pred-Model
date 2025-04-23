let shipTypes = [];
const checkboxValues = {};
const BACKEND_URL = "https://co2-backend.onrender.com"; // ⬅️ Set your backend URL here

// Function to load ship types on page load
async function loadShipTypes() {
    try {
        const response = await fetch(`${BACKEND_URL}/get-ship-types/`);
        const data = await response.json();

        if (data.ship_types) {
            populateShipTypes(data.ship_types);
        } else {
            console.error("Error fetching ship types:", data.error);
        }
    } catch (error) {
        console.error("Error loading ship types:", error);
    }
}

// Populate ship types dropdown
function populateShipTypes(types) {
    const shipTypeSelect = document.getElementById("shipType");
    shipTypeSelect.innerHTML = "<option value=''>Select Ship Type</option>";

    types.forEach(type => {
        const option = document.createElement("option");
        option.value = type.id;
        option.textContent = type.name;
        shipTypeSelect.appendChild(option);
    });
}

// Fetch ship names based on selected ship type
async function updateShipNames() {
    const shipTypeSelect = document.getElementById("shipType");
    const selectedIndex = shipTypeSelect.selectedIndex;
    if (selectedIndex === -1) return;

    const shipTypeName = shipTypeSelect.options[selectedIndex].textContent;

    try {
        const response = await fetch(`${BACKEND_URL}/get-ship-names/${encodeURIComponent(shipTypeName)}`);
        const data = await response.json();

        const shipNameSelect = document.getElementById("shipName");
        shipNameSelect.innerHTML = "<option value=''>Select Ship Name</option>";

        if (data.ship_names && data.ship_names.length > 0) {
            data.ship_names.forEach(name => {
                const option = document.createElement("option");
                option.value = name;
                option.textContent = name;
                shipNameSelect.appendChild(option);
            });
        } else {
            console.warn("No ships found for this type.");
        }
    } catch (error) {
        console.error("Error updating ship names:", error);
    }
}

// Fetch Deadweight & Gross Tonnage based on ship name
async function updateValues() {
    const shipName = document.getElementById("shipName").value;

    if (!shipName) return;

    try {
        const response = await fetch(`${BACKEND_URL}/get-ship-data/${encodeURIComponent(shipName)}`);
        const data = await response.json();

        if (data.deadweight && data.grosstonnage) {
            document.getElementById("deadweight").value = data.deadweight;
            document.getElementById("grossTonnage").value = data.grosstonnage;
        } else {
            console.warn("Missing ship data.");
        }
    } catch (error) {
        console.error("Error fetching ship data:", error);
    }
}

// Update checkbox values
function updateCheckboxValue(checkbox) {
    checkboxValues[checkbox.value] = checkbox.checked ? 1 : 0;
    console.log("Updated checkboxValues:", checkboxValues);
}

// Predict CO2 Emissions
async function predictEmissions() {
    const shipType = document.getElementById("shipType").value;
    const deadweight = parseFloat(document.getElementById("deadweight").value) || 0;
    const grossTonnage = parseFloat(document.getElementById("grossTonnage").value) || 0;
    const steamingTime = parseFloat(document.getElementById("steamingTime").value) || 0;
    const distance = parseFloat(document.getElementById("distance").value) || 0;

    if (!shipType) {
        alert("Please select a ship type.");
        return;
    }

    const inputData = {
        ship_type: document.getElementById("shipType").options[document.getElementById("shipType").selectedIndex].textContent,
        Deadweight: deadweight,
        GrossTonnage: grossTonnage,
        SteamingTime: steamingTime,
        Distance: distance,
        FuelTypes: {
            "ME_MDO/MGO": checkboxValues["ME_MDO/MGO"] || 0,
            "ME_HFO": checkboxValues["ME_HFO"] || 0,
            "ME_LFO": checkboxValues["ME_LFO"] || 0,
            "AE_Boiler_MDO/MGO": checkboxValues["AE_Boiler_MDO/MGO"] || 0,
            "AE_Boiler_HFO": checkboxValues["AE_Boiler_HFO"] || 0,
            "AE_Boiler_LFO": checkboxValues["AE_Boiler_LFO"] || 0
        }
    };

    try {
        const response = await fetch(`${BACKEND_URL}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(inputData)
        });

        const result = await response.json();
        document.getElementById("result").innerText = JSON.stringify(result, null, 2);
    } catch (error) {
        console.error("Error predicting emissions:", error);
        document.getElementById("result").innerText = "Error predicting CO2 emissions.";
    }
}

// On DOM load
document.addEventListener('DOMContentLoaded', () => {
    loadShipTypes();

    // Add listeners after DOM is ready
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => updateCheckboxValue(checkbox));
    });
});
