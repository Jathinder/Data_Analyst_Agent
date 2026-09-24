// =====================================================
// CONFIGURATION
// =====================================================

const API_URL = "http://127.0.0.1:8000";


// =====================================================
// ELEMENTS
// =====================================================

const questionInput =
    document.getElementById("questionInput");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const buttonText =
    document.getElementById("buttonText");

const buttonLoader =
    document.getElementById("buttonLoader");

const loadingSection =
    document.getElementById("loadingSection");

const resultsSection =
    document.getElementById("resultsSection");

const errorBox =
    document.getElementById("errorBox");

const answerText =
    document.getElementById("answerText");

const rowCount =
    document.getElementById("rowCount");

const columnCount =
    document.getElementById("columnCount");

const stepCount =
    document.getElementById("stepCount");

const resultStatus =
    document.getElementById("resultStatus");

const tableHead =
    document.getElementById("tableHead");

const tableBody =
    document.getElementById("tableBody");

const sqlCode =
    document.getElementById("sqlCode");

const detailsSteps =
    document.getElementById("detailsSteps");

const chartSection =
    document.getElementById("chartSection");

const chartDetails =
    document.getElementById("chartDetails");

const downloadBtn =
    document.getElementById("downloadBtn");

const copySqlBtn =
    document.getElementById("copySqlBtn");

const recentQueries =
    document.getElementById("recentQueries");


// Chart instance
let currentChart = null;


// =====================================================
// QUERY LIBRARY
// =====================================================

document.querySelectorAll(".example-query").forEach(
    button => {

        button.addEventListener("click", () => {

            questionInput.value =
                button.dataset.query;

            questionInput.focus();

        });

    }
);


// =====================================================
// ENTER KEY
// =====================================================

questionInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {

            analyzeQuestion();

        }

    }
);


// =====================================================
// ANALYZE BUTTON
// =====================================================

analyzeBtn.addEventListener(
    "click",
    analyzeQuestion
);


// =====================================================
// ANALYZE QUESTION
// =====================================================

