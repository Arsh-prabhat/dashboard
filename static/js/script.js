let currentBox = {};
let selectedSupply = {};

/* =========================================================
   DEFAULT DATES (10 YEARS BACK)
========================================================= */
function setDefaultDates() {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 10);
    const dateStr = d.toISOString().split("T")[0];
    document.getElementById("fromDate").value = dateStr;
    document.getElementById("toDate").value = dateStr;
}

/* =========================================================
   LOAD MAIN SALES DATA (REMAINING QTY)
========================================================= */
async function loadData() {
    const from = document.getElementById("fromDate").value;
    const to = document.getElementById("toDate").value;

    if (!from || !to) {
        alert("Please select both dates");
        return;
    }

    const res = await fetch(`/api/sales?from=${from}&to=${to}`);
    const data = await res.json();

    const table = document.getElementById("salesTable");
    table.innerHTML = "";

    if (data.length === 0) {
        table.innerHTML = `<tr><td colspan="3">No data found</td></tr>`;
        return;
    }

    data.forEach(r => {
        table.innerHTML += `
            <tr>
                <td>${r.boxId}</td>
                <td>${r.boxName}</td>
                <td 
                    class="qty-cell"
                    title="Ordered: ${r.ordered} | Supplied: ${r.supplied}"
                    onclick="loadBranchBreakup('${r.boxId}', '${r.boxName}', ${r.remaining})"
                >
                    ${r.remaining}
                </td>
            </tr>
        `;
    });
}

document.getElementById("searchBtn").addEventListener("click", loadData);
setDefaultDates();

/* =========================================================
   BRANCH-WISE BREAKUP
========================================================= */
async function loadBranchBreakup(boxId, boxName, remainingQty) {
    currentBox = { boxId, boxName, remainingQty };

    const from = document.getElementById("fromDate").value;
    const to = document.getElementById("toDate").value;

    const res = await fetch(
        `/api/branch-breakup?boxId=${boxId}&from=${from}&to=${to}`
    );
    const data = await res.json();

    const table = document.getElementById("branchTable");
    table.innerHTML = "";

    if (data.length === 0) {
        table.innerHTML = `<tr><td colspan="4">No data found</td></tr>`;
    }

    data.forEach(r => {
        table.innerHTML += `
            <tr>
                <td>${r.company}</td>
                <td>${r.branch}</td>
                <td>${r.qty}</td>
                <td>
                    <button 
                        onclick="openSupplyForm('${r.company}', '${r.branch}')"
                        ${currentBox.remainingQty === 0 ? "disabled" : ""}
                    >
                        Enter Supply
                    </button>
                </td>
            </tr>
        `;
    });

    document.getElementById("branchModal").classList.remove("hidden");
}

function closeBranchModal() {
    document.getElementById("branchModal").classList.add("hidden");
}

/* =========================================================
   OPEN WRITE VIEW (SUPPLY ENTRY)
========================================================= */
function openSupplyForm(company, branch) {
    selectedSupply = {
        company,
        branch,
        boxId: currentBox.boxId,
        boxName: currentBox.boxName,
        remainingQty: currentBox.remainingQty
    };

    document.getElementById("sCompany").value = company;
    document.getElementById("sBranch").value = branch;
    document.getElementById("sBox").value = currentBox.boxId;
    document.getElementById("sQty").value = "";

    document.getElementById("supplyModal").classList.remove("hidden");
}

function closeSupplyModal() {
    document.getElementById("supplyModal").classList.add("hidden");
}

/* =========================================================
   SAVE SUPPLY ENTRY
========================================================= */
async function saveSupply() {
    const qty = parseInt(document.getElementById("sQty").value);

    if (!qty || qty <= 0) {
        alert("Enter a valid quantity");
        return;
    }

    if (qty > selectedSupply.remainingQty) {
        alert("Entered quantity exceeds remaining quantity");
        return;
    }

    const res = await fetch("/api/save-supply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            boxId: selectedSupply.boxId,
            boxName: selectedSupply.boxName,
            qty: qty,
            branchcode: selectedSupply.branch,
            company: selectedSupply.company
        })
    });

    const data = await res.json();

    if (data.success) {
        alert("Supply saved successfully");
        closeSupplyModal();
        closeBranchModal();
        loadData(); // 🔄 refresh main table
    } else {
        alert(data.msg || "Error saving supply");
    }
}
