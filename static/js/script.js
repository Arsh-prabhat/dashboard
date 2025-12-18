/* =========================================================
   GLOBAL STATE
========================================================= */
let currentBoxId = null;
let currentBoxName = null;

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
   LOAD MAIN SALES DATA (PENDING QTY)
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

    if (!data || data.length === 0) {
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
                    onclick="loadBranchBreakup('${r.boxId}', '${r.boxName}')"
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
   LOAD BRANCH-WISE BREAKUP
========================================================= */
async function loadBranchBreakup(boxId, boxName) {
    currentBoxId = boxId;
    currentBoxName = boxName;

    const from = document.getElementById("fromDate").value;
    const to = document.getElementById("toDate").value;

    const res = await fetch(
        `/api/branch-breakup?boxId=${boxId}&from=${from}&to=${to}`
    );
    const data = await res.json();

    const table = document.getElementById("branchTable");
    table.innerHTML = "";

    if (!data || data.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="4" class="muted">No branch data</td>
            </tr>
        `;
        return;
    }

    data.forEach((r, index) => {
        table.innerHTML += `
            <tr>
                <td>${r.company}</td>
                <td>${r.qty}</td>
                <td>
                    <input
                        type="number"
                        min="0"
                        max="${r.qty}"
                        id="supplied_${index}"
                        style="width:80px"
                    >
                </td>
                <td>
                    <button onclick="saveSupply(
                        '${currentBoxId}',
                        '${currentBoxName}',
                        ${r.branch},
                        '${r.company}',
                        'supplied_${index}'
                    )">
                        Save
                    </button>
                </td>
            </tr>
        `;
    });
}

/* =========================================================
   SAVE SUPPLIED QUANTITY
========================================================= */
async function saveSupply(boxId, boxName, branchcode, company, inputId) {
    const qtyInput = document.getElementById(inputId);
    const qty = parseInt(qtyInput.value);

    if (!qty || qty <= 0) {
        alert("Enter valid supplied quantity");
        return;
    }

    try {
        const res = await fetch("/api/save-supply", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                boxId: boxId,
                boxName: boxName,
                qty: qty,
                branchcode: branchcode,
                company: company
            })
        });

        const data = await res.json();

        if (data.success) {
            alert("Saved successfully");
            qtyInput.value = "";
            loadData(); // refresh pending qty
        } else {
            alert("Save failed");
        }
    } catch (err) {
        console.error(err);
        alert("Server error while saving");
    }
}