async function analyzeQuestion() {

    const question =
        questionInput.value.trim();


    if (!question) {

        showError(
            "Please enter a question first."
        );

        return;

    }


    // Reset interface
    hideError();

    resultsSection.classList.add("hidden");

    loadingSection.classList.remove("hidden");

    analyzeBtn.disabled = true;

    buttonText.textContent = "Analyzing...";

    buttonLoader.classList.remove("hidden");


    try {

        const response =
            await fetch(
                `${API_URL}/analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Backend request failed."
            );

        }


        displayResults(data);

        saveRecentQuery(question);


    } catch (error) {

        console.error(error);

        showError(
            `Could not analyze the question: ${error.message}`
        );

    } finally {

        loadingSection.classList.add("hidden");

        analyzeBtn.disabled = false;

        buttonText.textContent = "Analyze";

        buttonLoader.classList.add("hidden");

    }

}


// =====================================================
// DISPLAY RESULTS
// =====================================================

function displayResults(data) {

    resultsSection.classList.remove("hidden");


    const answer =
        data.answer || "No answer returned.";

    const sql =
        data.sql || "";

    const columns =
        data.columns || [];

    const rows =
        data.rows || [];

    const steps =
        data.steps || 0;


    // Answer
    answerText.textContent =
        answer;


    // KPI
    rowCount.textContent =
        rows.length;

    columnCount.textContent =
        columns.length;

    stepCount.textContent =
        steps;

    detailsSteps.textContent =
        steps;


    if (data.error) {

        resultStatus.textContent = "⚠";

    } else {

        resultStatus.textContent = "✓";

    }


    // Table
    buildTable(
        columns,
        rows
    );


    // SQL
    sqlCode.textContent =
        sql;


    // Chart
    buildChart(
        columns,
        rows
    );


    // Scroll to results
    setTimeout(() => {

        resultsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 100);

}


// =====================================================
// BUILD TABLE
// =====================================================

function buildTable(columns, rows) {

    tableHead.innerHTML = "";

    tableBody.innerHTML = "";


    if (!columns.length) {

        return;

    }


    const headerRow =
        document.createElement("tr");


    columns.forEach(column => {

        const th =
            document.createElement("th");

        th.textContent =
            column;

        headerRow.appendChild(th);

    });


    tableHead.appendChild(
        headerRow
    );


    rows.forEach(row => {

        const tr =
            document.createElement("tr");


        row.forEach(value => {

            const td =
                document.createElement("td");

            if (
                value === null ||
                value === undefined
            ) {

                td.textContent = "NULL";

            } else {

                td.textContent =
                    value;

            }


            tr.appendChild(td);

        });


        tableBody.appendChild(tr);

    });

}


// =====================================================
// BUILD CHART
// =====================================================

function buildChart(columns, rows) {

    chartSection.classList.add("hidden");


    if (currentChart) {

        currentChart.destroy();

        currentChart = null;

    }


    if (
        columns.length < 2 ||
        rows.length === 0
    ) {

        return;

    }


    // Find numeric column
    let numericIndex = -1;

    let categoryIndex = -1;


    for (
        let i = 0;
        i < columns.length;
        i++
    ) {

        const values =
            rows.map(row => row[i]);


        const numericValues =
            values.filter(
                value =>
                    typeof value === "number"
            );


        if (
            numericValues.length >
            rows.length * 0.5
        ) {

            numericIndex = i;

            break;

        }

    }


    if (numericIndex === -1) {

        return;

    }


    // First non-numeric column
    for (
        let i = 0;
        i < columns.length;
        i++
    ) {

        if (i !== numericIndex) {

            categoryIndex = i;

            break;

        }

    }


    if (categoryIndex === -1) {

        return;

    }


    const labels =
        rows.map(
            row =>
                String(row[categoryIndex])
        );


    const values =
        rows.map(
            row =>
                Number(row[numericIndex])
        );


    const canvas =
        document.getElementById(
            "resultChart"
        );


    const ctx =
        canvas.getContext("2d");


    const chartType =
        rows.length > 15
            ? "line"
            : "bar";


    currentChart =
        new Chart(
            ctx,
            {
                type: chartType,

                data: {

                    labels: labels,

                    datasets: [

                        {
                            label:
                                columns[numericIndex],

                            data: values,

                            borderColor:
                                "#8b7dff",

                            backgroundColor:
                                "rgba(118,105,255,0.25)",

                            borderWidth: 2,

                            tension: 0.35,

                            fill:
                                chartType ===
                                "line"

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            labels: {

                                color:
                                    "#aab3c4"

                            }

                        }

                    },

                    scales: {

                        x: {

                            ticks: {

                                color:
                                    "#7f8ba2",

                                maxRotation: 45

                            },

                            grid: {

                                color:
                                    "rgba(255,255,255,0.05)"

                            }

                        },

                        y: {

                            ticks: {

                                color:
                                    "#7f8ba2"

                            },

                            grid: {

                                color:
                                    "rgba(255,255,255,0.05)"

                            }

                        }

                    }

                }

            }
        );


    chartSection.classList.remove(
        "hidden"
    );


    chartDetails.innerHTML =
        `
        Chart: ${chartType === "line"
            ? "Line Chart"
            : "Bar Chart"}

        &nbsp; · &nbsp;

        Category: ${columns[categoryIndex]}

        &nbsp; · &nbsp;

        Metric: ${columns[numericIndex]}

        &nbsp; · &nbsp;

        Data Points: ${rows.length}
        `;

}


// =====================================================
// DOWNLOAD CSV
// =====================================================

downloadBtn.addEventListener(
    "click",
    () => {

        const table =
            document.getElementById(
                "resultTable"
            );


        if (!table.rows.length) {

            return;

        }


        let csv = "";


        // Header
        const headers =
            Array.from(
                table.rows[0].cells
            ).map(
                cell =>
                    `"${cell.textContent.replace(
                        /"/g,
                        '""'
                    )}"`
            );


        csv +=
            headers.join(",") +
            "\n";


        // Rows
        for (
            let i = 1;
            i < table.rows.length;
            i++
        ) {

            const row =
                Array.from(
                    table.rows[i].cells
                ).map(
                    cell =>
                        `"${cell.textContent.replace(
                            /"/g,
                            '""'
                        )}"`
                );


            csv +=
                row.join(",") +
                "\n";

        }


        const blob =
            new Blob(
                [csv],
                {
                    type:
                        "text/csv;charset=utf-8;"
                }
            );


        const url =
            URL.createObjectURL(blob);


        const link =
            document.createElement("a");


        link.href = url;

        link.download =
            "query_results.csv";


        link.click();


        URL.revokeObjectURL(url);

    }
);


// =====================================================
// COPY SQL
// =====================================================

copySqlBtn.addEventListener(
    "click",
    async () => {

        const sql =
            sqlCode.textContent;


        if (!sql) {

            return;

        }


        try {

            await navigator.clipboard.writeText(
                sql
            );


            const original =
                copySqlBtn.textContent;


            copySqlBtn.textContent =
                "Copied ✓";


            setTimeout(() => {

                copySqlBtn.textContent =
                    original;

            }, 1500);


        } catch (error) {

            console.error(
                "Copy failed:",
                error
            );

        }

    }
);


// =====================================================
// RECENT QUERIES
// =====================================================

function saveRecentQuery(question) {

    let queries =
        JSON.parse(
            localStorage.getItem(
                "recentQueries"
            ) || "[]"
        );


    queries =
        queries.filter(
            item =>
                item !== question
        );


    queries.unshift(
        question
    );


    queries =
        queries.slice(0, 5);


    localStorage.setItem(
        "recentQueries",
        JSON.stringify(queries)
    );


    renderRecentQueries();

}


function renderRecentQueries() {

    const queries =
        JSON.parse(
            localStorage.getItem(
                "recentQueries"
            ) || "[]"
        );


    recentQueries.innerHTML = "";


    queries.forEach(query => {

        const item =
            document.createElement("div");


        item.className =
            "recent-item";


        item.textContent =
            query;


        item.style.cursor =
            "pointer";


        item.addEventListener(
            "click",
            () => {

                questionInput.value =
                    query;

                questionInput.focus();

            }
        );


        recentQueries.appendChild(
            item
        );

    });

}


renderRecentQueries();


// =====================================================
// ERROR HANDLING
// =====================================================

function showError(message) {

    errorBox.textContent =
        message;

    errorBox.classList.remove(
        "hidden"
    );

}


function hideError() {

    errorBox.classList.add(
        "hidden"
    );

}