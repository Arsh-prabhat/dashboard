/* =========================================================
   GLOBAL STATE
========================================================= */
let currentBoxId = null;
let currentBoxName = null;

/* =========================================================
   FIXED DATE (2015 – system limitation)
========================================================= */
function setDefaultDates() {
    fromDate.value = "2015-12-18";
    toDate.value   = "2015-12-31";
}

/* =========================================================
   LOAD MAIN SALES DATA (PENDING QTY)
========================================================= */
async function loadData() {
    const res = await fetch(
        `/api/sales?from=${fromDate.value}&to=${toDate.value}`
    );
    const data = await res.json();

    salesTable.innerHTML = "";

    if (!data.length) {
        salesTable.innerHTML = `<tr><td colspan="3">No data</td></tr>`;
        return;
    }

    data.forEach(r => {
        salesTable.innerHTML += `
            <tr>
                <td>${r.boxId}</td>
                <td>${r.boxName}</td>
                <td class="qty-cell"
                    title="Ordered: ${r.ordered} | Supplied: ${r.supplied}"
                    onclick="loadBranchBreakup('${r.boxId}', '${r.boxName}')">
                    ${r.remaining}
                </td>
            </tr>
        `;
    });
}

/* =========================================================
   LOAD COMPANY-WISE BREAKUP (NO BRANCH)
========================================================= */
async function loadBranchBreakup(boxId, boxName) {
    currentBoxId = boxId;
    currentBoxName = boxName;

    const res = await fetch(
        `/api/branch-breakup?boxId=${boxId}&from=${fromDate.value}&to=${toDate.value}`
    );
    const data = await res.json();

    branchTable.innerHTML = "";

    if (!data.length) {
        branchTable.innerHTML = `<tr><td colspan="4">No data</td></tr>`;
        return;
    }

    data.forEach((r, i) => {
        branchTable.innerHTML += `
            <tr>
                <td>${r.company}</td>
                <td>${r.qty}</td>
                <td>
                    <input type="number"
                           min="0"
                           max="${r.qty}"
                           id="sup_${i}"
                           style="width:70px">
                </td>
                <td>
                    <button onclick="saveSupply(
                        '${boxId}',
                        '${boxName}',
                        '${r.company}',
                        'sup_${i}'
                    )">
                        Save
                    </button>
                </td>
            </tr>
        `;
    });
}

/* =========================================================
   SAVE SUPPLIED QTY
========================================================= */
async function saveSupply(boxId, boxName, company, inputId) {
    const qty = parseInt(document.getElementById(inputId).value);

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
            supplyDate: fromDate.value
        })
    });

    const data = await res.json();

    if (data.success) {
        alert("Saved successfully");

        // 🔁 refresh both tables
        loadData();
        loadBranchBreakup(currentBoxId, currentBoxName);
    } else {
        alert("Save failed");
    }
}

/* =========================================================
   INIT
========================================================= */
searchBtn.onclick = loadData;
setDefaultDates();
