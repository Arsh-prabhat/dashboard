let currentBoxId = null;
let currentBoxName = null;
let godowns = [];

/* ================= DEFAULT DATE ================= */
function setDefaultDates() {
    document.getElementById("fromDate").value = "2015-12-18";
    document.getElementById("toDate").value = "2015-12-31";
}

/* ================= LOAD GODOWNS ================= */
async function loadGodowns() {
    const res = await fetch("/api/godowns");
    godowns = await res.json();
}

/* ================= LOAD MAIN TABLE ================= */
async function loadData() {
    const from = fromDate.value;
    const to = toDate.value;

    const res = await fetch(`/api/sales?from=${from}&to=${to}`);
    const data = await res.json();

    const table = document.getElementById("salesTable");
    table.innerHTML = "";

    if (data.length === 0) {
        table.innerHTML = `<tr><td colspan="4">No data found</td></tr>`;
        document.getElementById("branchTable").innerHTML = `
            <tr><td colspan="5">Select a box to view details</td></tr>
        `;
        return;
    }

    data.forEach(r => {
        table.innerHTML += `
            <tr>
                <td>${r.boxId}</td>
                <td>${r.boxName}</td>
                <td>${r.ordered}</td>
                <td class="qty-cell"
                    onclick="loadBranchBreakup('${r.boxId}','${r.boxName}')">
                    ${r.remaining}
                </td>
            </tr>
        `;
    });
}

/* ================= BRANCH TABLE ================= */
async function loadBranchBreakup(boxId, boxName) {
    currentBoxId = boxId;
    currentBoxName = boxName;

    const from = fromDate.value;
    const to = toDate.value;

    const res = await fetch(
        `/api/branch-breakup?boxId=${boxId}&from=${from}&to=${to}`
    );
    const data = await res.json();

    const table = document.getElementById("branchTable");
    table.innerHTML = "";

    if (data.length === 0) {
        table.innerHTML = `<tr><td colspan="5">No pending quantity</td></tr>`;
        return;
    }

    data.forEach((r, index) => {
        let options = godowns.map(g =>
            `<option value="${g}">${g}</option>`
        ).join("");

        table.innerHTML += `
            <tr>
                <td>${r.company}</td>

                <td>
                    <select id="godown_${index}">
                        ${options}
                    </select>
                </td>

                <td>${r.qty}</td>

                <td>
                    <input type="number"
                           min="1"
                           max="${r.qty}"
                           id="supplied_${index}"
                           style="width:80px">
                </td>

                <td>
                    <button onclick="saveSupply(
                        '${currentBoxId}',
                        '${currentBoxName}',
                        '${r.company}',
                        'supplied_${index}',
                        'godown_${index}'
                    )">
                        Save
                    </button>
                </td>
            </tr>
        `;
    });
}

/* ================= SAVE ================= */
async function saveSupply(boxId, boxName, company, qtyId, godownId) {
    const qty = parseInt(document.getElementById(qtyId).value);
    const godown = document.getElementById(godownId).value;

    if (!qty || qty <= 0) {
        alert("Enter valid quantity");
        return;
    }

    const res = await fetch("/api/save-supply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            boxId,
            boxName,
            qty,
            company,
            godown
        })
    });

    const data = await res.json();

    if (data.success) {
        alert("Saved successfully");
        loadData();
        loadBranchBreakup(boxId, boxName);
    } else {
        alert("Save failed");
    }
}

/* ================= INIT ================= */
document.addEventListener("DOMContentLoaded", async () => {
    setDefaultDates();
    await loadGodowns();
    loadData();
    document.getElementById("searchBtn").addEventListener("click", loadData);
});
