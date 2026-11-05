let sortDirections = {};

function sortTable(columnIndex) {
    const table = document.getElementById("books-table");
    if (!table) return;

    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    sortDirections[columnIndex] = sortDirections[columnIndex] === 1 ? -1 : 1;
    const direction = sortDirections[columnIndex];

    rows.sort((rowA, rowB) => {
        const cellA = rowA.children[columnIndex].innerText.trim().toLowerCase();
        const cellB = rowB.children[columnIndex].innerText.trim().toLowerCase();

        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return (numA - numB) * direction;
        }

        return cellA.localeCompare(cellB, 'de', { numeric: true }) * direction;
    });

    rows.forEach(row => tbody.appendChild(row));
}